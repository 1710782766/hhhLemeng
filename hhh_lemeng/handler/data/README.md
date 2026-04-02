# 数据目录说明

此目录存放运行时生成的数据文件，**请勿提交到 Git**：

| 文件 | 大小 | 说明 |
|------|------|------|
| `inventory_data.json` | ~1.3MB | 库存数据，通过 API 获取 |
| `inventory_category_map.json` | ~74KB | 分类映射数据 |
| `inventory_item_nums.json` | ~29KB | 商品编号数据 |
| `inventory_meta.json` | ~100B | 库存元数据 |
| `address_db.json` | ~1KB | 收货地址本地数据库 |
| `nhsoft_token_cache.json` | ~500B | OAuth Token 缓存 |
| `backup/` | - | 库存历史备份目录 |

以上文件可通过服务运行时重新获取，无需提交。

## 存储抽象

所有数据读写通过 `InventoryStorage` 和 `AddressDB` 统一管理（详见 `handler/common/lemeng/`）。

将来迁移到数据库时，只需修改存储实现，业务代码无需改动。
