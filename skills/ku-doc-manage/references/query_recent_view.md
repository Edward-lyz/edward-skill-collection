# 查询文档浏览记录

查询指定在线文档在一定时间范围内的访问记录，包括访问人身份和访问时间。

## 使用规则

- 用户只提供文档名称或链接时，先获取 `doc-id`，再调用本命令。
- 用户使用“今天、昨天、本周、近 1 个月”等自然语言时间时，先转换为毫秒级时间戳。
- 默认查询最近 7 天；单次最长查询 7 天；更长周期需按 7 天拆分多次查询。
- 如需完整统计，需分页查询，不能只查第一页。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| begin-time | long | 否 | 最近 7 天起始时间 | 记录起始时间(毫秒级时间戳) |
| end-time | long | 否 | 当前时间 | 记录结束时间(毫秒级时间戳) |
| page-num | int | 否 | 1 | 页码 |
| page-size | int | 否 | 10 | 每页数量 |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "repositoryGuid": "E3d4LRExEl",
        "docGuid": "1xosIYvQX3qxeI",
        "totalViewers": 1,
        "count": 1,
        "data": [
            {
                "username": "zhangsan",
                "nickname": "张三",
                "email": "zhangsan@baidu.com",
                "viewTime": 1640966400000
            }
        ]
    },
    "traceId": "123456789012345678"
}
```

## 响应字段说明

| 字段 | 说明 |
|---|---|
| repositoryGuid | 文档所在知识库 ID |
| docGuid | 文档 ID，对应请求参数 `doc-id` |
| totalViewers | 总访问次数/总浏览记录数，不做用户去重 |
| count | 当前页返回的访问记录数量 |
| data | 当前页访问记录列表 |
| username / nickname / email | 访问人身份信息 |
| viewTime | 访问时间，毫秒级时间戳 |

> 如需展示去重访问人数，Agent 应基于 `username` 或 `email` 自行去重统计。

## 分页规则

`page-num` 表示第几页，`page-size` 表示每页返回多少条。  
如果用户需要完整统计，应持续翻页，直到返回记录数小于 `page-size` 或无更多数据。

## CLI 调用示例

```bash
# 查询默认时间范围，默认最近 7 天
ku query-recent-view --doc-id WKoT7ltTnjU1oW

# 指定时间范围查询
ku query-recent-view --doc-id WKoT7ltTnjU1oW --begin-time 1640966400000 --end-time 1641052800000

# 翻页查询
ku query-recent-view --doc-id WKoT7ltTnjU1oW --page-num 2 --page-size 20
```

## 典型用户 Prompt

| 用户 Prompt | Agent 处理方式 |
|---|---|
| 查一下今天谁看过这篇文档 | 转换时间范围，查询并汇总访问人 |
| 看看老板有没有看我发的方案 | 查询访问记录，并按目标用户筛选 |
| 统计这篇文档本周有多少人看过 | 查询本周记录，统计总访问次数和去重访问人数 |
| 查询近 1 个月访问记录 | 按 7 天拆分查询并合并统计 |