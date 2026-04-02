"""数据文件路径管理"""

from pathlib import Path
from typing import Dict, Callable

from .storage import FileStorage, Storage


# 数据目录
def get_data_dir() -> Path:
    """获取数据目录路径

    基于 hhh_lemeng/handler 目录计算 data 文件夹路径：
    hhh_lemeng/handler/common/lemeng/data_path.py -> hhh_lemeng/handler/data/
    """
    return Path(__file__).parent.parent.parent.parent / "handler" / "data"


# ==================== 文件路径定义 ====================


def get_address_db_file() -> Path:
    """地址数据库文件"""
    return get_data_dir() / "address_db.json"


def get_token_cache_file() -> Path:
    """Token 缓存文件"""
    return get_data_dir() / "nhsoft_token_cache.json"


# ==================== 库存相关（预留） ====================


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


# ==================== 统一存储获取 ====================

# 存储类型注册表
_STORAGE_REGISTRY: Dict[str, Callable[[], Storage]] = {}


def register_storage(name: str, factory: Callable[[], Storage]) -> None:
    """注册存储实例工厂函数

    Args:
        name: 存储名称，如 "address_db", "token_cache"
        factory: 返回 Storage 实例的工厂函数
    """
    _STORAGE_REGISTRY[name] = factory


def get_storage(name: str) -> Storage:
    """获取已注册的存储实例

    Args:
        name: 存储名称

    Returns:
        Storage 实例

    Raises:
        KeyError: 如果存储名称未注册
    """
    if name not in _STORAGE_REGISTRY:
        raise KeyError(
            f"Storage '{name}' not registered. Available: {list(_STORAGE_REGISTRY.keys())}"
        )
    return _STORAGE_REGISTRY[name]()


def _init_default_storages() -> None:
    """初始化默认存储实例（本地文件存储）"""
    # 地址数据库
    register_storage("address_db", lambda: FileStorage(get_address_db_file()))

    # Token 缓存
    register_storage("token_cache", lambda: FileStorage(get_token_cache_file()))

    # 库存数据存储（延迟导入避免循环依赖，放在 get_storage("inventory") 时导入）

    # 之后（使用 DatabaseStorage）


# 数据库存储实现示例（未完成，需根据实际数据库设计实现）
# def _init_default_storages() -> None:
#     # 需要先初始化数据库连接池
#     from some_db_library import create_pool
#     db_pool = create_pool("postgres://user:pass@localhost/dbname")

#     register_storage("address_db", lambda: DatabaseStorage(db_pool, "address_db"))
#     register_storage("token_cache", lambda: DatabaseStorage(db_pool, "token_cache"))


# 启动时自动初始化
_init_default_storages()
