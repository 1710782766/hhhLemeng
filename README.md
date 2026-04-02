# hhhLemeng

对接乐檬开放平台的中间层服务，基于 Tornado 异步框架。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动服务（端口8167）
cd hhh_lemeng && uv run python server.py

# 爬取API文档
uv run main.py
```

## 项目结构

- `hhh_lemeng/` - 生产服务（Tornado）
- `docs/` - API 文档
- `main.py` / `fetch_api_detail.py` - 文档爬虫

## 存储层设计（可移植性）

项目采用存储抽象层设计，数据读写统一通过接口完成，便于将来从本地文件迁移到数据库。

### 架构

```
业务代码（AddressDB / InventoryStorage / TokenManager）
    ↓ 调用
存储接口（Storage.load() / Storage.save()）
    ↓ 实现
文件存储（FileStorage） ← 当前使用
数据库存储（DatabaseStorage） ← 将来迁移
```

### 当前存储

| 存储名称 | 用途 | 数据文件 |
|---------|------|---------|
| `address_db` | 收货地址 | `handler/data/address_db.json` |
| `token_cache` | OAuth Token | `handler/data/nhsoft_token_cache.json` |
| `inventory` | 库存数据 | `handler/data/inventory_*.json` |

### 迁移到数据库

只需修改 `hhh_lemeng/handler/common/lemeng/data_path.py` 中的注册逻辑，业务代码无需改动。

示例：将 `address_db` 从文件切换到数据库

```python
# 1. 实现 DatabaseStorage 类
class DatabaseStorage(Storage):
    def __init__(self, db_pool, table_name):
        self.db_pool = db_pool
        self.table_name = table_name

    def load(self) -> Dict:
        # 从数据库查询
        pass

    def save(self, data: Dict) -> None:
        # 写入数据库
        pass

    def exists(self) -> bool:
        pass

# 2. 修改注册（data_path.py）
def _init_default_storages():
    db_pool = create_pool("postgres://...")  # 初始化连接池
    register_storage("address_db", lambda: DatabaseStorage(db_pool, "address_db"))
    # 其他存储...
```

完成以上两步后，`AddressDB` 等业务类会自动使用数据库，无需修改任何业务逻辑。
