# 采购订单新增

## 接口信息

| 项目 | 内容 |
|------|------|
| 接口名称 | 采购订单新增 |
| 接口方法 | nhsoft.amazon.purchase.order.save |
| 接口版本 | V1 |
| 最后更新时间 | 2026-03-03 23:30:23 |
| 请求方式 | POST |
| 接口地址 | https://cloud.nhsoft.cn/api/nhsoft.amazon.purchase.order.save |
| 接口子系统 | 乐檬零售 |

## 请求参数(POST)

| 参数名称 | 参数类型 | 必须 | 参数说明 | 长度 | 精度 | 示例值 |
|----------|----------|------|----------|------|------|--------|
| branch_num | integer | 是 | 门店编码 | | | 99 |
| storehouse_num | integer | 是 | 仓库编码 | | | 150050001 |
| supplier_num | integer | 是 | 供应商编码 | | | 203000001 |
| purchase_order_operator | string | 是 | 操作人 | | | 管理员 |
| purchase_order_memo | string | 否 | 备注 | | | 备注信息 |
| purchase_order_bill_no | string | 否 | 外部流水号(长度小于50个字符)(该字段即将废弃,后续使用新字段 purchase_order_out_bill_no) | | | A0001 |
| purchase_order_out_bill_no | string | 否 | 外部流水号(长度小于50个字符) | | | A0001 |
| purchase_order_employee | string | 否 | 业务员 | | | 业务员名称 |
| purchase_order_date | string | 是 | 采购日期 格式：yyyy-MM-dd | | | 2021-01-20 |
| purchase_order_deadline | string | 是 | 交货期限 格式：yyyy-MM-dd | | | 2021-01-20 |
| purchase_order_details | array\<object\> | 是 | 订单明细 | | | |

## 请求示例

```json
{
  "branch_num": "99",
  "storehouse_num": "150050001",
  "supplier_num": "203000001",
  "purchase_order_operator": "管理员",
  "purchase_order_memo": "备注信息",
  "purchase_order_bill_no": "A0001",
  "purchase_order_out_bill_no": "A0001",
  "purchase_order_employee": "业务员名称",
  "purchase_order_date": "2021-01-20",
  "purchase_order_deadline": "2021-01-20",
  "purchase_order_details": [
    {
      "item_num": "150050001",
      "item_use_qty": 1,
      "item_use_price": 1,
      "item_use_unit": "公斤",
      "item_present_unit": "公斤",
      "item_present_qty": 1,
      "item_memo": "备注信息",
      "item_qty": 1,
      "detail_last_price": 1.25,
      "detail_producing_date": "2024-01-01"
    }
  ],
  "request_order_fids": [
    "ul"
  ]
}
```

## 响应参数

| 参数名称 | 参数类型 | 参数说明 | 示例值 |
|----------|----------|----------|--------|
| purchase_order_fid | string | 采购订单号 | PO2030990000001 |
| branch_num | integer | 门店编码 | 99 |
| storehouse_num | integer | 仓库编码 | 150050001 |
| supplier_num | integer | 供应商编码 | 203000001 |
| purchase_order_creator | string | 创建人 | 管理员 |
| purchase_order_date | string | 采购日期 | 2021-01-20 |
| purchase_order_memo | string | 备注 | 备注信息 |
| purchase_order_bill_no | string | 外部流水号(即将废弃，使用新字段:purchase_order_out_bill_no) | A0001 |
| purchase_order_out_bill_no | string | 外部流水号 | A0001 |
| purchase_order_operator | string | 业务员 | 业务员名称 |
| purchase_order_create_time | string | 创建时间 | 2021-01-20 00:00:00 |
| purchase_order_auditor | string | 审核人 | 管理员 |
| purchase_order_audit_time | string | 审核时间 | 2021-01-20 00:00:00 |
| purchase_order_cancel_time | string | 作废时间 | 2021-01-20 00:00:00 |
| purchase_order_last_edit_time | string | 最后修改时间 | 2021-01-20 00:00:00 |
| purchase_order_deadline | string | 交货期限 | 2021-01-20 |
| purchase_order_state_code | integer | 状态代码 | 1 |
| purchase_order_state_name | string | 状态名称 | 制单 |
| purchase_order_total_money | number | 订单金额（小数点2位） | 1.0 |
| purchase_order_no_tax_money | number | 不含税金额（小数点2位） | 1.0 |
| purchase_order_label | string | 供应商平台 处理状态 | 已处理 |
| purchase_order_supplier_print_count | integer | 供应商平台 打印次数 | 0 |
| purchase_order_receive_state | string | 收货状态（未收货，部分收货，全部收货） | 全部收货 |
| purchase_order_pre_money | number | 预付金额 | 100 |
| purchase_order_details | array\<object\> | 订单明细 | |

## 响应示例

```json
{
  "purchase_order_fid": "PO2030990000001",
  "branch_num": "99",
  "storehouse_num": "150050001",
  "supplier_num": "203000001",
  "purchase_order_creator": "管理员",
  "purchase_order_date": "2021-01-20",
  "purchase_order_memo": "备注信息",
  "purchase_order_bill_no": "A0001",
  "purchase_order_out_bill_no": "A0001",
  "purchase_order_operator": "业务员名称",
  "purchase_order_create_time": "2021-01-20 00:00:00",
  "purchase_order_auditor": "管理员",
  "purchase_order_audit_time": "2021-01-20 00:00:00",
  "purchase_order_cancel_time": "2021-01-20 00:00:00",
  "purchase_order_last_edit_time": "2021-01-20 00:00:00",
  "purchase_order_deadline": "2021-01-20",
  "purchase_order_state_code": "1",
  "purchase_order_state_name": "制单",
  "purchase_order_total_money": 1,
  "purchase_order_no_tax_money": 1,
  "purchase_order_label": "已处理",
  "purchase_order_supplier_print_count": "0",
  "purchase_order_receive_state": "全部收货",
  "purchase_order_pre_money": 100,
  "purchase_order_details": [
    {
      "detail_num": "1",
      "item_num": "150050001",
      "item_use_qty": 1,
      "item_use_price": 1,
      "item_use_unit": "公斤",
      "item_name": "苹果",
      "item_use_rate": 1,
      "item_qty": 1,
      "item_unit": "公斤",
      "item_code": "10001",
      "item_spec": "1箱*10公斤",
      "item_present_unit": "公斤",
      "item_present_qty": 1,
      "detail_sub_total": 1,
      "detail_no_tax_money": 1,
      "detail_tax_money": 1,
      "detail_tax_rate": 0.03,
      "detail_send_use_qty": 1,
      "detail_producing_date": "2021-01-01",
      "item_received_qty": 10,
      "item_received_present_qty": 10,
      "detail_period": "60",
      "detail_last_price": 1.25,
      "item_memo": "备注信息",
      "detail_other_tax_rate": 0.03,
      "detail_other_tax_money": 1
    }
  ]
}
```

## 返回码

暂无数据
