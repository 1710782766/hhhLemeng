"""
库存数据存储管理模块

统一管理库存相关的本地文件存储，便于将来迁移到数据库。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .storage import FileStorage


def _get_data_dir() -> Path:
    """获取数据目录路径（内部函数，避免循环依赖）"""
    return Path(__file__).parent.parent.parent.parent / "handler" / "data"


def _get_inventory_data_file() -> Path:
    """库存数据文件"""
    return _get_data_dir() / "inventory_data.json"


def _get_inventory_nums_file() -> Path:
    """库存商品编码列表文件"""
    return _get_data_dir() / "inventory_item_nums.json"


def _get_inventory_category_map_file() -> Path:
    """库存商品分类映射文件"""
    return _get_data_dir() / "inventory_category_map.json"


def _get_inventory_meta_file() -> Path:
    """库存更新元数据文件"""
    return _get_data_dir() / "inventory_meta.json"


def _get_backup_dir() -> Path:
    """库存备份目录"""
    return _get_data_dir() / "backup"


class InventoryStorage:
    """库存数据存储管理类"""

    def __init__(self):
        self._nums_storage = FileStorage(_get_inventory_nums_file(), default_data=[])
        self._category_map_storage = FileStorage(_get_inventory_category_map_file(), default_data={})
        self._meta_storage = FileStorage(_get_inventory_meta_file(), default_data={})

    # ==================== 商品编码列表 ====================

    def get_item_nums(self) -> List[Any]:
        """获取库存商品编码列表"""
        return self._nums_storage.load()

    def save_item_nums(self, item_nums: List[Any]) -> None:
        """保存库存商品编码列表"""
        self._nums_storage.save(item_nums)

    # ==================== 商品分类映射 ====================

    def get_category_map(self) -> Dict[str, str]:
        """获取商品分类映射 {item_num: category_code}"""
        return self._category_map_storage.load()

    def save_category_map(self, category_map: Dict[str, str]) -> None:
        """保存商品分类映射"""
        self._category_map_storage.save(category_map)

    # ==================== 元数据 ====================

    def get_meta(self) -> Dict[str, Any]:
        """获取更新元数据"""
        return self._meta_storage.load()

    def save_meta(self, total_count: int, storehouse_num: int) -> None:
        """保存更新元数据"""
        meta = {
            "updated_at": datetime.now().isoformat(),
            "total_count": total_count,
            "storehouse_num": storehouse_num,
        }
        self._meta_storage.save(meta)

    # ==================== 完整库存数据 ====================

    def get_data_file(self) -> Path:
        """获取完整库存数据文件路径"""
        return _get_inventory_data_file()

    def save_full_data(self, items: List[Any]) -> None:
        """保存完整库存数据"""
        data_file = self.get_data_file()
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def get_backup_dir(self) -> Path:
        """获取备份目录"""
        return _get_backup_dir()

    # ==================== 批量更新 ====================

    def save_all(
        self,
        items: List[Any],
        category_map: Dict[str, str],
        storehouse_num: int,
    ) -> None:
        """批量保存库存数据

        Args:
            items: 完整库存数据列表
            category_map: 商品分类映射
            storehouse_num: 仓库编码
        """
        # 1. 保存商品编码列表
        item_nums = [item.get("item_num") for item in items if item.get("item_num")]
        self.save_item_nums(item_nums)

        # 2. 保存分类映射
        self.save_category_map(category_map)

        # 3. 保存元数据
        self.save_meta(len(items), storehouse_num)

        # 4. 保存完整库存数据
        data_file = self.get_data_file()
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)


# 全局实例
_inventory_storage: Optional[InventoryStorage] = None


def get_inventory_storage() -> InventoryStorage:
    """获取库存存储实例"""
    global _inventory_storage
    if _inventory_storage is None:
        _inventory_storage = InventoryStorage()
    return _inventory_storage
