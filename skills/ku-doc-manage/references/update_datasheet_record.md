# update-datasheet-records - 更新数据表记录

更新数据表中已存在的记录。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID |
| view-id | string | 是 | 视图ID |
| records | string | 是 | 更新的记录数据，必须包含recordId（可通过 get-datasheet-records 获取） |

### record_data 结构

> 如需更新附件类型字段，请先使用 [upload_datasheet_attachment.md](./upload_datasheet_attachment.md) 上传附件，获取 `mimeType`、`name`、`size`、`token`、`url` 等附件参数后，再将这些参数作为附件字段值写入 `records`。附件字段更新默认按“追加附件”处理：如果记录中已有附件数据，需要先使用 `get-datasheet-records` 查询并保留已有附件列表，再把新增附件追加到列表后一起提交。如果用户明确希望覆盖附件字段，则可以直接使用新增附件数据更新记录，无需查询已有附件。提交更新前需要按 `token` + `url` 对附件列表去重；如果存在 `token` 和 `url` 都相同的重复附件，只保留一份。`token` 和 `url` 不允许省略或替换，必须使用上传接口返回的真实值。

```json
{
    "records": [
        {
            "recordId": "rec123456",
            "fields": {
                "字段名1": "新值1",
                "字段名2": "新值2",
                "附件": [
                    {
                        "mimeType": "application/octet-stream",
                        "name": "1.sql",
                        "size": 1918,
                        "token": "space/2026/06/30/892545f4e5fa434099f1dfb2efxxxxb33",
                        "url": "https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfbxxxx3b33"
                    }
                ]
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
| result.records | list | 已更新的记录列表 |
| result.records[].recordId | string | 记录唯一 ID |
| result.records[].createdAt | long | 记录创建时间（毫秒时间戳） |
| result.records[].updatedAt | long | 记录最后更新时间（毫秒时间戳） |
| result.records[].fields | object | 更新后的字段内容，仅返回实际更新的字段 |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {
        "records": [
            {
                "createdAt": 1773922880000,
                "fields": {
                    "状态": "已完成"
                },
                "recordId": "recVNNHvWiNiI",
                "updatedAt": 1773922880000
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689815786734395392"
}
```

## CLI调用示例

```bash
# 更新单条记录
ku update-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --view-id viwxxx --records '[{"recordId": "rec123456", "fields": {"状态": "已完成"}}]'

# 批量更新多条记录
ku update-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --view-id viwxxx --records '[{"recordId": "rec123456", "fields": {"状态": "已完成", "完成时间": 1635724800000}}, {"recordId": "rec789012", "fields": {"状态": "进行中"}}]'

# 追加附件字段：先查询已有附件列表，再将已有附件和新增附件一起提交，避免覆盖原附件
ku get-datasheet-records --dist-id dst2dkRDo6AEJzFpZM --view-id viww2ircw1hng --record-ids recaTsKD49BM8
ku update-datasheet-records --dist-id dst2dkRDo6AEJzFpZM --view-id viww2ircw1hng --records '[{"recordId":"recaTsKD49BM8","fields":{"附件":[{"mimeType":"application/octet-stream","name":"已有附件.sql","size":1024,"token":"space/2026/06/30/existing-real-token","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/existing-real-token"},{"mimeType":"application/octet-stream","name":"1.sql","size":1918,"token":"space/2026/06/30/892545f4e5fa434099f1dfbxxxxb33","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfb2exxxx33"}]}}]'
```