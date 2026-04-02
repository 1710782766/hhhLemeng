import tornado
from typing import TYPE_CHECKING

from hhh_lemeng.handler.common.lemeng.utils import error_handler, BaseHandler
from hhh_lemeng.handler.common.lemeng.error import LemRequestError
from hhh_lemeng.handler.common.lemeng.config import (
    BRANCH_NUM,
    STOREHOUSE_NUM,
    CLIENT_FID,
    OPERATOR,
)
from hhh_lemeng.handler.common.lemeng.address_db import get_address_db
from hhh_lemeng.handler.common.lemeng.inventory_storage import get_inventory_storage

if TYPE_CHECKING:
    from hhh_lemeng.handler.service.hhhLemengService import HhhLemengService


class LmOauthCodeCallback(tornado.web.RequestHandler):
    """
    乐檬 - 获取授权码（code）回调
    """

    async def get(self):
        # code=FydrPB&state=1
        self.hhh_lm: "HhhLemengService" = self.application.settings["hhh_lm"]

        code = self.get_argument("code", "")
        state = self.get_argument("state", "")

        await self.hhh_lm.init_token(code)

        print(f"code: {code}, state: {state}")

        self.set_status(200)
        self.write("success")


class ShopItemFind(BaseHandler):
    """
    商品档案查询（带主图）

    :param
        pindex: 页码，默认 1
        psize: 每页数量，默认 10，最大 20
        item_category_code: 商品类别编码（可选）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)
        pindex = paras.get("pindex", 1)
        psize = min(paras.get("psize", 10), 20)  # 最大 20
        item_category_code = paras.get("item_category_code", "")

        # 1. 查询商品列表
        items, msg = await self.hhh_lm.nhsoft_amazon_basic_item_find(
            page_no=pindex, page_size=psize, item_category_code=item_category_code
        )

        if not items:
            await self.response_success({}, [], msg)
            return

        # 2. 提取所有商品编码
        item_nums = [item["item_num"] for item in items if item.get("item_num")]

        # 3. 查询图片
        images = []
        if item_nums:
            images, _ = await self.hhh_lm.nhsoft_amazon_basic_itemimage_find(
                item_nums=item_nums
            )

        # 4. 构建图片映射 {item_num: default_image_url}
        image_map = {}
        for img in images:
            if img.get("pos_image_default") and img.get("item_num"):
                image_map[img["item_num"]] = img.get("pos_image_url", "")

        # 5. 注入主图到商品数据
        for item in items:
            item["item_image"] = image_map.get(item.get("item_num"), "")

        await self.response_success({}, items, msg)


class MallItemFind(BaseHandler):
    """
    商城商品查询（乐檬新零售）

    :param
        pindex: 页码，默认 1
        psize: 每页数量，默认 10，最大 200
        category_ids: 商品分类ID列表（可选）
        name: 商品名称模糊查询（可选）
        item_name_or_code_or_barcode: 商品名称/代码/条码（可选）
        enable: 是否启用（可选，默认 true）
        stop_sale: 是否停售（可选，默认 false）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        pindex = paras.get("pindex", 1)
        psize = min(paras.get("psize", 10), 200)  # 最大 200
        category_ids = paras.get("category_ids", [])
        name = paras.get("name", "")
        item_name_or_code_or_barcode = paras.get("item_name_or_code_or_barcode", "")
        enable = paras.get("enable", True)
        stop_sale = paras.get("stop_sale", False)

        # 构建查询参数
        kwargs = {
            "page_no": pindex,
            "page_size": psize,
            "enable": enable,
            "stop_sale": stop_sale,
        }

        if category_ids:
            kwargs["category_ids"] = category_ids
        if name:
            kwargs["name"] = name
        if item_name_or_code_or_barcode:
            kwargs["item_name_or_code_or_barcode"] = item_name_or_code_or_barcode

        result, msg = await self.hhh_lm.nhsoft_mercury_basic_item_find(**kwargs)

        await self.response_success({}, result, msg)


class ShopCategoryFind(BaseHandler):
    """
    商品类别查询（只返回有库存商品的分类）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        self._print_info({})

        result, msg = await self.hhh_lm.nhsoft_amazon_basic_itemcategory_find()

        if not result:
            await self.response_success({}, result, msg)
            return

        # 读取库存商品分类映射
        inventory_storage = get_inventory_storage()
        category_map = inventory_storage.get_category_map()

        if not category_map:
            # 没有缓存时返回全部分类
            await self.response_success({}, result, msg)
            return

        # 统计每个分类下有多少有库存商品
        category_item_count = {}
        for item_num, cat_code in category_map.items():
            if cat_code:
                category_item_count[cat_code] = category_item_count.get(cat_code, 0) + 1

        # 构建分类映射：code -> category_info
        all_categories = {cat["category_code"]: cat for cat in result}

        # 找出有商品的分类
        categories_with_items = set(category_item_count.keys())

        # 找出所有需要保留的分类（包括有商品的分类及其所有祖先）
        categories_to_keep = set()

        def mark_ancestors(cat_code):
            """递归标记所有祖先分类"""
            while cat_code:
                if cat_code in categories_to_keep:
                    break  # 已处理过，避免循环
                categories_to_keep.add(cat_code)
                cat = all_categories.get(cat_code)
                cat_code = cat.get("parent_category_code") if cat else None

        for cat_code in categories_with_items:
            mark_ancestors(cat_code)

        # 过滤分类
        filtered_result = [
            {
                **cat,
                "item_count": category_item_count.get(cat["category_code"], 0),
            }
            for cat in result
            if cat["category_code"] in categories_to_keep
        ]

        await self.response_success({}, filtered_result, msg)


class ShopItemDetail(BaseHandler):
    """
    商品档案详情

    :param
        item_num: 商品编码
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)
        item_num = paras.get("item_num", "")

        if not item_num:
            raise LemRequestError("商品编码不能为空")

        # 1. 查询商品详情
        result, msg = await self.hhh_lm.nhsoft_amazon_basic_item_read(item_num=item_num)

        if not result:
            await self.response_success({}, [], msg)
            return

        # 2. 查询图片
        images = []
        if result.get("item_num"):
            images, _ = await self.hhh_lm.nhsoft_amazon_basic_itemimage_find(
                item_nums=[result["item_num"]]
            )

        # 3. 注入主图到商品数据
        result["item_image"] = ""
        for img in images:
            if (
                img.get("pos_image_default")
                and img.get("item_num") == result["item_num"]
            ):
                result["item_image"] = img.get("pos_image_url", "")
                break

        await self.response_success(result, [], msg)


class WholesaleOrderCreate(BaseHandler):
    """
    创建批发订单

    :param
        items: 商品列表 [{"item_num": "", "item_count": 1, "item_price": 0.0, "item_unit": ""}]
        memo: 订单备注（可选）
        address_id: 收货地址ID（可选，不传使用默认客户）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        items = paras.get("items", [])
        memo = paras.get("memo", "")
        address_id = paras.get("address_id", "")

        if not items:
            raise LemRequestError("商品列表不能为空")

        # 组装订单明细，转换字段名
        wholesale_book_details = []
        for item in items:
            detail = {
                "item_num": item.get("item_num"),
                "item_use_qty": item.get("item_use_qty", 1),
                "item_use_unit": item.get("item_use_unit", "件"),
            }
            wholesale_book_details.append(detail)

        # 确定使用的客户信息
        client_fid = CLIENT_FID
        client_name = "好惠花"

        # 如果传入了 address_id，从本地数据库查询对应的客户
        if address_id:
            address_db = get_address_db()
            address = address_db.get_address_by_id(address_id)
            if not address:
                raise LemRequestError("收货地址不存在")
            client_fid = address["client_fid"]
            client_name = address["name"]

        result, msg = await self.hhh_lm.nhsoft_amazon_wholesale_book_save(
            branch_num=BRANCH_NUM,
            storehouse_num=STOREHOUSE_NUM,
            client_fid=client_fid,
            client_name=client_name,
            wholesale_book_memo=memo,
            wholesale_book_operator=OPERATOR,
            wholesale_book_details=wholesale_book_details,
        )

        await self.response_success(result, [], msg)


class WholesaleOrderFind(BaseHandler):
    """
    批发订单查询

    :param
        pindex: 页码，默认 1
        psize: 每页数量，默认 10
        date_from: 开始日期，格式 yyyy-MM-dd
        date_to: 结束日期，格式 yyyy-MM-dd
        state_codes: 单据状态代码(1:制单 3:制单|审核 7:制单|审核|中止) 可选
        client_fid: 客户ID
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        pindex = paras.get("pindex", 1)
        psize = paras.get("psize", 10)
        date_from = paras.get("start_date", "")
        date_to = paras.get("end_date", "")
        state_codes = paras.get("state_codes", [])
        client_fid = paras.get("client_fid", CLIENT_FID)

        if not date_from or not date_to:
            raise LemRequestError("开始日期和结束日期不能为空")

        if not client_fid:
            raise LemRequestError("客户ID不能为空")

        result, msg = await self.hhh_lm.nhsoft_amazon_wholesale_book_find(
            page_no=pindex,
            page_size=psize,
            date_from=date_from,
            date_to=date_to,
            state_codes=state_codes,
            client_fid=client_fid,
        )

        await self.response_success({}, result, msg)


class WholesaleOrderDetail(BaseHandler):
    """
    批发订单详情（按订单号查询）

    :param
        wholesale_book_fid: 批发订单号
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        wholesale_book_fid = paras.get("wholesale_book_fid", "")

        if not wholesale_book_fid:
            raise LemRequestError("订单号不能为空")

        result, msg = await self.hhh_lm.nhsoft_amazon_wholesale_book_read(
            wholesale_book_fid=wholesale_book_fid
        )

        await self.response_success(result, [], msg)


class WholesaleOrderDelete(BaseHandler):
    """
    批发订单删除

    :param
        wholesale_book_fid: 批发订单号
        operator: 操作员（可选，默认使用配置的 OPERATOR）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        wholesale_book_fid = paras.get("wholesale_book_fid", "")
        operator = paras.get("operator", OPERATOR)

        if not wholesale_book_fid:
            raise LemRequestError("订单号不能为空")

        result, msg = await self.hhh_lm.nhsoft_amazon_wholesale_book_delete(
            wholesale_book_fid=wholesale_book_fid,
            operator=operator,
        )

        await self.response_success(result, [], msg)


class ClientAddressList(BaseHandler):
    """
    客户地址列表查询

    :param
        client_fid: 客户编码（可选，默认使用配置中的 CLIENT_FID）
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        client_fid = paras.get("client_fid", CLIENT_FID)

        result, msg = await self.hhh_lm.nhsoft_amazon_basic_client_address_read(
            client_fid=client_fid
        )

        await self.response_success({}, result, msg)


class AddressList(BaseHandler):
    """
    收货地址列表查询（本地维护）

    从请求头获取 uid
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        # 从请求头获取 uid
        uid = self.request.headers.get("uid", "")
        if not uid:
            raise LemRequestError("缺少用户标识")

        address_db = get_address_db()
        addresses = address_db.get_addresses_by_uid(uid)

        await self.response_success({}, addresses, "获取成功")


class AddressCreate(BaseHandler):
    """
    新增收货地址

    同时在乐檬创建客户，并保存映射关系

    :param
        name: 收货人姓名
        phone: 收货人电话
        province: 省份
        city: 城市
        district: 区县
        detail: 详细地址
    """

    MAX_RETRY = 3  # 最大重试次数，用于处理客户代码已存在的情况

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        # 从请求头获取 uid
        uid = self.request.headers.get("uid", "")
        if not uid:
            raise LemRequestError("缺少用户标识")

        name = paras.get("name", "").strip()
        phone = paras.get("phone", "").strip()
        province = paras.get("province", "").strip()
        city = paras.get("city", "").strip()
        district = paras.get("district", "").strip()
        detail = paras.get("detail", "").strip()

        if not all([name, phone, province, city, district, detail]):
            raise LemRequestError("请填写完整的地址信息")

        # 构建完整地址
        full_address = f"{province}{city}{district}{detail}"

        # 获取地址数据库
        address_db = get_address_db()

        # 尝试创建客户，处理"客户代码已存在"的情况
        client_fid = None
        last_error = None
        client_code = None

        for attempt in range(self.MAX_RETRY):
            # 生成 client_code
            client_code = address_db.get_next_client_code(uid)

            try:
                # 在乐檬创建客户
                result, msg = await self.hhh_lm.nhsoft_amazon_basic_client_save(
                    branch_num=BRANCH_NUM,
                    client_name=f"好惠花-{name}",
                    client_code=client_code,
                    client_mobile=phone,
                    client_type="好惠花",
                    client_birth="2000-01-01",
                    client_settlement_type="临时指定",
                    client_settle_day_of_month="11",
                    client_settle_period="30",
                    client_settlement_model="所属门店结算",
                    client_credit_enable=1,
                    client_credit_limit=10000,
                    wholesale_book_balance_enough_enable=0,
                    client_usual_discount=0.9,
                    client_price_level="1",
                    client_wholesale_discount=0.9,
                    client_wholesale_level="1",
                    client_actived=1,
                    client_shared=1,
                    client_level_name="好惠花",
                    client_addr=full_address,
                    client_ship_addr=full_address,
                    client_linkman=name,
                    client_phone=phone,
                )

                if result and result.get("client_fid"):
                    client_fid = result["client_fid"]
                    break
                else:
                    raise LemRequestError(f"创建客户失败: {msg}")

            except LemRequestError as e:
                last_error = str(e)
                # 检查是否是"客户代码已存在"的错误
                if "已存在" in last_error:
                    self.hhh_lm.log.info(
                        f"client_code {client_code} 已存在，尝试下一个序号 (尝试 {attempt + 1}/{self.MAX_RETRY})"
                    )
                    continue
                else:
                    # 其他错误直接抛出
                    raise

        if not client_fid:
            raise LemRequestError(
                f"创建客户失败，已重试 {self.MAX_RETRY} 次: {last_error}"
            )

        # 保存到本地数据库
        address = address_db.add_address(
            uid=uid,
            name=name,
            phone=phone,
            province=province,
            city=city,
            district=district,
            detail=detail,
            client_fid=client_fid,
        )

        await self.response_success(address, [], "创建成功")


class InventoryFind(BaseHandler):
    """
    库存查询

    :param
        storehouse_num: 仓库编码（可选，不传使用默认仓库）
        item_nums: 商品编码列表（可选）
        pindex: 页码，默认 1
        psize: 每页数量，默认 100
    """

    @error_handler
    async def post(self):
        self.set_default_headers()
        paras = self._get_json()
        self._print_info(paras)

        storehouse_num = paras.get("storehouse_num", STOREHOUSE_NUM)
        item_nums = paras.get("item_nums", [])
        pindex = paras.get("pindex", 1)
        psize = paras.get("psize", 100)

        # 构建查询参数
        kwargs = {
            "storehouse_num": storehouse_num,
            "page_no": pindex,
            "page_size": psize,
        }

        if item_nums:
            kwargs["item_nums"] = item_nums

        result, msg = await self.hhh_lm.nhsoft_amazon_inventory_find(**kwargs)

        await self.response_success({}, result, msg)
