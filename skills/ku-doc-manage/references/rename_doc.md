# rename-doc - 重命名文档

重命名指定的知识库文档。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| new-name | string | 是 | - | 新文档名称 |
| username | string | 是 | - | 操作人用户名 |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"OK"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.success | bool | 重命名操作是否成功 |
| result.docInfo | object | 重命名后的文档信息 |
| result.docInfo.docGuid | string | 文档ID |
| result.docInfo.name | string | 重命名后的文档名称，重点关注该字段 |
| result.docInfo.url | string | 文档访问链接；重命名成功后可返回该链接，方便用户点击查询验证 |
| result.docInfo.repositoryGuid | string | 所属知识库ID |
| result.docInfo.typeDesc | string | 文档类型描述 |

## 响应示例

```json
{
  "msg": "OK",
  "result": {
    "docInfo": {
      "childCount": 3,
      "created": 1658846508000,
      "docGuid": "9bf4e53e8a394d",
      "groupGuid": "hAVa-nq7IH",
      "name": "QQ测试重命名",
      "publishTime": 1782784299000,
      "repositoryGuid": "x4KQsIwk3I",
      "spaceGuid": "HFVrC7hq1Q",
      "type": 1,
      "typeDesc": "普通文档",
      "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/hAVa-nq7IH/x4KQsIwk3I/9bf4e53e8a394d"
    },
    "success": true
  },
  "returnCode": 200,
  "returnMessage": "OK",
  "status": 200,
  "success": true,
  "traceId": "726978154617563136"
}
```

## 结果展示建议

重命名成功后，建议向用户展示 `result.docInfo.name` 和 `result.docInfo.url`，其中 `result.docInfo.url` 可用于点击打开文档并验证名称是否已更新。

## CLI调用示例

```bash
# 重命名文档
ku rename-doc --doc-id WKoT7ltTnjU1oW --new-name "新的文档标题" --username zhangsan

```
