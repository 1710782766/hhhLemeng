# 客户地址列表查询

## 接口信息

| 项目 | 内容 |
|------|------|
| 接口名称 | 客户地址列表查询 |
| 接口方法 | nhsoft.amazon.basic.client.address.read |
| 接口版本 | V1 |
| 请求方式 | GET |
| 接口子系统 | 乐檬零售 |

## 请求参数(GET)

| 参数名称 | 参数类型 | 必须 | 参数说明 |
|----------|----------|------|----------|
| client_fid | string | 是 | 客户主键（合作伙伴ID）二选一 |

## 响应参数

| 参数名称 | 参数类型 | 参数说明 | 示例值 |
|----------|----------|----------|--------|
| id | string | 地址ID | |
| client_id | string | 客户ID | |
| contact_name | string | 联系人姓名 | |
| contact_phone | string | 联系人电话 | |
| province | string | 省份 | |
| city | string | 城市 | |
| area | string | 区县 | |
| address_detail | string | 详细地址 | |
| default_address | boolean | 是否默认地址 | true/false |
| address_id | string | 地址编码 | |
| default_create_flag | boolean | 默认创建标识 | true/false |

## 响应示例

```json
{
  "id": "",
  "client_id": "",
  "contact_name": "",
  "contact_phone": "",
  "province": "",
  "city": "",
  "area": "",
  "address_detail": "",
  "default_address": true,
  "address_id": "",
  "default_create_flag": true
}
```

## 返回码

暂无数据
