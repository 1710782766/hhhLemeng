# 乐檬 (Lemeng) 项目指南

本仓库包含两个协作项目，用于对接乐檬开放平台 API。

## 项目概述

| 子项目               | 路径                             | 职责                                           |
| -------------------- | -------------------------------- | ---------------------------------------------- |
| **文档爬虫**   | 根目录（`main.py`、`docs/`） | 爬取乐檬开放平台 API 文档，为开发提供参考      |
| **hhh_lemeng** | `hhh_lemeng/`                  | 乐檬开放平台 API 集成服务（Tornado，生产代码） |

**业务定位**：本系统作为分销平台中间层，对接乐檬供应商系统，核心业务流程为：

```
供应商（乐檬平台）↔ API ↔ hhh_lemeng（中间层服务）↔ 我们的 App ↔ 终端用户
```

## 技术栈

- **Python**: 3.12+
- **依赖管理**: `uv`（现代 Python 包管理器）
- **Web 框架**: Tornado 6.5.4（异步 Web 框架）
- **浏览器自动化**: Playwright 1.58.0（用于文档爬虫）
- **认证方式**: OAuth2 Bearer Token（自动缓存 + 刷新）

## 项目进度

### 已封装 API 接口（20个）

| 分类 | 数量 | 接口列表 |
|------|------|----------|
| 供应链-批发 | 3 | `wholesale_book_find` / `save` / `saveandaudit` |
| 供应链-采购 | 4 | `purchase_order_find` / `save` / `saveandaudit` / `read` |
| 门店 | 1 | `branch_list` |
| 仓库 | 1 | `basic_storehouse_find` |
| 供应商档案 | 2 | `basic_supplier_find` / `read` |
| 商品档案 | 5 | `basic_item_find` / `read` / `itemcategory_find` / `department_find` / `itemimage_find` |
| 客户档案 | 4 | `basic_client_find` / `category_find` / `save` / `update` |

### 已保存接口详情文档

| 分类 | 文档路径 |
|------|----------|
| 供应链-采购 | `docs/供应链/采购详情/` (3个) |
| 供应商档案 | `docs/档案/供应商详情/` (2个) |

### 待完成接口（参考 `docs/` 目录）

- [ ] 供应链-采购：收货单、退货单、供货关系等
- [ ] 供应链-批发：查询接口已封装，其他状态管理接口
- [ ] 档案：供应商新增/修改/删除
- [ ] 零售、会员、结算、WMS 等大类

## 项目结构

```
lemeng/
├── pyproject.toml          # 项目配置和依赖
├── uv.lock                 # uv 锁定文件
├── .python-version         # Python 版本指定 (3.12)
├── .gitignore              # Git 忽略配置
├── README.md               # 项目说明（当前为空）
├── CLAUDE.md               # 详细的业务和技术文档
├── AGENTS.md               # 本文件
│
├── main.py                 # 文档爬虫主程序（Playwright）
├── debug.py                # 爬虫调试脚本（可视化调试）
├── docs/                   # 爬取的 API 文档（Markdown）
│   ├── README.md           # 文档索引
│   ├── _nav.json           # 导航结构
│   ├── 通用/、档案/、零售/、会员/
│   ├── 供应链/、结算/、WMS/
│   ├── 基础服务/、用户中心/
│   └── ...
│
└── hhh_lemeng/             # 生产服务代码
    ├── server.py           # Tornado 服务入口（端口 8167）
    ├── app.py              # 本地测试脚本
    ├── logging.log         # 日志文件
    ├── nhsoft_token_cache.json   # OAuth Token 缓存（敏感，勿提交）
    │
    └── handler/
        ├── hhhLemeng.py           # OAuth 授权码回调处理器
        ├── service/
        │   └── hhhLemengService.py    # 核心：所有 API 调用封装
        └── common/lemeng/
            ├── token.py           # Token 生命周期管理（含并发锁）
            ├── encryption.py      # Base64 + XOR 加解密
            ├── error.py           # LemRequestError 业务异常
            ├── pringLog.py        # 日志配置
            └── utils.py           # BaseHandler、error_handler 装饰器
```

## 构建与运行

### 环境准备

本项目使用 `uv` 作为包管理器。确保已安装 `uv`：

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装依赖

```bash
uv sync
```

### 运行文档爬虫

```bash
# 爬取所有 API 文档到 docs/ 目录
uv run main.py
```

### 运行生产服务

```bash
# 开发环境（单进程）
uv run python -m hhh_lemeng.server

# 或指定端口
uv run python -m hhh_lemeng.server --port=8167

# 调试
uv run python -m hhh_lemeng.app
```

服务将在 `http://0.0.0.0:8167` 启动。

### 环境变量

| 变量        | 说明     | 默认值  |
| ----------- | -------- | ------- |
| `APP_ENV` | 运行环境 | `dev` |

环境配置：

- `dev`: 开发环境，单进程，详细日志输出到文件
- `prod`: 生产环境，多进程，最小化日志输出到 stdout

## 开发规范

### 代码组织

1. **只修改 `hhh_lemeng/` 目录内的文件** - 根目录文件为文档爬虫，生产代码在 `hhh_lemeng/`
2. **所有 IO 操作使用 `async/await`** - 保持 Tornado 异步风格
3. **业务错误处理** - 使用 `LemRequestError`，通过 `@error_handler` 装饰器统一处理
4. **日志记录** - 使用 `pringLog.get_log()` 获取 logger，避免直接使用 `print`

### 敏感文件

- `hhh_lemeng/nhsoft_token_cache.json` - OAuth Token 缓存文件，**已配置在 .gitignore 中，请勿提交**

### API 方法命名规范

API 方法统一封装在 `HhhLemengService` 类中，命名规则：

```python
# 将 API 方法名中的点替换为下划线
nhsoft.amazon.basic.item.find -> nhsoft_amazon_basic_item_find
```

### 已封装的 API 方法

| 分类        | 方法名                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------- |
| 供应链-批发 | `wholesale_book_find` / `save` / `saveandaudit`                                             |
| 供应链-采购 | `purchase_order_find` / `save` / `saveandaudit` / `read`                                    |
| 门店        | `branch_list`                                                                                   |
| 仓库        | `basic_storehouse_find`                                                                         |
| 商品档案    | `basic_item_find` / `read` / `itemcategory_find` / `department_find` / `itemimage_find` |
| 供应商档案  | `basic_supplier_find` / `read`                                                            |
| 客户档案    | `basic_client_find` / `save` / `update` / `category_find`                                 |

## 认证流程

1. **首次授权**: 访问授权 URL 获取 code

   ```
   https://cloud.nhsoft.cn/authserver/oauth/authorize?
     response_type=code&state=1&client_id={appid}&redirect_uri={redirect_uri}
   ```
2. **回调处理**: code 通过 `/api/lmOauthCodeCallback` 回调接口处理
3. **Token 管理**:

   - 自动缓存到 `nhsoft_token_cache.json`
   - 自动刷新（提前 120 秒过期）
   - 并发保护（同一时间只有一个协程刷新）

## 开发环境配置（dev）

```
Host:        https://cloud.nhsoft.cn
AppID:       93ec09e991d6469288c5fe38fe91c927
Port:        8167
RedirectURI: http://127.0.0.1:8167/api/lmOauthCodeCallback
```

## 已知注意事项

### 批发订单相关

- `wholesale_book_deadline` 传入的日期会被服务端强制覆盖为创建日期 +7 天，无法自定义
- `wholesale_book_out_bill_no`（外部流水号）在 `saveandaudit` 中默认用 `get_oid("EX")` 自动生成，**不要传空字符串**，否则第三方管理系统无法关联订单
- 通过 API 查询到的订单不代表第三方管理系统可见——未审核（`state_code=1`）和已过期订单在管理端默认不展示
- `wholesale_book_find` 时间间隔不能超过 5 天

## 文档爬虫说明

### 使用场景

为 `hhh_lemeng` 新增接口时，按需爬取该接口详情页获取参数文档：

```
接口详情页 URL：
https://console.nhsoft.cn/documents/api-doc/{group_id}/{category_id}/{method_name}

示例：
/documents/api-doc/1/2/nhsoft.amazon.basic.item.find
```

### 网站结构

网站基于 Umi 3.5 SPA 架构：

- **第一层**: 导航菜单分组（档案、零售、会员、供应链…）
- **第二层**: 分类页面（API 列表，共 53 个分类）
- **第三层**: 接口详情页（参数表、请求/响应示例、返回码）

### 关键 CSS 选择器

| 用途       | 选择器                                               |
| ---------- | ---------------------------------------------------- |
| 根菜单     | `.ant-menu.ant-menu-root`                          |
| 主内容区   | `[class*="content-wrapper"]`（CSS Modules 哈希类） |
| 分类列表项 | `li.ant-list-item`                                 |

### 爬虫注意事项

- 展开子菜单需等待动画完成（`wait_for_timeout(1500)`）
- 菜单获取必须用 `:scope > children`，否则产生重复条目
- `page.evaluate()` 中含正则 `\n` 时，Python 字符串用 `r"""..."""` 原始字符串

### 接口详情文档存储规范

爬取的接口详情需要保存到 `docs/` 目录，避免重复爬取：

```
docs/
├── README.md                    # 文档索引（接口列表）
├── 供应链/
│   ├── 采购.md                  # 接口列表（方法名汇总）
│   └── 采购详情/                # 接口详情目录
│       ├── nhsoft.amazon.purchase.order.find.md
│       ├── nhsoft.amazon.purchase.order.save.md
│       └── nhsoft.amazon.purchase.order.saveandaudit.md
└── ...
```

**存储规则**：
1. **接口列表**保持原有结构，存储在 `{分类}.md` 中（如 `采购.md`）
2. **接口详情**存储在 `{分类}详情/` 子目录中，文件名格式：`{method_name}.md`
3. 已爬取的接口详情**无需重复爬取**，直接从本地读取
4. 详情文档格式：包含接口信息、请求参数、请求示例、响应参数、响应示例、返回码

## 本地测试

使用 `hhh_lemeng/app.py` 进行本地 API 测试：

```python
# 示例：查询批发订单
result, _ = await lemengService.nhsoft_amazon_wholesale_book_find(
    client_fid="0026403010000001"
)
print(result)
```

运行测试：

```bash
uv run python -m hhh_lemeng.app
```

## 调试工具

### 爬虫调试

```bash
# 可视化调试爬虫（会打开浏览器窗口）
uv run python debug.py
```

### 日志查看

```bash
# 开发环境日志
tail -f hhh_lemeng/logging.log
```
