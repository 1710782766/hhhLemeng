import datetime
import json
from pathlib import Path
import random
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import urllib.parse

import tornado

from hhh_lemeng.handler.common.lemeng.error import LemRequestError
from hhh_lemeng.handler.common.lemeng.token import NhsoftTokenManager
from hhh_lemeng.handler.common.lemeng.inventory_storage import get_inventory_storage

if TYPE_CHECKING:
    from logging import Logger


class HhhLemengService:
    def __init__(self, env: str, log: "Logger"):
        self.env = env
        self.log = log

        self.config = {
            "dev": {
                "host": "https://cloud.nhsoft.cn",
                "appid": "93ec09e991d6469288c5fe38fe91c927",
                "secret": "190e2ba3400d40d1ae5b70328f903d27",
                "redirect_uri": "http://127.0.0.1:8167/api/lmOauthCodeCallback",
            },
            "pro": {},
        }
        self.env_config = self.config[self.env]
        self.work_path = Path.cwd() / "hhh_lemeng"
        self.appid = self.env_config["appid"]
        self.secret = self.env_config["secret"]
        self.redirect_uri = self.env_config["redirect_uri"]
        self.host: str = self.env_config["host"]

        self.tokenManager = NhsoftTokenManager(
            self.appid, self.secret, self.work_path, self.redirect_uri
        )

    async def init_token(self, code):
        return await self.tokenManager.exchange_code_for_token(code)

    async def get_token(self):
        return await self.tokenManager.get_access_token()

    @staticmethod
    def get_oid(prefix="") -> str:
        """
        :param prefix: 前缀
        :return: 随机订单号
        """
        return (
            prefix
            + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            + str(random.randint(1000000, 9999999))
        )

    async def send_request(
        self, req_method: str, req_url: str, req_data: Optional[Dict] = None
    ) -> Tuple[Any, str]:
        token = await self.get_token()
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        }

        body = None
        if req_method == "POST":
            body = json.dumps(req_data or {}, ensure_ascii=False).encode("utf-8")
        elif req_method == "GET":
            query = urllib.parse.urlencode(req_data or {}, doseq=True)
            if query:
                req_url = req_url + "?" + query

        self.log.info(f"{'-' * 10}请求接口{'-' * 10}\n{req_url}")

        self.log.info(
            "请求参数："
            + json.dumps(req_data or {}, ensure_ascii=False, separators=(",", ":"))
        )

        http_client = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest(
            url=req_url,
            method=req_method,
            headers=headers,
            body=body,
            validate_cert=False,
        )

        try:
            response = await http_client.fetch(request)
            if response.code == 200 and response.body:
                try:
                    result = json.loads(response.body.decode("utf-8"))
                    self.log.info(
                        "返回数据："
                        + json.dumps(result, ensure_ascii=False, separators=(",", ":"))
                    )
                    return self.process_resp(result)
                except json.JSONDecodeError:
                    self.log.error(response.body.decode("utf-8"))
                    raise LemRequestError("服务端异常")
            else:
                ex_result = (
                    json.loads(response.body.decode("utf-8"))
                    if response.body
                    else "No response content"
                )
                self.log.error(f"请求发生异常: {ex_result}")
                raise LemRequestError(
                    f"请求失败，或响应异常，请检查status_code和返回内容！\nStatus Code: {response.code}\nResponse: {ex_result}"
                )
        except tornado.httpclient.HTTPClientError as e:
            self.log.error(f"请求发生异常: {e.response.body.decode('utf-8')}")
            raise LemRequestError(f"网络异常")

    def process_resp(self, response):
        code = response.get("code")
        if int(code) == 0:
            data = response.get("result")
            msg = response.get("msg")
            return data, msg or "获取最新消息成功"
        else:
            msg = response.get("msg", "请求响应异常")
            self.log.error("返回code非0，错误消息：" + msg)
            raise LemRequestError(msg)

    # -------------------- 供应链-批发 --------------------
    async def nhsoft_amazon_wholesale_book_find(self, **kwargs):
        """
        批发订单查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/122/146/nhsoft.amazon.wholesale.book.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.wholesale.book.find/v2"

        req_data = {
            "date_type": "最后修改时间",  # 时间类型:制单时间、审核时间、作废时间、最后修改时间、付款确认时间
            "date_from": "2026-02-05",  # 开始时间
            "date_to": "2026-02-10",  # 结束时间
            "page_no": 1,
            "page_size": 10,
            "client_fid": "",  # 客户编号
            "state_codes": [],  # 单据状态代码(1:制单 3:制单|审核 7:制单|审核|中止)
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_wholesale_book_save(self, **kwargs):
        """
        批发订单新增

        doc: https://console.nhsoft.cn/documents/api-doc/122/146/nhsoft.amazon.wholesale.book.save
        """
        req_url = f"{self.host}/api/nhsoft.amazon.wholesale.book.save"

        str_format = "%Y-%m-%d"
        now_date = datetime.datetime.now()
        next_month = now_date + datetime.timedelta(days=30)

        req_data = {
            "branch_num": "",  # integer 门店编码
            "storehouse_num": "",  # integer 仓库编码
            "client_fid": "",  # 客户编号
            "wholesale_book_operator": "",  # 操作员 ('管理员')
            "wholesale_book_memo": "",  # 备注
            "wholesale_book_out_bill_no": self.get_oid("EX"),  # 外部流水号(最大长度50)
            "wholesale_book_date": now_date.strftime(
                str_format
            ),  # 订购日期 格式：yyyy-MM-dd
            "wholesale_book_deadline": next_month.strftime(
                str_format
            ),  # 交货期限 格式：yyyy-MM-dd
            "wholesale_book_details": [],  # array<object> 订单明细
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_wholesale_book_saveandaudit(self, **kwargs):
        """
        批发订单新增并审核

        doc: https://console.nhsoft.cn/documents/api-doc/122/146/nhsoft.amazon.wholesale.book.saveandaudit
        """
        req_url = f"{self.host}/api/nhsoft.amazon.wholesale.book.saveandaudit"

        str_format = "%Y-%m-%d"
        now_date = datetime.datetime.now()
        next_month = now_date + datetime.timedelta(days=30)

        req_data = {
            "branch_num": "",  # integer 门店编码
            "storehouse_num": "",  # integer 仓库编码
            "client_fid": "",  # 客户编号
            "wholesale_book_operator": "",  # 操作员 ('管理员')
            "wholesale_book_memo": "",  # 备注
            "wholesale_book_out_bill_no": self.get_oid("EX"),  # 外部流水号(最大长度50)
            "wholesale_book_date": now_date.strftime(
                str_format
            ),  # 订购日期 格式：yyyy-MM-dd
            "wholesale_book_deadline": next_month.strftime(
                str_format
            ),  # 交货期限 格式：yyyy-MM-dd
            "wholesale_book_details": [],  # array<object> 订单明细
            "address_id": "",  # string 收货地址ID（通过客户地址列表接口获取）
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_wholesale_book_read(self, **kwargs):
        """
        批发订单读取

        doc: https://console.nhsoft.cn/documents/api-doc/122/146/nhsoft.amazon.wholesale.book.read
        """
        req_url = f"{self.host}/api/nhsoft.amazon.wholesale.book.read"

        req_data = {
            "wholesale_book_fid": "",  # string 批发订单号(和外部流水号二选一)
            "wholesale_book_out_bill_no": "",  # string 外部流水号(和批发订单号二选一)
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_wholesale_book_delete(self, **kwargs):
        """
        批发订单删除

        doc: https://console.nhsoft.cn/documents/api-doc/122/146/nhsoft.amazon.wholesale.book.delete
        """
        req_url = f"{self.host}/api/nhsoft.amazon.wholesale.book.delete"

        req_data = {
            "wholesale_book_fid": "",  # string 必填 批发订单单号
            "operator": "",  # string 操作员
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    # -------------------- 供应链-采购 --------------------
    async def nhsoft_amazon_purchase_order_find(self, **kwargs):
        """
        采购订单查询

        doc: https://console.nhsoft.cn/documents/api-doc/122/123/nhsoft.amazon.purchase.order.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.purchase.order.find"

        req_data = {
            "date_type": "最后修改时间",  # 时间类型:审核时间、最后修改时间、制单时间、作废时间
            "date_from": "2026-02-05",  # 开始时间
            "date_to": "2026-02-10",  # 结束时间
            "page_no": 1,
            "page_size": 10,
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_purchase_order_save(self, **kwargs):
        """
        采购订单新增

        doc: https://console.nhsoft.cn/documents/api-doc/122/123/nhsoft.amazon.purchase.order.save
        """
        req_url = f"{self.host}/api/nhsoft.amazon.purchase.order.save"

        str_format = "%Y-%m-%d"
        now_date = datetime.datetime.now()
        next_month = now_date + datetime.timedelta(days=30)

        req_data = {
            "branch_num": "",  # integer 必填 门店编码
            "storehouse_num": "",  # integer 必填 仓库编码
            "supplier_num": "",  # integer 必填 供应商编码
            "purchase_order_operator": "",  # string 必填 操作人
            "purchase_order_memo": "",  # string 备注
            "purchase_order_bill_no": "",  # string 外部流水号(即将废弃)
            "purchase_order_out_bill_no": "",  # string 外部流水号(长度小于50个字符)
            "purchase_order_employee": "",  # string 业务员
            "purchase_order_date": now_date.strftime(
                str_format
            ),  # string 必填 采购日期 yyyy-MM-dd
            "purchase_order_deadline": next_month.strftime(
                str_format
            ),  # string 必填 交货期限 yyyy-MM-dd
            "purchase_order_details": [],  # array<object> 必填 订单明细
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_purchase_order_saveandaudit(self, **kwargs):
        """
        采购订单新增并审核

        doc: https://console.nhsoft.cn/documents/api-doc/122/123/nhsoft.amazon.purchase.order.saveandaudit
        """
        req_url = f"{self.host}/api/nhsoft.amazon.purchase.order.saveandaudit"

        str_format = "%Y-%m-%d"
        now_date = datetime.datetime.now()
        next_month = now_date + datetime.timedelta(days=30)

        req_data = {
            "branch_num": "",  # integer 必填 门店编码
            "storehouse_num": "",  # integer 必填 仓库编码
            "supplier_num": "",  # integer 必填 供应商编码
            "purchase_order_operator": "",  # string 必填 操作人
            "purchase_order_memo": "",  # string 备注
            "purchase_order_bill_no": "",  # string 外部流水号(即将废弃)
            "purchase_order_out_bill_no": self.get_oid(
                "PO"
            ),  # string 外部流水号(长度小于50个字符)
            "purchase_order_employee": "",  # string 业务员
            "purchase_order_date": now_date.strftime(
                str_format
            ),  # string 必填 采购日期 yyyy-MM-dd
            "purchase_order_deadline": next_month.strftime(
                str_format
            ),  # string 必填 交货期限 yyyy-MM-dd
            "purchase_order_details": [],  # array<object> 必填 订单明细
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_purchase_order_read(self, **kwargs):
        """
        采购订单读取

        doc: https://console.nhsoft.cn/documents/api-doc/122/123/nhsoft.amazon.purchase.order.read
        """
        req_url = f"{self.host}/api/nhsoft.amazon.purchase.order.read"

        req_data = {
            "purchase_order_fid": "",  # string 采购订单号(和外部流水号二选一)
            "purchase_order_bill_no": "",  # string 外部流水号(和采购订单号二选一)
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    # -------------------- 门店 --------------------
    async def nhsoft_amazon_branch_list(self, **kwargs):
        """
        获取所有门店

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/15/nhsoft.amazon.branch.list
        """
        req_url = f"{self.host}/api/nhsoft.amazon.branch.list/v2"

        req_data = {
            "page_no": 1,
            "page_size": 100,
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def usercenter_basic_branch_find(self, **kwargs):
        """
        门店查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/15/nhsoft.usercenter.basic.branch.find
        """
        req_url = f"{self.host}/api/nhsoft.usercenter.basic.branch.find"

        req_data = {
            "name": "",  # 门店名称
            "code": "",  # 门店编码
            # "type": "",  # 类型（SYSTEM|USER）
            "region_id": "",  # 区域ID
            "branch_nums": "",  # 用户中心门店id array<integer>
            "branch_ids": "",  # 门店ID列表 array<integer>
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    # -------------------- 仓库 --------------------
    async def nhsoft_amazon_basic_storehouse_find(self, **kwargs):
        """
        仓库查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/29/nhsoft.amazon.basic.storehouse.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.storehouse.find"

        req_data = {
            "branch_num": "",
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    # -------------------- 供应商档案 --------------------
    async def nhsoft_amazon_basic_supplier_find(self, **kwargs):
        """
        供应商查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/26/nhsoft.amazon.basic.supplier.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.supplier.find"

        req_data = {
            "branch_num": "",  # integer 必填 门店编码
            "actived": True,  # boolean 是否启用
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_basic_supplier_read(self, **kwargs):
        """
        供应商读取

        doc: https://console.nhsoft.cn/documents/api-doc/1/26/nhsoft.amazon.basic.supplier.read
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.supplier.read"

        req_data = {
            "supplier_num": "",  # integer 供应商编码（合作伙伴ID二选一）
            "user_center_partner_id": "",  # integer 合作伙伴ID（供应商编码二选一）
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    # -------------------- 商品档案 --------------------
    async def nhsoft_amazon_basic_item_find(self, **kwargs):
        """
        商品档案查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/2/nhsoft.amazon.basic.item.find

        支持根据分页参数动态添加 item_nums，只返回有库存的商品。
        item_nums 从 inventory_item_nums.json 读取，根据 page_no 和 page_size 动态切片。

        当传入 item_category_code 时：
        - 从 inventory_category_map.json 筛选匹配分类的商品（支持树形匹配，如"10"匹配"1001"、"100101"等）
        - 对筛选结果分页后调用乐檬API
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.item.find/v2"

        # 读取库存商品编码列表
        inventory_storage = get_inventory_storage()
        inventory_item_nums = inventory_storage.get_item_nums()

        # 读取商品分类映射
        category_map = inventory_storage.get_category_map()

        req_data = {
            "page_no": 1,
            "page_size": 10,
            # "item_type": 1,  # 商品类型编号(1:标准4:组合商品5:非库存商品6:制单组合7:制单拆分8:自定义组合9:成分商品10:分级商品11:原料商品)
            "item_category_code": "",  # 商品类别编码
            "item_nums": [],  # 商品编码列表
            # "filter_sleep": True,  # boolean 是否过滤休眠商品（true过滤，false不过滤，默认true）
            # "filter_weed_out": True,  # boolean 是否过滤淘汰商品（true过滤，false不过滤，默认true）
        }
        req_data.update(kwargs or {})

        page_no = req_data.get("page_no", 1)
        page_size = req_data.get("page_size", 10)
        category_code = req_data.get("item_category_code", "")

        # 根据是否传入分类参数决定筛选逻辑
        if category_code:
            # 传入分类：本地筛选匹配分类的商品（树形匹配，如"10"匹配"1001"、"100101"等）
            filtered_item_nums = [
                item_num
                for item_num in inventory_item_nums
                if category_map.get(str(item_num), "").startswith(category_code)
            ]
            # 对筛选结果分页
            start_idx = (page_no - 1) * page_size
            end_idx = start_idx + page_size
            page_item_nums = filtered_item_nums[start_idx:end_idx]

            if not page_item_nums:
                return [], f"分类 {category_code} 下无有库存商品"
        else:
            # 未传入分类：使用原有逻辑，从库存列表分页
            start_idx = (page_no - 1) * page_size
            end_idx = start_idx + page_size
            page_item_nums = inventory_item_nums[start_idx:end_idx]

        # 确保 item_nums 不为空
        if page_item_nums and len(page_item_nums) > 0:
            req_data["item_nums"] = page_item_nums
        else:
            return [], "库存商品列表为空"

        # 如果传入了分类，本地已经筛选完毕，不需要再传 item_category_code 给乐檬
        # 否则乐檬会按 AND 逻辑处理（item_nums AND item_category_code），导致结果为空
        if category_code:
            req_data.pop("item_category_code", None)

        # 给乐檬传的 page_no 固定为 1，分页由我们自己的 page_no 控制
        req_data["page_no"] = 1

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_basic_item_read(self, **kwargs):
        """
        商品档案读取

        doc: https://console.nhsoft.cn/documents/api-doc/1/2/nhsoft.amazon.basic.item.read
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.item.read"

        req_data = {
            "item_num": "",
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_basic_itemcategory_find(self):
        """
        商品类别查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/2/nhsoft.amazon.basic.itemcategory.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.itemcategory.find"

        return await self.send_request("GET", req_url)

    async def nhsoft_amazon_basic_department_find(self):
        """
        商品部门查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/2/nhsoft.amazon.basic.department.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.department.find"

        return await self.send_request("GET", req_url)

    async def nhsoft_amazon_basic_itemimage_find(self, **kwargs):
        """
        查询商品所有图片

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/2/nhsoft.amazon.basic.itemimage.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.itemimage.find"

        req_data = {
            "item_nums": [],  # 商品编码列表
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_basic_item_image_find(self, **kwargs):
        """
        商品档案图片查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/2/nhsoft.base.basic.item.image.find
        """
        req_url = f"{self.host}/api/nhsoft.base.basic.item.image.find"

        req_data = {
            "item_num": "",  # 商品编号
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    # -------------------- 库存查询 --------------------
    async def nhsoft_amazon_inventory_find(self, **kwargs):
        """
        库存查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/3/nhsoft.amazon.inventory.inventory.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.inventory.inventory.find/v2"

        req_data = {
            "storehouse_num": "",  # integer 必填 仓库编码
            "item_nums": [],  # array<integer> 商品编码列表
            "page_no": 1,  # integer 必填 查询页码
            "page_size": 100,  # integer 必填 查询分页大小
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_basic_client_find(self, **kwargs):
        """
        客户查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/25/nhsoft.amazon.basic.client.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.client.find"

        req_data = {
            "branch_num": "",  # integer 门店编码
            "client_fids": [],  # array<string> 客户编码列表
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    async def nhsoft_amazon_basic_client_category_find(self, **kwargs):
        """
        客户类别查询

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/25/nhsoft.amazon.basic.clientcategory.find
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.clientcategory.find"

        return await self.send_request("GET", req_url)

    async def nhsoft_amazon_basic_client_save(self, **kwargs):
        """
        客户新增

        doc: https://console.nhsoft.cn/pages/func/api-manage/1/25/nhsoft.amazon.basic.client.save
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.client.save"

        req_data = {
            # "client_parent_fid": "",  # 父级客户编码
            "branch_num": "",  # integer 门店编码
            "client_name": "",  # 客户名称
            "client_code": "",  # 客户代码
            "client_mobile": "",  # 联系电话
            "client_type": "",  # 客户类别
            "client_birth": "",  #  客户生日
            "client_settlement_type": "",  # 结算方式(临时指定、指定帐期、指定日期、货到付款、款到发货)
            "client_settle_day_of_month": "",  # 月结日期 11 ?
            "client_settle_period": "",  # 结转周期 30 ?
            "client_settlement_model": "",  # 结算模式(所属门店结算、业务发生门店结算)
            "client_credit_enable": "",  # 是否启用信用额度(1启用,0不启用)
            "client_credit_limit": "",  # 信用额度
            "wholesale_book_balance_enough_enable": "",  # 商城下单需保证余额充足(1启用,0不启用)
            "client_usual_discount": "",  # 零售价折扣值 0.9 ?
            "client_price_level": "",  # 零售价价格级别 '1' ?
            "client_wholesale_discount": "",  # 批发价折扣 0.9 ?
            "client_wholesale_level": "",  # 批发价格级别 '1' ?
            "client_actived": "",  # integer 是否启用(1启用,0不启用)
            "client_shared": "",  # integer 是否共享(1共享,0不共享）
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_basic_client_update(self, **kwargs):
        """
        客户修改

        doc: https://console.nhsoft.cn/documents/api-doc/1/25/nhsoft.amazon.basic.client.update
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.client.update"

        req_data = {
            "client_fid": "",  # 客户编号
            # ....详见接口文档
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)

    async def nhsoft_amazon_basic_client_address_read(self, **kwargs):
        """
        客户地址列表查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/25/nhsoft.amazon.basic.client.address.read
        """
        req_url = f"{self.host}/api/nhsoft.amazon.basic.client.address.read"

        req_data = {
            "client_fid": "",  # string 客户主键（合作伙伴ID）二选一
        }
        req_data.update(kwargs or {})

        return await self.send_request("GET", req_url, req_data)

    # -------------------- 乐檬新零售 --------------------
    async def nhsoft_mercury_basic_item_find(self, **kwargs):
        """
        商城商品查询

        doc: https://console.nhsoft.cn/documents/api-doc/1/2/nhsoft.mercury.basic.item.find
        """
        req_url = f"{self.host}/api/nhsoft.mercury.basic.item.find"

        req_data = {
            "page_no": 1,  # integer 必填 查询页码 从1开始
            "page_size": 10,  # integer 必填 查询分页大小，最大200
            "attribute_id": "",  # integer 商品属性ID
            "auto_on_sale": None,  # boolean 是否自动上架
            "barcode": "",  # string 商品条码
            "category_ids": [],  # array<integer> 商品分类ID列表
            "code": "",  # string 商品代码
            "delete_flag": None,  # boolean 是否删除
            "enable": None,  # boolean 是否启用
            "enable_negative_inventory": None,  # boolean 是否允许负库存
            "group_id": "",  # integer 商品分组ID
            "id": "",  # string 商品ID(支持多商品，逗号分开)
            "item_name_or_code_or_barcode": "",  # string 外部商品名称 商品规格值 商品条码
            "label_id": "",  # integer 商品标签ID
            "manual": None,  # boolean 是否手工指定商品
            "name": "",  # string 商品名称
            "query_sold_amount": None,  # boolean 是否查询销量 不传默认查询
            "self_pick_days": None,  # boolean 是否允许自提
            "simple_group": None,  # boolean 商品分组只查询 本分组的商品
            "stop_sale": None,  # boolean 是否停售
            "sync_inventory": None,  # boolean 是否同步库存
            "variant_ids": [],  # array<integer> 商品规格ID列表
            "variant_inventory": None,  # boolean 商品规格是否同步库存
        }
        req_data.update(kwargs or {})

        return await self.send_request("POST", req_url, req_data)
