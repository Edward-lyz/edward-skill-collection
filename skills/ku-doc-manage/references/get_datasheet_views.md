# get-datasheet-views - 获取数据表视图

获取数据表的所有视图信息。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID，唯一标识一个数据表 |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.views | list | 视图列表 |
| result.views[].id | string | 视图唯一 ID，可用于查询记录时指定视图 |
| result.views[].name | string | 视图显示名称 |
| result.views[].type | string | 视图类型，如 `"Grid"`（表格视图） |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {
        "views": [
            {
                "id": "viwzJzBij51Cq",
                "name": "表格",
                "type": "Grid"
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689806969574147072"
}
```

## CLI调用示例

```bash
# 获取数据表视图列表
ku get-datasheet-views --dist-id dstxRvKjhSZZJDNvpZ
```