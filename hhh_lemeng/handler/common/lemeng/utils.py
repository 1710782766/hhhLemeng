import base64
import datetime
import decimal
from functools import wraps
import json
import os
import tornado
import urllib.parse
from hhh_lemeng.handler.common.lemeng.encryption import decode_data, decode_data2

from typing import TYPE_CHECKING

from hhh_lemeng.handler.common.lemeng.error import LemRequestError

if TYPE_CHECKING:
    from hhh_lemeng.handler.service.hhhLemengService import HhhLemengService


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class APP_CFG:
    RESJSON = '{"status": %s, "message": "%s", "result": %s, "ext": %s}'


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header(
            "Access-Control-Allow-Origin", self.request.headers.get("Origin", "*")
        )
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header(
            "Access-Control-Allow-Headers",
            "x-requested-with, token, content-type, appid, channel, logintype, rid, sign, timestamp, uid, version, lat, lng",
        )
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Max-Age", "3600")
        self.set_header("Content-Type", "application/json;charset=utf-8")

        self.hhh_lm: "HhhLemengService" = self.application.settings["hhh_lm"]

    def _get_json(self):
        paras = self.get_body_argument("paras", "")
        if not paras:
            return {}
        try:
            return json.loads(decode_data(paras))
        except Exception as e:
            try:
                return json.loads(decode_data2(paras))
            except Exception as e2:
                return json.loads(paras)

    def _get_header(self, key: str):
        return self.request.headers.get(key)

    def _write_json(self, res: str):
        self.write(res)

    def options(self, *args, **kwargs):
        # 处理浏览器的预检请求
        self.set_status(204)
        self.finish()

    # def write_error(self, status_code, **kwargs):
    #     # exc = kwargs.get("exc_info")
    #     # print("exc: ", exc)
    #     self.set_status(500)
    #     res = APP_CFG.RESJSON % (2, "系统错误", {}, {})
    #     self._write_json(res)
    #     self.finish()

    async def response_success(
        self, data: dict = {}, ls: list = [], msg: str = "操作成功"
    ):
        _dict = {"data": data, "list": ls}
        res = json.dumps(_dict, separators=(",", ":"), cls=MyEncoder)
        res = str(res).replace(":null", ':""').replace(": None", ': ""')
        res = APP_CFG.RESJSON % (0, msg, res, {})
        self._write_json(res)
        await self.finish()

    def _print_info(self, paras):
        APP_ENV = os.environ.get("APP_ENV", "dev")
        if paras and APP_ENV == "dev":
            print(
                f"请求接口{self.request.uri} -- 请求参数：{json.dumps(paras, ensure_ascii=False)}"
            )


def error_handler(func):
    """
    错误处理器
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        self: BaseHandler = args[0]
        try:
            return await func(*args, **kwargs)
        except LemRequestError as e:
            err_msg = str(e)
            res = APP_CFG.RESJSON % (2, err_msg, {}, {})
            self._write_json(res)
            await self.finish()
            return None
        except Exception as e:
            self.hhh_lm.log.error(e)
            res = APP_CFG.RESJSON % (2, "系统异常", {}, {})
            self._write_json(res)
            await self.finish()

    return wrapper


def encode_proinfo(obj: dict) -> str:
    json_str = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    encoded = urllib.parse.quote(json_str, safe="~()*!.'")
    return base64.b64encode(encoded.encode("utf-8")).decode("utf-8")
