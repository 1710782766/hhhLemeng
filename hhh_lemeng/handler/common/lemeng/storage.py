"""
存储抽象层

定义统一的存储接口，便于将来从本地文件迁移到数据库/RADIUS。
目前提供 FileStorage 本地文件实现。
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class Storage(ABC):
    """存储接口抽象基类"""

    @abstractmethod
    def load(self) -> Any:
        """加载数据"""
        pass

    @abstractmethod
    def save(self, data: Any) -> None:
        """保存数据"""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """检查存储是否存在"""
        pass


class FileStorage(Storage):
    """本地文件存储实现"""

    def __init__(
        self,
        file_path: Path,
        default_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            file_path: 文件路径
            default_data: 不存在时返回的默认数据
        """
        self.file_path = file_path
        self.default_data = default_data if default_data is not None else {}

    def exists(self) -> bool:
        return self.file_path.exists()

    def load(self) -> Any:
        """加载 JSON 文件数据"""
        if not self.exists():
            return self.default_data.copy()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            return self.default_data.copy()

    def save(self, data: Dict[str, Any]) -> None:
        """保存数据到 JSON 文件"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


class JSONFileStorage(FileStorage):
    """JSON 文件存储（与 FileStorage 功能相同，保留兼容性）"""

    pass


# # 数据库存储实现示例（未完成，需根据实际数据库设计实现）
# from typing import Any, Dict
# from .storage import Storage


# class DatabaseStorage(Storage):
#     """数据库存储实现（示例）"""

#     def __init__(self, db_pool, table_name: str):
#         self.db_pool = db_pool
#         self.table_name = table_name

#     async def load(self) -> Dict[str, Any]:
#         """从数据库加载"""
#         # TODO: 实现数据库查询
#         data = await self.db_pool.fetchrow(
#             f"SELECT data FROM {self.table_name} WHERE id = 1"
#         )
#         return json.loads(data["data"]) if data else {}

#     async def save(self, data: Dict[str, Any]) -> None:
#         """保存到数据库"""
#         # TODO: 实现数据库写入
#         await self.db_pool.execute(
#             f"INSERT INTO {self.table_name} (id, data) VALUES (1, $1) "
#             f"ON CONFLICT (id) DO UPDATE SET data = $1",
#             json.dumps(data),
#         )

#     def exists(self) -> bool:
#         # TODO: 检查记录是否存在
#         pass
