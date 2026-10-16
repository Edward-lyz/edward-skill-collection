# 查询我最近浏览/编辑的文档

查询当前用户最近浏览或最近编辑的文档列表。

## 使用规则

- 通过 `action` 参数区分查询类型：`recent-view` 表示最近浏览，`recent-edit` 表示最近编辑，默认为 `recent-view`。
- 用户使用"今天、昨天、本周、近 1 个月"等自然语言时间时，先转换为毫秒级时间戳。
- 默认查询最近 5 天；单次最长查询 5 天；更长周期需按 5 天拆分多次查询。
- `page-size` 最大支持 20 条，超过 20 会报错。
- 接口最大返回总数为 200 条记录，如需完整统计，需分页查询，不能只查第一页。
- **必须展示的字段**：返回给用户时，必须展示文档标题（`name`）、文档访问链接（`url`）、文档类型（`typeDesc`）、最后访问/编辑时间（`visitTime`），其他字段可根据用户需求返回。
- **排序规则**：列表数据按时间倒排（最近的在前）返回给用户。
- **权限限制**：此能力仅支持查询当前用户本人的浏览/编辑记录，不支持查询他人的数据。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| action | string | 是 | recent-view | 查询类型：`recent-view`（最近浏览）或 `recent-edit`（最近编辑） |
| begin-time | long | 否 | 5 天前 | 起始时间（毫秒级时间戳） |
| end-time | long | 否 | 当前时间 | 结束时间（毫秒级时间戳） |
| page-num | int | 否 | 1 | 页码 |
| page-size | int | 否 | 20 | 每页数量（最大 20） |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "beginTime": "2026-05-22 11:56:59",
        "beginTimeDesc": "2026-05-22 11:56:59",
        "count": 15,
        "data": [
            {
                "action": 1,
                "actionDesc": "最近浏览",
                "childCount": 0,
                "created": "2026-05-26 19:00:39",
                "docGuid": "Qm2DixjlG8QV5k",
                "groupGuid": "2tsPs8CtSd",
                "name": "【2026-05-26】文件泄漏漏洞需通过升级SDK解决",
                "publishTime": "2026-05-26 19:00:40",
                "repositoryGuid": "z1biVCa6jg",
                "repositoryInfo": {
                    "groupGuid": "2tsPs8CtSd",
                    "name": "SO 大通讯基础团队",
                    "ownerType": 30,
                    "repositoryGuid": "z1biVCa6jg",
                    "spaceGuid": "HFVrC7hq1Q",
                    "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/z1biVCa6jg"
                },
                "spaceGuid": "HFVrC7hq1Q",
                "type": 1,
                "typeDesc": "普通文档",
                "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/z1biVCa6jg/Qm2DixjlG8QV5k",
                "visitTime": "2026-05-26 19:00:40"
            }
        ],
        "endTime": "2026-05-27 11:56:59",
        "endTimeDesc": "2026-05-27 11:56:59",
        "total": 15,
        "username": "ai_testassistant"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "714688512140744704"
}
```

## 响应字段说明

| 字段 | 说明 |
|---|---|
| beginTime | 查询起始时间（格式：YYYY-MM-DD HH:mm:ss） |
| beginTimeDesc | 查询起始时间（格式：YYYY-MM-DD HH:mm:ss） |
| endTime | 查询结束时间（格式：YYYY-MM-DD HH:mm:ss） |
| endTimeDesc | 查询结束时间（格式：YYYY-MM-DD HH:mm:ss） |
| count | 当前页返回的文档数量 |
| total | 符合条件的文档总数 |
| username | 当前用户名 |
| data | 文档列表 |
| data[].docGuid | 文档 ID |
| data[].name | 文档标题 |
| data[].url | 文档访问链接 |
| data[].action | 操作类型（1=最近浏览，2=最近编辑） |
| data[].actionDesc | 操作类型描述 |
| data[].type | 文档类型 |
| data[].typeDesc | 文档类型描述 |
| data[].visitTime | 最后访问/编辑时间（格式：YYYY-MM-DD HH:mm:ss） |
| data[].created | 文档创建时间（格式：YYYY-MM-DD HH:mm:ss） |
| data[].publishTime | 文档发布时间（格式：YYYY-MM-DD HH:mm:ss） |
| data[].repositoryGuid | 文档所在知识库 ID |
| data[].repositoryInfo | 知识库详细信息 |
| data[].spaceGuid | 空间 ID |
| data[].groupGuid | 分组 ID |
| data[].childCount | 子文档数量 |

## 分页规则

`page-num` 表示第几页，`page-size` 表示每页返回多少条。  
如果用户需要完整统计，应持续翻页，直到返回记录数小于 `page-size` 或无更多数据。

## CLI 调用示例

```bash
# 查询最近浏览的文档
ku query-recent-doc --action recent-view

# 查询最近编辑的文档
ku query-recent-doc --action recent-edit

# 指定时间范围查询
ku query-recent-doc --action recent-view --begin-time 1716192000000 --end-time 1716796800000

# 分页查询
ku query-recent-doc --action recent-view --page-num 1 --page-size 20
```

## 典型用户 Prompt

| 用户 Prompt | Agent 处理方式 |
|---|---|
| 我最近看过哪些文档 | 调用 `--action recent-view` 查询最近浏览记录 |
| 查一下我最近编辑的文档 | 调用 `--action recent-edit` 查询最近编辑记录 |
| 我今天看过什么文档 | 转换时间范围，调用 `--action recent-view` 并指定时间参数 |
| 列出我本周编辑的所有文档 | 转换时间范围，调用 `--action recent-edit` 并指定时间参数 |
