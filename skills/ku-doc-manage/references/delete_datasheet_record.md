# delete-datasheet-records - 删除数据表记录

删除数据表中的指定记录，支持批量删除，一次最多删除 10 条。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID |
| record-ids | string | 是 | 要删除的记录ID，支持单个或多个，多个时用英文逗号分隔，一次最多 10 条（可通过 get-datasheet-records 获取） |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result | null | 删除操作无返回数据，固定为 `null` |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": null,
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "68981354213224480"
}
```

## CLI调用示例

```bash
# 删除单条记录
ku delete-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --record-ids rec123456

# 批量删除多条记录（最多 10 条，用英文逗号分隔）
ku delete-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --record-ids rec123456,rec789012,rec345678
```