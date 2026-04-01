"""
收货地址数据库管理模块
使用本地 JSON 文件存储地址与乐檬客户FID的映射关系
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class AddressDB:
    """地址数据库操作类"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "address_db.json"
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({"addresses": [], "uid_sequence": {}})

    def _load_data(self) -> Dict:
        """加载数据库数据"""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"addresses": [], "uid_sequence": {}}

    def _save_data(self, data: Dict):
        """保存数据库数据"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _generate_address_id(self, uid: str) -> str:
        """生成地址ID

        规则: uid + 序号(自增)
        例如: 3901383351133131, 3901383351133132
        """
        data = self._load_data()
        uid_sequence = data.get("uid_sequence", {})

        # 获取当前 uid 的序号
        current_seq = uid_sequence.get(uid, 0)
        current_seq += 1
        uid_sequence[uid] = current_seq

        # 保存序号
        data["uid_sequence"] = uid_sequence
        self._save_data(data)

        return f"{uid}{current_seq}"

    def get_next_client_code(self, uid: str) -> str:
        """获取下一个 client_code

        client_code 格式: uid + 序号(自增)
        与 address_id 共用序号
        """
        # 直接复用 _generate_address_id，确保序号被正确占用
        return self._generate_address_id(uid)

    def add_address(
        self,
        uid: str,
        name: str,
        phone: str,
        province: str,
        city: str,
        district: str,
        detail: str,
        client_fid: str,
    ) -> Dict:
        """添加新地址

        Args:
            uid: 用户ID
            name: 收货人姓名
            phone: 收货人电话
            province: 省份
            city: 城市
            district: 区县
            detail: 详细地址
            client_fid: 乐檬客户FID

        Returns:
            添加的地址信息
        """
        data = self._load_data()
        addresses = data.get("addresses", [])

        # 生成地址ID
        address_id = self._generate_address_id(uid)

        # 检查是否第一个地址,第一个设为默认
        is_default = len([a for a in addresses if a.get("uid") == uid]) == 0

        # 如果有其他默认地址,取消默认
        if is_default:
            for addr in addresses:
                if addr.get("uid") == uid and addr.get("is_default"):
                    addr["is_default"] = False

        address = {
            "id": address_id,
            "uid": uid,
            "name": name,
            "phone": phone,
            "province": province,
            "city": city,
            "district": district,
            "detail": detail,
            "client_fid": client_fid,
            "is_default": is_default,
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        addresses.append(address)
        data["addresses"] = addresses
        self._save_data(data)

        return address

    def get_addresses_by_uid(self, uid: str) -> List[Dict]:
        """获取用户的所有地址"""
        data = self._load_data()
        addresses = data.get("addresses", [])

        # 过滤该用户的地址,并构造返回格式
        result = []
        for addr in addresses:
            if addr.get("uid") == uid:
                result.append(
                    {
                        "id": addr["id"],
                        "name": addr["name"],
                        "phone": addr["phone"],
                        "province": addr["province"],
                        "city": addr["city"],
                        "district": addr["district"],
                        "detail": addr["detail"],
                        "client_fid": addr["client_fid"],
                        "full_address": f"{addr['province']}{addr['city']}{addr['district']}{addr['detail']}",
                        "is_default": addr["is_default"],
                    }
                )

        # 按创建时间排序,默认地址排最前
        result.sort(key=lambda x: (not x["is_default"], x["id"]))
        return result

    def get_address_by_id(self, address_id: str) -> Optional[Dict]:
        """根据地址ID获取地址信息"""
        data = self._load_data()
        addresses = data.get("addresses", [])

        for addr in addresses:
            if addr.get("id") == address_id:
                return {
                    "id": addr["id"],
                    "uid": addr["uid"],
                    "name": addr["name"],
                    "phone": addr["phone"],
                    "province": addr["province"],
                    "city": addr["city"],
                    "district": addr["district"],
                    "detail": addr["detail"],
                    "full_address": f"{addr['province']}{addr['city']}{addr['district']}{addr['detail']}",
                    "client_fid": addr["client_fid"],
                    "is_default": addr["is_default"],
                }

        return None

    def get_default_address(self, uid: str) -> Optional[Dict]:
        """获取用户的默认地址"""
        addresses = self.get_addresses_by_uid(uid)
        for addr in addresses:
            if addr["is_default"]:
                return addr
        # 没有默认地址,返回第一个
        return addresses[0] if addresses else None


# 全局实例
_address_db = None


def get_address_db() -> AddressDB:
    """获取地址数据库实例"""
    global _address_db
    if _address_db is None:
        _address_db = AddressDB()
    return _address_db
