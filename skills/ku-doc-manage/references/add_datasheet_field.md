# add-datasheet-field - 添加数据表字段

向数据表添加新字段。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID |
| type | string | 是 | 字段类型，如 `SingleText`、`Number`、`SingleSelect` 等 |
| name | string | 是 | 字段名称，不能超过100个字符 |
| property | object | 条件必需 | 字段属性，`Text`/`URL`/`Phone`/`Email`/`Attachment`/`Member`/`WorkDoc`/`Formula`/`AutoNumber`/`CreatedBy`/`LastModifiedBy`/`Button` 类型非必填，其他类型必填 |

### 字段类型说明

| 类型 | 说明 | property示例 |
|------|------|-------------|
| SingleText | 单行文本 | `{"defaultValue": "默认文本"}` |
| Text | 多行文本 | 无需传property |
| SingleSelect | 单选 | `{"options": [{"name": "选项1"}]}` |
| MultiSelect | 多选 | `{"options": [{"name": "选项1"}]}` |
| Number | 数字 | `{"precision": 2}` |
| DateTime | 日期时间 | `{"dateFormat": "YYYY-MM-DD"}` |
| Checkbox | 复选框 | `{"icon": "smile"}` |
| URL | 网址 | 无需传property |
| Phone | 电话 | 无需传property |
| Email | 邮箱 | 无需传property |
| Currency | 货币 | `{"precision": 2}` |
| Percent | 百分比 | `{"precision": 1}` |
| Attachment | 附件 | 无需传property |
| Member | 成员 | 无需传property |
| Rating | 评级 | `{"icon": "star","max": 5}` |
| WorkDoc | 工作文档 | 无需传property |
| Formula | 公式 | 无需传property |
| AutoNumber | 编号 | 无需传property |
| CreatedTime | 创建时间 | `{"dateFormat": "YYYY/MM/DD"}` |
| LastModifiedTime | 最后修改时间 | `{"dateFormat": "YYYY/MM/DD"}` |
| CreatedBy | 创建人 | 无需传property |
| LastModifiedBy | 最后修改人 | 无需传property |
| Button | 按钮 | 无需传property |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.id | string | 新创建的字段 ID，可用于后续字段操作 |
| result.name | string | 新创建的字段名称 |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {
        "id": "fldhLZsuiUaJL",
        "name": "数字列"
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689808229064919040"
}
```

## CLI调用示例

```bash
# 添加数字类型字段
ku add-datasheet-field --dist-id dstxRvKjhSZZJDNvpZ --type Number --name "数字列" --property '{"precision": 2}'

# 添加单选类型字段
ku add-datasheet-field --dist-id dstxRvKjhSZZJDNvpZ --type SingleSelect --name "状态" --property '{"options": [{"name": "待处理"}, {"name": "进行中"}, {"name": "已完成"}]}'

# 添加文本类型字段（property 非必填）
ku add-datasheet-field --dist-id dstxRvKjhSZZJDNvpZ --type Text --name "备注"
```