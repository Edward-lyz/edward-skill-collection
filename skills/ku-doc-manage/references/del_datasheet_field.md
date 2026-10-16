# del-datasheet-field - 删除数据表字段

删除数据表的指定字段。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID |
| field-id | string | 是 | 要删除的字段ID（可通过 get-datasheet-fields 获取） |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result | object | 空对象 `{}`，删除操作无额外返回数据 |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {},
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689811862560315392"
}
```

## CLI调用示例

```bash
# 删除数据表字段
ku del-datasheet-field --dist-id dstxRvKjhSZZJDNvpZ --field-id fldhLZsuiUaJL
```