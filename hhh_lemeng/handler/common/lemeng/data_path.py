"""数据文件路径管理"""
from pathlib import Path


def get_data_dir() -> Path:
    """获取数据目录路径

    基于 hhh_lemeng/handler 目录计算 data 文件夹路径：
    hhh_lemeng/handler/common/lemeng/data_path.py -> hhh_lemeng/handler/data/
    """
    return Path(__file__).parent.parent.parent.parent / "handler" / "data"


def get_inventory_data_file() -> Path:
    """库存数据文件"""
    return get_data_dir() / "inventory_data.json"


def get_inventory_nums_file() -> Path:
    """库存商品编码列表文件"""
    return get_data_dir() / "inventory_item_nums.json"


def get_inventory_category_map_file() -> Path:
    """库存商品分类映射文件"""
    return get_data_dir() / "inventory_category_map.json"


def get_inventory_meta_file() -> Path:
    """库存更新元数据文件"""
    return get_data_dir() / "inventory_meta.json"


def get_backup_dir() -> Path:
    """库存备份目录"""
    return get_data_dir() / "backup"


def get_address_db_file() -> Path:
    """地址数据库文件"""
    return get_data_dir() / "address_db.json"
