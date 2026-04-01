import os
from pathlib import Path
import signal
import tornado
from tornado.options import define, options

from hhh_lemeng.handler.common.lemeng.pringLog import get_log

from hhh_lemeng.handler.hhhLemeng import (
    LmOauthCodeCallback,
    ShopItemFind,
    MallItemFind,
    ShopCategoryFind,
    ShopItemDetail,
    WholesaleOrderCreate,
    WholesaleOrderFind,
    WholesaleOrderDetail,
    WholesaleOrderDelete,
    ClientAddressList,
    AddressList,
    AddressCreate,
    InventoryFind,
)
from hhh_lemeng.handler.service.hhhLemengService import HhhLemengService


define("port", type=int, default=8167, help="run on the given port")


# 创建路由表
raw_urls = [
    (r"/lmOauthCodeCallback", LmOauthCodeCallback),
    # 商品相关
    (r"/shopItemFind.do", ShopItemFind),
    (r"/mallItemFind.do", MallItemFind),
    (r"/shopCategoryFind.do", ShopCategoryFind),
    (r"/shopItemDetail.do", ShopItemDetail),
    # 批发订单相关
    (r"/wholesaleOrderCreate.do", WholesaleOrderCreate),
    (r"/wholesaleOrderFind.do", WholesaleOrderFind),
    (r"/wholesaleOrderDetail.do", WholesaleOrderDetail),
    (r"/wholesaleOrderDelete.do", WholesaleOrderDelete),
    # 客户相关
    (r"/clientAddressList.do", ClientAddressList),
    # 本地维护的收货地址相关
    (r"/addressList.do", AddressList),
    (r"/addressCreate.do", AddressCreate),
    # 库存查询
    (r"/inventoryFind.do", InventoryFind),
]
urls = [(r"/api" + pattern, handler) for pattern, handler in raw_urls]


def make_app():
    work_path = Path.cwd() / "hhh_lemeng"
    return tornado.web.Application(
        urls,
        autoreload=False,
        debug=False,
        hhh_lm=HhhLemengService("dev", get_log(work_path)),
    )


def shutdown(sig, frame):
    print(f"🛑 Received signal {sig}, shutting down...")
    tornado.ioloop.IOLoop.current().add_callback_from_signal(
        tornado.ioloop.IOLoop.current().stop
    )


# 定义服务器
def open_serve():
    APP_ENV = os.environ.get("APP_ENV", "dev")

    # 创建应用实例
    app = make_app()

    server = tornado.httpserver.HTTPServer(
        app,
        xheaders=True,
    )
    server.bind(options.port, address="0.0.0.0")

    if APP_ENV == "prod":
        server.start(0)  # 多进程
    else:
        server.start(1)  # 单进程

    print(f"🚀 Server started on {options.port} ({APP_ENV})")

    loop = tornado.ioloop.IOLoop.current()
    loop.start()


# 应用运行入口，解析命令行参数
if __name__ == "__main__":
    # 从命令行解析全局选项。
    tornado.options.parse_command_line()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 启动服务器
    open_serve()
