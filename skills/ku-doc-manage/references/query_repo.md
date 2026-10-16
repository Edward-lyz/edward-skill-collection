# 分页查询知识库文档列表

根据知识库ID分页查询文档列表,支持多种筛选条件和互动数据展示。也支持查询指定父目录下的文档列表。

> **快捷用法**：如果用户提供的是某个父目录的文档 URL 或文档 ID，可直接从中解析出 `repo-id`（`repositoryGuid`）和 `parent-doc-id`（`docGuid`），无需用户单独传入这两个参数。
>
> 知识库文档 URL 格式为：
> `https://ku.baidu-int.com/knowledge/{spaceGuid}/{categoryGuid}/{repositoryGuid}/{docGuid}`
>
> 示例：`https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/E3d4LRExEl/1xosIYvQX3qxeI`
> - `repo-id` = `E3d4LRExEl`（倒数第二段）
> - `parent-doc-id` = `1xosIYvQX3qxeI`（最后一段）

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| repo-id | string | 是 | - | 知识库ID(repositoryGuid) |
| page-num | int | 否 | 1 | 页码 |
| page-size | int | 否 | 10 | 每页数量 |
| parent-doc-id | string | 否 | null | 父文档ID |
| doc-guids | array | 否 | null | 文档ID列表,限制查询范围 |
| urls | array | 否 | null | 文档URL列表,限制查询范围 |
| show-creator | boolean | 否 | false | 是否展示文档作者信息 |
| show-publisher | boolean | 否 | false | 是否展示文档最近更新者信息 |
| order-by | string | 否 | null | 排序字段(如"publishTime") |
| order-direction | string | 否 | "desc" | 排序方向(desc=倒序,asc=正序) |


## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "count": 622,
        "data": [
            {
                "childCount": 0,
                "created": 1640966400000,
                "creatorUserInfo": {
                    "email": "zhangsan@baidu.com",
                    "nickname": "张三",
                    "username": "zhangsan"
                },
                "docGuid": "1xosIYvQX3qxeI",
                "name": "示例文档标题",
                "publishTime": 1641052800000,
                "publisherUserInfo": {
                    "email": "lisi@baidu.com",
                    "nickname": "李四",
                    "username": "lisi"
                },
                "repositoryGuid": "E3d4LRExEl",
                "type": 1,
                "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/E3d4LRExEl/1xosIYvQX3qxeI"
            }
        ],
        "total": 622
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
# 基础查询
ku query-repo --repo-id E3d4LRExEl

# 按更新时间倒序排列，自定义每页数量
ku query-repo --repo-id E3d4LRExEl --order-by publishTime --order-direction desc --page-size 20

# 显示创建者和发布者信息
ku query-repo --repo-id E3d4LRExEl --show-creator --show-publisher

# 翻页查询
ku query-repo --repo-id E3d4LRExEl --page-num 2 --page-size 20

# 查询指定父目录下的文档列表（repo-id 和 parent-doc-id 可从父目录文档URL中解析）
ku query-repo --repo-id E3d4LRExEl --parent-doc-id 1xosIYvQX3qxeI

# 限制查询范围到指定文档ID列表
ku query-repo --repo-id E3d4LRExEl --doc-guids doc1,doc2,doc3

# 限制查询范围到指定文档URL列表
ku query-repo --repo-id E3d4LRExEl --urls url1,url2
```
