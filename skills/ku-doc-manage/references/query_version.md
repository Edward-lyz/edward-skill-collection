# 查询文档版本列表 (query-version)

查询指定文档的所有历史版本信息，用于文档版本回溯和历史记录查看。

## 能力说明

查询文档版本历史列表，返回版本 ID、更新时间、更新人、版本类型。

## 能力特性

**历史可追溯**：支持查询某个时间点、某个人、某次版本的内容变化。

> **核心用途**：获取文档历史版本列表，版本 ID 可配合 `query-content` 的 `--version-id` 参数读取历史正文，实现版本对比、变更审计、回滚恢复等功能。

## 典型场景

| 用户问题 | 对应操作 |
|---------|---------|
| 最近谁改了文档 | `query-version` 查看最新版本记录 |
| 这篇文档有哪些历史版本 | `query-version` 查看完整版本列表 |

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 否* | - | 文档ID(docGuid)，与url二选一 |
| url | string | 否* | - | 文档URL，与doc-id二选一 |
| page-num | int | 否 | 1 | 页码，从1开始 |
| page-size | int | 否 | 10 | 每页数量，建议值：1-100 |

> **说明**：`doc-id` 和 `url` 参数至少需要提供一项


## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "count": 6,
        "data": [
            {
                "createTime": 1778468485000,
                "docGuid": "48d083b9c57448",
                "initType": 4,
                "sourceVersionId": 0,
                "updateUserInfo": {
                    "email": "qinqin@baidu.com",
                    "nickname": "秦琴",
                    "username": "qinqin"
                },
                "versionId": 6,
                "versionName": ""
            },
            {
                "createTime": 1775111284000,
                "docGuid": "48d083b9c57448",
                "initType": 4,
                "sourceVersionId": 0,
                "updateUserInfo": {
                    "email": "qinqin@baidu.com",
                    "nickname": "秦琴",
                    "username": "qinqin"
                },
                "versionId": 5,
                "versionName": ""
            }
        ],
        "docGuid": "48d083b9c57448",
        "total": 6
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "708929306156751872"
}
```

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| versionId | int | 版本ID，可用于 `query-content --version-id` 获取该版本的正文内容 |
| versionName | string | 版本名称 |
| initType | int | 版本类型：0-发布，1-新建，2-标题编辑，3-回退，4-草稿 |
| createTime | long | 版本创建时间（毫秒时间戳） |
| docGuid | string | 文档ID |
| sourceVersionId | int | 来源版本ID |
| updateUserInfo | object | 更新用户信息 |
| count | int | 当前页返回的版本数量 |
| total | int | 该文档的版本总数 |

**initType 类型说明**：

| initType | 说明 |
|----------|------|
| 0 | 发布（正式版本） |
| 1 | 新建（文档首次创建） |
| 2 | 标题编辑（仅修改标题） |
| 3 | 回退（回退到历史版本） |
| 4 | 草稿（未发布版本） |

## 分页规则

默认每页返回 10 条记录，如需完整版本列表需持续翻页：

| 响应判断条件 | 说明 |
|-------------|------|
| `count < page-size` | 已到最后一页 |
| `count === 0` | 无更多数据 |
| 累计数量 ≥ `total` | 已获取全部版本 |


## CLI 调用示例

```bash
# 基础查询（使用文档ID）
ku query-version --doc-id zBXzyBE1u0jVK8

# 使用URL查询
ku query-version --url "https://ku.baidu-int.com/knowledge/path1/path2/path3/docId"

# 分页查询
ku query-version --doc-id zBXzyBE1u0jVK8 --page-num 1 --page-size 20

# 只查询最新版本
ku query-version --doc-id zBXzyBE1u0jVK8 --page-num 1 --page-size 1
```

## 错误码

| returnCode | 说明 | 处理建议 |
|-------------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误（缺少 docId 和 url，或两者都为空） | 检查参数，确保至少提供了 doc-id 或 url |
| 60414 | 无权限访问文档 | 检查用户是否有该文档的访问权限 |