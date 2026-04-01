import asyncio
import json
import shutil
import urllib.parse
from datetime import datetime
from pathlib import Path

from hhh_lemeng.handler.common.lemeng.pringLog import get_log
from hhh_lemeng.handler.service.hhhLemengService import HhhLemengService
from hhh_lemeng.handler.common.lemeng.data_path import (
    get_data_dir,
    get_backup_dir,
    get_inventory_data_file,
    get_inventory_nums_file,
    get_inventory_meta_file,
    get_inventory_category_map_file,
)


async def update_inventory_data(
    lemengService: HhhLemengService, storehouse_num: int = 264030025
):
    """库存更新 - 每天可调用数次，更新库存数据

    路径: hhh_lemeng/handler/data/
    - inventory_data.json      # 完整库存数据
    - inventory_item_nums.json # 商品编码列表
    - inventory_meta.json      # 更新时间和总数
    - inventory_data_*.json    # 历史备份（保留3份）
    """
    work_path = get_data_dir()
    backup_dir = get_backup_dir()
    data_file = get_inventory_data_file()
    nums_file = get_inventory_nums_file()
    meta_file = get_inventory_meta_file()
    category_map_file = get_inventory_category_map_file()

    # 1. 备份旧数据（保留最近3份到 backup/ 目录）
    if data_file.exists():
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"inventory_data_{timestamp}.json"
        shutil.copy(data_file, backup_file)
        print(f"📦 已备份旧数据到: {backup_file.relative_to(Path.cwd())}")
        # 清理旧备份，只保留3份
        backups = sorted(
            backup_dir.glob("inventory_data_*.json"), key=lambda p: p.stat().st_mtime
        )
        for old_backup in backups[:-3]:
            old_backup.unlink()
            print(f"🗑️  删除旧备份: {old_backup.name}")

    # 2. 循环获取所有库存数据
    all_items = []
    page_no = 1
    page_size = 100

    while True:
        result, _ = await lemengService.nhsoft_amazon_inventory_find(
            storehouse_num=storehouse_num,
            page_no=page_no,
            page_size=page_size,
        )
        if not result:
            print(f"第 {page_no} 页无数据，停止翻页")
            break
        all_items.extend(result)
        print(f"第 {page_no} 页获取 {len(result)} 条数据，当前累计 {len(all_items)} 条")
        page_no += 1

    # 3. 保存数据
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    # 4. 保存 item_nums 列表
    items = [item.get("item_num") for item in all_items]
    with open(nums_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)

    # 5. 保存元数据
    meta = {
        "updated_at": datetime.now().isoformat(),
        "total_count": len(all_items),
        "storehouse_num": storehouse_num,
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 6. 批量并发获取商品分类信息并缓存
    print("\n📦 正在并发获取商品分类信息...")
    category_map = {}
    batch_size = 100
    max_concurrency = 10  # 最大并发数
    host = "https://cloud.nhsoft.cn"
    token = await lemengService.get_token()
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }

    http_client = __import__(
        "tornado.httpclient", fromlist=["AsyncHTTPClient"]
    ).AsyncHTTPClient()

    async def fetch_batch(batch_nums: list) -> list:
        """并发获取单个batch的分类信息"""
        req_url = f"{host}/api/nhsoft.amazon.basic.item.find/v2"
        req_data = {"page_no": 1, "page_size": len(batch_nums), "item_nums": batch_nums}
        query = urllib.parse.urlencode(req_data, doseq=True)
        url = req_url + "?" + query
        request = __import__(
            "tornado.httpclient", fromlist=["HTTPRequest"]
        ).HTTPRequest(url=url, method="GET", headers=headers, validate_cert=False)
        response = await http_client.fetch(request)
        result = json.loads(response.body.decode("utf-8"))
        items_list, _ = lemengService.process_resp(result)
        return items_list

    # 将items分成batches
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    # 使用信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch_with_semaphore(batch_nums):
        async with semaphore:
            return await fetch_batch(batch_nums)

    # 并发执行所有batch
    total_batches = len(batches)
    print(f"   共 {total_batches} 个批次，最大并发 {max_concurrency}")

    # 分组并发执行，每完成一组打印进度
    for batch_idx in range(0, total_batches, max_concurrency):
        group_end = min(batch_idx + max_concurrency, total_batches)
        group_batches = [
            fetch_with_semaphore(batches[i]) for i in range(batch_idx, group_end)
        ]
        results = await asyncio.gather(*group_batches)

        # 收集结果
        for items_list in results:
            for item in items_list:
                item_num = item.get("item_num")
                category_code = item.get("item_category_code", "")
                if item_num and category_code:
                    category_map[item_num] = category_code

        # 计算实际处理的商品数量
        processed_items = min(group_end * batch_size, len(items))
        print(
            f"   进度 {processed_items}/{len(items)} 条 ({processed_items * 100 // len(items)}%)"
        )

    with open(category_map_file, "w", encoding="utf-8") as f:
        json.dump(category_map, f, ensure_ascii=False)
    print(f"✅ 分类信息已缓存: {len(category_map)} 条商品")

    print(f"\n✅ 库存更新完成！共 {len(all_items)} 条商品")
    print(f"📅 更新时间: {meta['updated_at']}")
    print(f"📁 数据路径: {work_path}")

    return len(all_items)


async def main():
    work_path = Path.cwd() / "hhh_lemeng"
    lemengService = HhhLemengService("dev", get_log(work_path))

    # await lemengService.init_token("FydrPB")

    # result = await lemengService.get_token()
    # print(result)

    """
    code=4P23nl&state=1
    https://cloud.nhsoft.cn/authserver/oauth/authorize?response_type=code&state=1&client_id=93ec09e991d6469288c5fe38fe91c927&redirect_uri=http://127.0.0.1:8167/api/lmOauthCodeCallback
    账号：15074132888
    """

    # ========== 门店 ==========
    # result, _ = await lemengService.nhsoft_amazon_branch_list()
    # print(result)

    # result, _ = await lemengService.usercenter_basic_branch_find(branch_ids=[99357])
    # print(result)

    # ========== 获取仓库 ==========
    # result, _ = await lemengService.nhsoft_amazon_basic_storehouse_find(branch_num=99)
    # print(result)

    # await update_inventory_data(lemengService)

    # ========== 商品档案查询-有库存商品 ==========
    # 不传分类：返回所有有库存商品
    # result, msg = await lemengService.nhsoft_amazon_basic_item_find(
    #     page_no=1, page_size=10
    # )
    # print(f"\n不分页 - msg: {msg}, count: {len(result) if result else 0}")

    # 传分类：返回该分类下有库存的商品（支持树形匹配，如"65"匹配"650302"、"650408"等）
    # result, msg = await lemengService.nhsoft_amazon_basic_item_find(
    #     page_no=1, page_size=10, item_category_code="65"
    # )
    # print(f"分类65 - msg: {msg}, count: {len(result) if result else 0}")

    # result, _ = await lemengService.nhsoft_amazon_basic_item_read(item_num=14703)
    # print(result)

    # result, _ = await lemengService.nhsoft_mercury_basic_item_find(page_size=5)
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_itemcategory_find()
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_department_find()
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_itemimage_find(
    #     item_nums=[62060, 62061, 62062, 62063, 62064, 62065, 62066, 62067, 62068, 62069]
    # )
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_item_image_find(
    #     item_num="62067"
    # )
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_client_find(
    #     client_fids=["0026403010000001", "0026403990003940", "0026403990003941"]
    # )
    # print(result)

    # post_data = {
    #     "branch_num": "99",
    #     "client_name": "好惠花-测试3",
    #     "client_code": "11903",
    #     "client_mobile": "18331511903",
    #     "client_type": "好惠花",
    #     "client_birth": "2000-01-01",
    #     "client_settlement_type": "临时指定",
    #     "client_settle_day_of_month": "11",
    #     "client_settle_period": "30",
    #     "client_settlement_model": "所属门店结算",
    #     "client_credit_enable": 1,
    #     "client_credit_limit": 10000,
    #     "wholesale_book_balance_enough_enable": 0,
    #     "client_usual_discount": 0.9,
    #     "client_price_level": "1",
    #     "client_wholesale_discount": 0.9,
    #     "client_wholesale_level": "1",
    #     "client_actived": 1,
    #     "client_shared": 1,
    #     "client_level_name": "好惠花",
    #     "client_addr": "浙江省杭州市滨江区江南大道3888号3幢1单元5楼",
    #     "client_ship_addr": "浙江省杭州市滨江区江南大道3888号3幢1单元5楼",
    #     "client_linkman": "好测-3",
    #     "client_phone": "18331511903",
    # }
    # result, _ = await lemengService.nhsoft_amazon_basic_client_save(**post_data)
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_basic_client_category_find()
    # print(result)

    # post_data = {
    #     "client_fid": "0026403990003940",  # 0026403990003940 | 0026403010000001 | 0026403990003941
    #     "branch_num": "99",
    #     "client_addr": "浙江省杭州市滨江区江南大道3888号3幢1单元5楼",
    #     "client_ship_addr": "浙江省杭州市滨江区江南大道3888号3幢1单元5楼",
    #     "client_type": "好惠花",
    #     "client_level_name": "好惠花",
    #     "client_mobile": "18331511902",
    #     "client_linkman": "好测-1",
    #     "client_phone": "18331511902",
    # }
    # result, _ = await lemengService.nhsoft_amazon_basic_client_update(**post_data)
    # print(result)

    # ========== 批发订单新增测试 ==========
    # post_data = {
    #     "branch_num": 99,
    #     "storehouse_num": 264030025,
    #     "client_fid": "0026403990003941",  # 0026403010000001
    #     "client_name": "好惠花",
    #     "wholesale_book_operator": "好惠花",
    #     "wholesale_book_memo": "好惠花测试商品请勿发货....",
    #     "wholesale_book_details": [
    #         # {
    #         #     "item_num": 20421,  # 商品编码
    #         #     "item_use_qty": 3.000,  # 订购数量（小数点3位）
    #         #     "item_use_unit": "件",  # 订购单位（商品档案中取item_wholesale_unit为批发单位）
    #         # },
    #         {
    #             "item_num": 20439,  # 商品编码
    #             "item_use_qty": 2.000,  # 订购数量（小数点3位）
    #             "item_use_unit": "件",  # 订购单位（商品档案中取item_wholesale_unit为批发单位）
    #         }
    #     ],
    #     # "address_id": "0026403010000001-1",
    #     # "wholesale_book_transfer_type": "商家配送",  # 配送方式
    #     # "wholesale_book_receivor": "好惠花1",  # 收货人（可选，配送方式为商家配送时必填）
    #     # "wholesale_book_phone": "18331511901",  # 收货人电话（可选，配送方式为商家配送时必填）
    #     # "client_address": "湖南省|益阳市|赫山区|朝阳学校",
    # }
    # result, _ = await lemengService.nhsoft_amazon_wholesale_book_save(**post_data)
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_wholesale_book_find(
    #     client_fid="0026403010000001"
    # )
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_wholesale_book_read(
    #     wholesale_book_fid="WB26403990004263"
    # )
    # print(result)

    # result, _ = await lemengService.nhsoft_amazon_purchase_order_find()
    # print(result)

    # ========== 获取供应商编码示例 ==========
    # result, _ = await lemengService.nhsoft_amazon_basic_supplier_find(branch_num=2)
    # print(result)  # 从返回结果中获取 supplier_num

    # ========== 采购订单新增并审核测试 ==========
    # post_data = {
    #     "branch_num": 2,  # 门店编码
    #     "storehouse_num": 264030003,  # 仓库编码
    #     "supplier_num": 264031029,  # 供应商编码（通过 nhsoft_amazon_basic_supplier_find 获取）
    #     "purchase_order_operator": "好惠花",  # 操作人
    #     "purchase_order_memo": "好惠花采购订单测试备注",
    #     "purchase_order_details": [
    #         {
    #             "item_num": 20421,  # 商品编码
    #             "item_use_qty": 10.000,  # 采购数量（小数点3位）
    #             "item_use_price": 5.00,  # 采购单价
    #             "item_use_unit": "件",  # 采购单位
    #         }
    #     ],
    # }
    # result, _ = await lemengService.nhsoft_amazon_purchase_order_saveandaudit(
    #     **post_data
    # )
    # print(result)

    # ========== 采购订单读取测试 ==========
    # result, _ = await lemengService.nhsoft_amazon_purchase_order_read(
    #     purchase_order_fid="PO26403020000005"
    # )
    # print(result)

    # ========== 客户地址列表查询 ==========
    # result, _ = await lemengService.nhsoft_amazon_basic_client_address_read(
    #     client_fid="0026403010000001"
    # )
    # print(result)

    # ========== 库存查询 ==========
    result, _ = await lemengService.nhsoft_amazon_inventory_find(
        storehouse_num=264030025,
        # item_nums=[
        #     62070,
        #     62071,
        #     62072,
        #     62073,
        #     62074,
        #     62075,
        #     62076,
        #     62077,
        #     62078,
        #     62079,
        # ],
        page_no=1,
        page_size=100,
    )
    print(result)
    print([item.get("item_num") for item in result])

    # await update_inventory_data(lemengService)

    # ========== 商品档案查询-有库存商品 ==========
    # result, msg = await lemengService.nhsoft_amazon_basic_item_find(
    #     page_no=1, page_size=10
    # )
    # # print(f"msg: {msg}, count: {len(result) if result else 0}")
    # print(result)


if __name__ == "__main__":
    asyncio.run(main())
