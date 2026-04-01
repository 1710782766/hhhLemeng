# 乐檬项目

## 语言

默认全部为中文，包括思考内容和总结内容

## 项目概述

本仓库包含两个协作项目：

| 子项目               | 路径                             | 职责                                              |
| -------------------- | -------------------------------- | ------------------------------------------------- |
| **文档爬虫**   | 根目录（`main.py`、`docs/`） | 爬取乐檬开放平台 API 文档，为 hhh_lemeng 提供参考 |
| **hhh_lemeng** | `hhh_lemeng/`                  | 乐檬开放平台 API 集成服务（Tornado，生产代码）    |

**爬虫的核心价值**：在为 `hhh_lemeng` 新增接口时，按需爬取对应接口的详情页（参数表、请求/响应示例、返回码），作为开发依据。

---

## 业务背景与目标

我们的 App 扮演**分销平台**角色，对接乐檬供应商，核心业务流程：

```
供应商（乐檬平台）
  ↕ API
hhh_lemeng（中间层服务）
  ↕
我们的 App
  ↕
终端用户
```

### 已完成

- 商品展示：分类列表、商品列表、商品详情
- **下单流程（2026-03-24 完成）**：
  - 创建批发订单接口（`wholesaleOrderCreate.do`）
  - 查询批发订单列表（`wholesaleOrderFind.do`）
  - 查询订单详情（`wholesaleOrderDetail.do`）
  - 商品分类查询（`shopCategoryFind.do`）
- 批发下单目前以和供应商调通可以正常查询到订单

### 待解决

- ~~供应商查不到订单问题~~
- ~~下单收货地址问题~~ → 2026-03-27 已完成，采用最简方案，每个地址对应一个乐檬客户

---

## hhh_lemeng（生产服务）

### 技术栈

- **框架**：Tornado（异步 Web 框架）
- **语言**：Python 3.12，`async/await` 异步模式
- **认证**：OAuth2 Bearer Token（自动缓存 + 刷新）
- **端口**：8167

### 目录结构

```
hhh_lemeng/
├── server.py                          # Tornado 服务入口，监听 8167 端口
├── app.py                             # 本地测试脚本
├── nhsoft_token_cache.json            # OAuth2 Token 缓存（敏感，勿提交）
├── logging.log                        # 日志文件
└── handler/
    ├── hhhLemeng.py                   # OAuth 授权码回调处理器 + HTTP接口
    ├── service/
    │   └── hhhLemengService.py        # 核心：所有 API 调用封装
    └── common/lemeng/
        ├── config.py                  # 固定配置（门店、仓库、客户等常量）
        ├── token.py                   # Token 生命周期管理（含并发锁）
        ├── encryption.py              # Base64 + XOR 加解密
        ├── error.py                   # LemRequestError 业务异常
        ├── pringLog.py                # 日志配置
        ├── utils.py                   # BaseHandler、error_handler 装饰器
        └── address_db.py              # 收货地址本地数据库（2026-03-27新增）
```

### 已封装的 API 方法（共 22 个）

| 分类        | 方法名                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------- |
| 供应链-批发 | `wholesale_book_find` / `read` / `save` / `saveandaudit`                                  |
| 供应链-采购 | `purchase_order_find` / `save` / `saveandaudit` / `read`                                  |
| 门店        | `branch_list`                                                                                   |
| 仓库        | `basic_storehouse_find`                                                                         |
| 商品档案    | `basic_item_find` / `read` / `itemcategory_find` / `department_find` / `itemimage_find` |
| 供应商档案  | `basic_supplier_find` / `read`                                                                |
| 客户档案    | `basic_client_find` / `save` / `update` / `category_find` / `address_read`              |

### HTTP 接口清单（前端调用）

| 接口路径                              | 功能             | 调用 Service 方法               |
| ------------------------------------- | ---------------- | ------------------------------- |
| `POST /api/shopItemFind.do`         | 商品列表查询     | `basic_item_find`             |
| `POST /api/shopCategoryFind.do`     | 商品分类查询     | `itemcategory_find`           |
| `POST /api/shopItemDetail.do`       | 商品详情         | `basic_item_read`             |
| `POST /api/wholesaleOrderCreate.do` | 创建批发订单     | `wholesale_book_save`         |
| `POST /api/wholesaleOrderFind.do`   | 查询批发订单列表 | `wholesale_book_find`         |
| `POST /api/wholesaleOrderDetail.do` | 查询订单详情     | `wholesale_book_read`         |
| `POST /api/clientAddressList.do`    | 查询客户地址列表 | `basic_client_address_read`   |
| `POST /api/addressList.do`          | 查询收货地址列表 | 本地数据库                    |
| `POST /api/addressCreate.do`        | 新增收货地址     | `basic_client_save`           |

**接口文档**：详见 [docs/前端接口文档.md](docs/前端接口文档.md)

### 环境配置（dev）

```
Host:        https://cloud.nhsoft.cn
AppID:       93ec09e991d6469288c5fe38fe91c927
Port:        8167
RedirectURI: http://127.0.0.1:8167/api/lmOauthCodeCallback
```

### 开发规范

- **只改 `hhh_lemeng/` 目录内的文件**
- 所有 IO 操作使用 `async/await`，保持 Tornado 异步风格
- 业务错误用 `LemRequestError`，通过 `@error_handler` 装饰器统一处理
- 日志用 `pringLog.get_log()` 获取 logger，不用 `print`
- `nhsoft_token_cache.json` 为敏感文件，不提交 git

### 固定配置

业务常量统一维护在 [`handler/common/lemeng/config.py`](hhh_lemeng/handler/common/lemeng/config.py)：

| 配置项   | 常量名             | 值                   | 说明       |
| -------- | ------------------ | -------------------- | ---------- |
| 门店编码 | `BRANCH_NUM`     | `99`               | 固定门店   |
| 仓库编码 | `STOREHOUSE_NUM` | `264030025`        | 固定仓库   |
| 客户编码 | `CLIENT_FID`     | `0026403010000001` | 好惠花客户 |
| 操作员   | `OPERATOR`       | `好惠花1`          | 订单操作员 |

**使用方式**：

```python
from hhh_lemeng.handler.common.lemeng.config import BRANCH_NUM, CLIENT_FID
```

### 响应格式规范

`BaseHandler.response_success(data, ls, msg)` 参数约定：

- **单条数据**（如商品详情、订单详情、创建订单结果）：放入 `data` 参数 → 前端从 `result.data` 获取
- **列表数据**（如商品列表、分类列表、订单列表）：放入 `ls` 参数 → 前端从 `result.list` 获取

**当前接口数据放置**：

| 接口                     | 数据位置        | 类型                       |
| ------------------------ | --------------- | -------------------------- |
| `shopItemFind`         | `result.list` | 商品数组（纯数组，无分页） |
| `shopCategoryFind`     | `result.list` | 分类数组（纯数组）         |
| `shopItemDetail`       | `result.data` | 商品详情对象               |
| `wholesaleOrderCreate` | `result.data` | 创建结果对象               |
| `wholesaleOrderFind`   | `result.list` | 订单数组（纯数组，无分页） |
| `wholesaleOrderDetail` | `result.data` | 订单详情对象               |
| `clientAddressList`    | `result.list` | 地址数组                   |

示例：

```python
# 单条数据
await self.response_success(result, [], "获取成功")

# 列表数据
await self.response_success({}, result, "获取成功")
```

### 已知注意事项

- `wholesale_book_deadline` 传入的日期会被服务端强制覆盖为创建日期 +7 天，无法自定义
- `wholesale_book_out_bill_no`（外部流水号）在 `saveandaudit` 中默认用 `get_oid("EX")` 自动生成，**不要传空字符串**，否则第三方管理系统无法关联订单
- 通过 API 查询到的订单不代表第三方管理系统可见——未审核（`state_code=1`）和已过期订单在管理端默认不展示
- `wholesale_book_find` 时间间隔不能超过 5 天

---

## 文档爬虫

### 技术栈

- **Python 3.12**，通过 `uv` 管理（`uv run main.py`，不用全局 python3）
- **Playwright**（`playwright>=1.58.0`）：SPA 页面渲染

### 使用场景

为 `hhh_lemeng` 新增接口时，按需爬取该接口详情页获取参数文档：

```
接口详情页 URL：
https://console.nhsoft.cn/documents/api-doc/{group_id}/{category_id}/{method_name}

示例：
/documents/api-doc/1/2/nhsoft.amazon.basic.item.find
```

### 账号（如果需要的话）

账号：haohuihua0220@163.com

密码：!PSWqaz147369

### 网站结构（Umi 3.5 SPA）

| 层级   | 说明                                        |
| ------ | ------------------------------------------- |
| 第一层 | 导航菜单分组（档案、零售、会员、供应链…）  |
| 第二层 | 分类页面（API 列表，共 53 个分类）          |
| 第三层 | 接口详情页（参数表、请求/响应示例、返回码） |

### 关键 CSS 选择器

| 用途       | 选择器                                               |
| ---------- | ---------------------------------------------------- |
| 根菜单     | `.ant-menu.ant-menu-root`                          |
| 主内容区   | `[class*="content-wrapper"]`（CSS Modules 哈希类） |
| 分类列表项 | `li.ant-list-item`                                 |

### 已完成工作

- [X] 两层爬虫 `main.py`，爬取 53 个分类文档到 `docs/`
- [X] 接口详情文档存储规范：保存在 `{分类}详情/` 子目录
- [X] 已保存接口详情：
  - 供应链/采购详情：3 个（find, save, saveandaudit）
  - 档案/供应商详情：2 个（find, read）

### 文档输出结构

```
docs/
├── README.md、_nav.json
├── 通用/全局说明.md
├── 档案/（14 个）、零售/（5 个）、会员/（7 个）
├── 供应链/（6 个）、结算/（6 个）、WMS/（8 个）
├── 基础服务/（3 个）、用户中心/（3 个）
└── 档案/供应商详情/          # 接口详情示例
    ├── nhsoft.amazon.basic.supplier.find.md
    └── nhsoft.amazon.basic.supplier.read.md
```

### 爬虫注意事项

- 展开子菜单需等待动画完成（`wait_for_timeout(1500)`）
- 菜单获取必须用 `:scope > children`，否则产生重复条目
- `page.evaluate()` 中含正则 `\n` 时，Python 字符串用 `r"""..."""` 原始字符串

---

## 收货地址模块（2026-03-27）

### 背景

解决用户下单时收货地址无法自定义的问题。经与乐檬沟通，采用最简方案：
- 下单时只传基础参数，不传配送地址相关参数
- 使用客户创建时设置的 `client_addr` 和 `client_ship_addr` 作为默认地址
- 每个收货地址对应乐檬系统中的一个客户

### 核心设计

**数据映射关系**：
```
我们的系统                    乐檬系统
-----------                   ---------
收货地址(id)      <--->      客户(client_fid)
  ├── 收货人姓名              ├── client_name/client_linkman
  ├── 电话                    ├── client_mobile/client_phone
  └── 省/市/区/详细地址        ├── client_addr/client_ship_addr
```

**地址ID生成规则**：
- 格式：`{uid}{序号}`，如 `3901383351133131`
- 序号从1开始自增
- 与 `client_code` 共用同一序号

### 新增文件

1. **`hhh_lemeng/handler/common/lemeng/address_db.py`**
   - 地址数据库操作类
   - 本地 JSON 存储映射关系
   - 方法：`add_address()`, `get_addresses_by_uid()`, `get_address_by_id()`

2. **`hhh_lemeng/data/address_db.json`**（运行时自动创建）
   - 本地地址数据存储
   - 结构：`{addresses: [], uid_sequence: {}}`

### 新增接口

| 接口路径 | 功能 | 关键参数 |
|---------|------|---------|
| `POST /api/addressList.do` | 获取用户地址列表 | 需传 `uid` 请求头 |
| `POST /api/addressCreate.do` | 新增收货地址 | 需传 `uid` 请求头，参数：name, phone, province, city, district, detail |

### 修改接口

**`POST /api/wholesaleOrderCreate.do`**
- 新增可选参数 `address_id`
- 不传时使用默认 `CLIENT_FID`
- 传入时查询本地数据库获取对应 `client_fid` 和 `client_name`
- 使用 `nhsoft_amazon_wholesale_book_save` 创建订单（最简参数）

### 客户创建参数

创建新客户时使用的固定参数（通过 `nhsoft_amazon_basic_client_save`）：

```python
{
    "branch_num": "99",
    "client_name": f"好惠花-{name}",
    "client_code": client_code,           # uid + 序号
    "client_mobile": phone,
    "client_type": "好惠花",
    "client_settlement_type": "临时指定",
    "client_settle_day_of_month": "11",
    "client_settle_period": "30",
    "client_settlement_model": "所属门店结算",
    "client_credit_enable": 1,
    "client_credit_limit": 10000,
    "wholesale_book_balance_enough_enable": 0,
    "client_usual_discount": 0.9,
    "client_price_level": "1",
    "client_wholesale_discount": 0.9,
    "client_wholesale_level": "1",
    "client_actived": 1,
    "client_shared": 1,
    "client_level_name": "好惠花",
    "client_addr": full_address,
    "client_ship_addr": full_address,
    "client_linkman": name,
    "client_phone": phone
}
```

### 验证记录

测试时间：2026-03-27

| 测试项 | 结果 |
|-------|------|
| 创建地址 `3901383351133131` | ✅ 成功，乐檬客户FID `0026403990003943` |
| 地址列表查询 | ✅ 返回正确地址信息 |
| 使用新地址创建订单 | ✅ 订单 `WB26403990004420`，`client_address` 正确 |
| 不传地址使用默认 | ✅ 订单 `WB26403990004421`，使用默认客户 |

### 接口调用示例

**创建地址**：
```bash
curl -X POST http://127.0.0.1:8167/api/addressCreate.do \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "uid: 390138335113313" \
  --data-urlencode 'paras={"name":"张三","phone":"18331511901","province":"湖南省","city":"长沙市","district":"天心区","detail":"测试地址123号"}'
```

**创建订单（指定地址）**：
```bash
curl -X POST http://127.0.0.1:8167/api/wholesaleOrderCreate.do \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'paras={"items":[{"item_num":20421,"item_count":1,"item_unit":"件"}],"address_id":"3901383351133131"}'
```
