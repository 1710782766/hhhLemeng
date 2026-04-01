import os
import json
from pathlib import Path
import time
import base64
import urllib.parse
import tornado.httpclient
import tornado.locks


class NhsoftTokenManager:
    """
    乐檬开放平台 Token 管理
    """

    TOKEN_URL = "https://cloud.nhsoft.cn/authserver/oauth/token"

    def __init__(
        self,
        app_id: str,
        secret: str,
        work_path: Path,
        redirect_uri: str,
        token_file_path: str = "./nhsoft_token_cache.json",
        expire_advance_seconds: int = 120,
        request_timeout: int = 15,
    ):
        self.app_id = app_id
        self.secret = secret
        self.token_file_path = work_path / token_file_path
        self.expire_advance_seconds = expire_advance_seconds
        self.request_timeout = request_timeout
        self.redirect_uri = redirect_uri

        self._http = tornado.httpclient.AsyncHTTPClient()
        self._refresh_lock = tornado.locks.Lock()

    async def get_access_token(self) -> str:
        """
        获取可用 access_token（自动读取缓存、自动刷新）
        """
        token_data = self._load_token_from_file()

        # 1) 有缓存且未过期：直接返回
        if token_data and self._is_token_valid(token_data):
            return token_data["access_token"]

        # 2) 无缓存/已过期：尝试刷新
        # 并发保护：同一时间只允许一个协程刷新
        async with self._refresh_lock:
            token_data = self._load_token_from_file()
            if token_data and self._is_token_valid(token_data):
                return token_data["access_token"]

            if token_data and token_data.get("refresh_token"):
                new_data = await self._refresh_token(token_data["refresh_token"])
                self._save_token_to_file(new_data)
                return new_data["access_token"]

            raise RuntimeError(
                "Nhsoft token missing: no valid token cache and no refresh_token found."
            )

    async def exchange_code_for_token(self, code: str) -> dict:
        """
        第一次授权后，用 code 换取 token，并写入缓存文件
        """
        new_data = await self._request_token_by_authorization_code(
            code, self.redirect_uri
        )
        self._save_token_to_file(new_data)
        return new_data

    async def _request_token_by_authorization_code(
        self, code: str, redirect_uri: str
    ) -> dict:
        """
        grant_type = authorization_code
        """
        body_dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        return await self._post_token(body_dict)

    async def _refresh_token(self, refresh_token: str) -> dict:
        """
        grant_type = refresh_token
        """
        body_dict = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        return await self._post_token(body_dict)

    async def _post_token(self, body_dict: dict) -> dict:
        """
        POST https://cloud.nhsoft.cn/authserver/oauth/token
        Content-Type: application/x-www-form-urlencoded
        Authorization: Basic base64(appId:secret)
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._build_basic_auth(),
        }

        body = urllib.parse.urlencode(body_dict)

        req = tornado.httpclient.HTTPRequest(
            url=self.TOKEN_URL,
            method="POST",
            headers=headers,
            body=body,
            request_timeout=self.request_timeout,
        )

        resp = await self._http.fetch(req, raise_error=False)

        if resp.code != 200:
            raw = (resp.body or b"").decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Nhsoft token request failed, code={resp.code}, body={raw}"
            )

        data = json.loads(resp.body.decode("utf-8"))

        # 标准化 + 写入过期时间
        return self._normalize_token_data(data)

    def _build_basic_auth(self) -> str:
        """
        Authorization: Basic base64(appId:secret)
        """
        raw = f"{self.app_id}:{self.secret}".encode("utf-8")
        b64 = base64.b64encode(raw).decode("utf-8")
        return f"Basic {b64}"

    def _normalize_token_data(self, data: dict) -> dict:
        """
        把返回的 token 信息补全 expire_at（本地时间戳）
        """
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = int(data.get("expires_in") or 0)

        if not access_token:
            raise RuntimeError(f"Nhsoft token response missing access_token: {data}")

        now = int(time.time())
        expire_at = now + expires_in

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "expire_at": expire_at,
            "token_type": data.get("token_type"),
            "scope": data.get("scope"),
            "jti": data.get("jti"),
            "Nhsoft-Merchant-Id": data.get("Nhsoft-Merchant-Id"),
        }

    def _is_token_valid(self, token_data: dict) -> bool:
        """
        判断 token 是否仍有效（带提前刷新窗口）
        """
        access_token = token_data.get("access_token")
        expire_at = int(token_data.get("expire_at") or 0)

        if not access_token or expire_at <= 0:
            return False

        now = int(time.time())

        # expire_advance_seconds：提前刷新，避免刚拿到就过期
        return now < (expire_at - self.expire_advance_seconds)

    def _load_token_from_file(self) -> dict | None:
        if not os.path.exists(self.token_file_path):
            return None

        try:
            with open(self.token_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            return None

        return None

    def _save_token_to_file(self, token_data: dict) -> None:
        # 确保目录存在
        folder = os.path.dirname(os.path.abspath(self.token_file_path))
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        with open(self.token_file_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
