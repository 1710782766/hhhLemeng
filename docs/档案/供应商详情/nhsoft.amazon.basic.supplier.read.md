# 供应商读取

## 接口信息

| 项目 | 内容 |
|------|------|
| 接口名称 | 供应商读取 |
| 接口方法 | nhsoft.amazon.basic.supplier.read |
| 接口版本 | V1 |
| 最后更新时间 | 2026-03-03 23:30:24 |
| 请求方式 | GET |
| 接口地址 | https://cloud.nhsoft.cn/api/nhsoft.amazon.basic.supplier.read |
| 接口子系统 | 乐檬零售 |

## 请求参数(GET)

| 参数名称 | 参数类型 | 必须 | 参数说明 | 长度 | 精度 | 示例值 |
|----------|----------|------|----------|------|------|--------|
| supplier_num | integer | 否 | 供应商编码（合作伙伴ID二选一） | | | 43440001 |
| user_center_partner_id | integer | 否 | 合作伙伴ID（供应商编码二选一） | | | 129 |

## 响应参数

| 参数名称 | 参数类型 | 参数说明 | 示例值 |
|----------|----------|----------|--------|
| supplier_num | integer | **供应商编码** | 99 |
| supplier_code | string | 供应商代码 | SP012 |
| supplier_name | string | 供应商名称 | 乐檬连营 |
| branch_num | integer | 所属门店编码 | 99 |
| supplier_pin | string | 速记码 | LMLY |
| supplier_kind | string | 供应商类型 | 默认供应商类别 |
| supplier_tax_no | string | 税务号 | 123123453145678 |
| supplier_tax | number | 进项税率 | 0.13 |
| supplier_taxpayer_type | string | 纳税人类型 | 小规模纳税人 |
| supplier_linkman | string | 联系人 | 乐檬 |
| supplier_linktel | string | 联系人电话 | 18899288103 |
| supplier_phone | string | 电话号码 | 18888888981 |
| supplier_fax | string | 传真 | 234251213 |
| supplier_postcode | string | 邮编 | 100000 |
| supplier_email | string | 电子邮箱 | 123456@qq.com |
| supplier_addr | string | 地址 | 南京市建邺区 |
| supplier_settlement_type | string | 结算方式 | 临时指定 |
| supplier_settle_day_of_month | integer | 月结日期 | 10 |
| supplier_settle_period | integer | 结转周期 | 30 |
| supplier_method | string | 经营方式（购销/联营） | 购销 |
| supplier_settlement_model | string | 结算模式 | 所属门店结算 |
| supplier_purchase_period | integer | 采购周期 | 30 |
| supplier_purchase_period_days | string | 采购周期 多个用逗号分隔(仅当周期为按周时生效) | 1 |
| supplier_purchase_period_unit | string | 采购周期（天，周，月，按周） | 天 |
| supplier_purchase_date | string | 首次/上次采购时间 | 2021-01-01 |
| supplier_purchase_deadline | integer | 交货期限 | |
| supplier_shared | integer | 是否共享（1共享，0不共享） | 1 |
| supplier_actived | integer | 是否启用（1启用，0不启用） | 1 |
| supplier_last_edit_time | string | 最后修改时间 | 2021-09-01 10:00:00 |
| user_center_partner_id | integer | 用户中心PartnerId | 1 |
| supplier_site | string | 网址 | www.baidu.com |
| return_order_confirm_flag | integer | 退货单需确认后才允许审核（1启用，0不启用） | 1 |
| supplier_memo | string | 备注 | 测试备注 |
| supplier_min_order_money | number | 起订金额 | 2.25 |
| supplier_shared_branches | array<object> | 供应商共享门店信息 | |
| supplier_share_regions | array<object> | 供应商共享区域信息 | |
| supplier_account_details | array<object> | 银行账号列表 | |
| supplier_extend1 | string | 扩展属性1 | value |
| supplier_extend2 | string | 扩展属性2 | value |
| supplier_extend3 | string | 扩展属性3 | value |
| supplier_extend4 | string | 扩展属性4 | value |
| supplier_extend5 | string | 扩展属性5 | value |
| supplier_extend6 | string | 扩展属性6 | value |
| supplier_extend7 | string | 扩展属性7 | value |
| supplier_extend8 | string | 扩展属性8 | value |
| supplier_extend9 | string | 扩展属性9 | value |
| supplier_extend10 | string | 扩展属性10 | value |
| supplier_min_money_type | integer | 起订金额校验类型；0禁止，1提醒 | 0 |
| supplier_recon_base | string | 对账基数(月结\|半月结\|自定义) | 自定义 |
| supplier_recon_day | integer | 对账天数 | 10 |
| supplier_recon | boolean | 启用对账 | true |
| supplier_rolling_order | boolean | 是否启用滚单结算 | true |
| supplier_carriage | number | 运费金额 | 10.0 |
| item_no_push_finance | boolean | 商品不推送到资金系统(调出单/调入单) | false |
| supplier_only_ln_item | boolean | 仅支持添加批次商品 | true |

## 响应示例

```json
{
  "supplier_num": "99",
  "supplier_code": "SP012",
  "supplier_name": "乐檬连营",
  "branch_num": "99",
  "supplier_pin": "LMLY",
  "supplier_kind": "默认供应商类别",
  "supplier_tax_no": "123123453145678",
  "supplier_tax": 0.13,
  "supplier_taxpayer_type": "小规模纳税人",
  "supplier_linkman": "乐檬",
  "supplier_linktel": "18899288103",
  "supplier_phone": "18888888981",
  "supplier_fax": "234251213",
  "supplier_postcode": "100000",
  "supplier_email": "123456@qq.com",
  "supplier_addr": "南京市建邺区",
  "supplier_settlement_type": "临时指定",
  "supplier_settle_day_of_month": "10",
  "supplier_settle_period": "30",
  "supplier_method": "购销",
  "supplier_settlement_model": "所属门店结算",
  "supplier_purchase_period": "30",
  "supplier_purchase_period_days": "1",
  "supplier_purchase_period_unit": "天",
  "supplier_purchase_date": "2021-01-01",
  "supplier_purchase_deadline": null,
  "supplier_shared": "1",
  "supplier_actived": "1",
  "supplier_last_edit_time": "2021-09-01 10:00:00",
  "user_center_partner_id": "1",
  "supplier_site": "www.baidu.com",
  "return_order_confirm_flag": "1",
  "supplier_memo": "测试备注",
  "supplier_min_order_money": 2.25,
  "supplier_shared_branches": [
    {
      "supplier_num": "434400001",
      "branch_num": "1"
    }
  ],
  "supplier_share_regions": [
    {
      "supplier_num": "434400001",
      "region_num": "1"
    }
  ],
  "supplier_account_details": [
    {
      "supplier_bank": "",
      "supplier_bank_account": "",
      "supplier_bank_account_name": "",
      "supplier_bank_default_flag": true,
      "supplier_bank_account_ref": ""
    }
  ],
  "supplier_extend1": "value",
  "supplier_extend2": "value",
  "supplier_extend3": "value",
  "supplier_extend4": "value",
  "supplier_extend5": "value",
  "supplier_extend6": "value",
  "supplier_extend7": "value",
  "supplier_extend8": "value",
  "supplier_extend9": "value",
  "supplier_extend10": "value",
  "supplier_min_money_type": "0",
  "supplier_recon_base": "自定义",
  "supplier_recon_day": "10",
  "supplier_recon": true,
  "supplier_rolling_order": true,
  "supplier_carriage": 10,
  "item_no_push_finance": true,
  "supplier_only_ln_item": true
}
```

## 返回码

暂无数据
