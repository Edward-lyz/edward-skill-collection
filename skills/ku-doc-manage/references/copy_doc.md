# 复制文档

将文档复制到指定知识库或目录。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 待复制的源文档ID |
| username | string | 否 | ak对应用户 | 操作者用户名 |
| target-repo-id | string | 否 | 源文档所在库 | 目标知识库ID |
| parent-doc-id | string | 否 | 源文档同级 | 目标父目录ID |
| new-title | string | 否 | 源标题的复制 | 新文档标题 |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "docInfo": {
            "childCount": 0,
            "created": 1640966400000,
            "docGuid": "2xosIYvQX3qxeJ",
            "name": "示例文档的复制",
            "publishTime": 1640966400000,
            "repositoryGuid": "E3d4LRExEl",
            "type": 1,
            "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/hAVa-nq7IH/E3d4LRExEl/2xosIYvQX3qxeJ"
        },
        "success": true
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "123456789012345678"
}
```


## CLI调用示例

```bash
# 复制文档到指定知识库
ku copy-doc --doc-id WKoT7ltTnjU1oW --target-repo-id E3d4LRExEl --new-title "我的文档副本"

# 复制到同一知识库（省略 --target-repo-id）
ku copy-doc --doc-id WKoT7ltTnjU1oW --new-title "我的文档副本"
```