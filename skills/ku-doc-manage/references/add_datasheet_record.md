# add-datasheet-records - 添加数据表记录

向指定数据表添加新记录，支持单条和批量添加。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID |
| view-id | string | 是 | 视图ID |
| records | string | 是 | 记录数据 JSON 数组 |

### record_data 结构说明

> 如需新增包含附件类型字段的记录，请先使用 [upload_datasheet_attachment.md](./upload_datasheet_attachment.md) 上传附件，获取 `mimeType`、`name`、`size`、`token`、`url` 等附件参数后，再将这些参数作为附件字段值写入 `records`。

```json
{
    "records": [
        {
            "fields": {
                "字段名1": "值1",
                "字段名2": "值2",
                "字段名3": 123,
                "附件": [
                    {
                        "mimeType": "application/octet-stream",
                        "name": "1.sql",
                        "size": 1918,
                        "token": "space/2026/06/30/892545f4e5fa434099f1dfbxxxxb33",
                        "url": "https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfbxxxb33"
                    }
                ]
            }
        },
        # 可以包含多条记录
        {
            "fields": {
                "字段名1": "值3",
                "字段名2": "值4"
            }
        }
    ]
}
```

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.records | list | 新增的记录列表 |
| result.records[].recordId | string | 新增记录的唯一 ID |
| result.records[].fields | object | 新增记录的字段内容，仅返回实际写入的字段 |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {
        "records": [
            {
                "fields": {
                    "标题": "测试标题3"
                },
                "recordId": "recVNNHvWiNiI"
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689810669935931392"
}
```

## CLI调用示例

```bash
# 添加单条记录
ku add-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --view-id viwxxx --records '[{"fields": {"标题": "新任务", "状态": "待处理", "负责人": "张三", "优先级": "高"}}]'

# 批量添加多条记录
ku add-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --view-id viwxxx --records '[{"fields": {"标题": "新任务", "状态": "待处理"}}, {"fields": {"标题": "新任务", "状态": "进行中"}}]'

# 添加包含附件字段的记录
ku add-datasheet-records --dist-id dst2dkRDo6AEJzFpZM --view-id viww2ircw1hng --records '[{"fields":{"标题":"测试标题3","附件":[{"mimeType":"application/octet-stream","name":"1.sql","size":1918,"token":"space/2026/06/30/892545f4e5fa434099f1dfbxxxx33","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfb2exxx33"}]}}]'
```