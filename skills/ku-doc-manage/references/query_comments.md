# 查询文档评论

查询文档的底部评论和侧边评论。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| no-bottom | boolean | 否 | false | 不查询底部评论（默认查询，传入此参数则跳过） |
| no-side | boolean | 否 | false | 不查询侧边评论（默认查询，传入此参数则跳过） |
| page-num | int | 否 | 1 | 页码 |
| page-size | int | 否 | 10 | 每页数量 |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "1xosIYvQX3qxeI",
        "bottomCommentResult": {
            "totalCount": 2,
            "rootCount": 1,
            "comments": [
                {
                    "commentType": 1,
                    "commentGuid": "5356d6774d",
                    "text": "这是一条底部评论示例",
                    "content": [
                        {
                            "type": "paragraph",
                            "children": [
                                {
                                    "text": "这是一条底部评论示例"
                                }
                            ],
                            "textAlign": "left",
                            "blockId": "docyg-377e18e0-e141-11f0-a9d1-2d329f98e194"
                        }
                    ],
                    "replyCommentGuid": "0000000000",
                    "rootCommentGuid": "0000000000",
                    "quote": null,
                    "status": 20,
                    "created": 1640966400000,
                    "commentUserInfo": {
                        "username": "zhangsan",
                        "nickname": "张三",
                        "email": "zhangsan@baidu.com"
                    },
                    "childrenComments": [
                        {
                            "commentType": 2,
                            "commentGuid": "d7818e9c77",
                            "text": "这是一条回复评论示例",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "children": [
                                        {
                                            "text": "这是一条回复评论示例"
                                        }
                                    ],
                                    "textAlign": "left",
                                    "blockId": "docyg-43b514b0-e141-11f0-a9d1-2d329f98e194",
                                    "textIndent": 0,
                                    "diffId": "7408clTA"
                                }
                            ],
                            "replyCommentGuid": "5356d6774d",
                            "rootCommentGuid": "5356d6774d",
                            "quote": null,
                            "status": 20,
                            "created": 1640970000000,
                            "commentUserInfo": {
                                "username": "lisi",
                                "nickname": "李四",
                                "email": "lisi@baidu.com"
                            },
                            "childrenComments": []
                        }
                    ]
                }
            ]
        },
        "sideCommentResult": {
            "totalCount": 0,
            "rootCount": 0,
            "comments": []
        }
    },
    "traceId": "123456789012345678",
    "status": 200,
    "msg": "OK",
    "success": true
}
```

## CLI调用示例

```bash
# 查询全部评论（底部+侧边）
ku query-comments --doc-id WKoT7ltTnjU1oW

# 翻页查询
ku query-comments --doc-id WKoT7ltTnjU1oW --page-num 2 --page-size 20

# 仅查询底部评论
ku query-comments --doc-id WKoT7ltTnjU1oW --no-side

# 仅查询侧边评论
ku query-comments --doc-id WKoT7ltTnjU1oW --no-bottom
```