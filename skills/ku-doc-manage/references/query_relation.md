# 查询文档关联信息

分页查询指定文档的关联信息，包括业务关联（iCafe 卡片、会议、GitCase、iAPI、采购）、引用、被引用、共创、读取等关系数据。

## 使用规则

- 用户只提供文档名称或链接时，先按 URL 解析规则提取 `doc-id`，再调用本命令。
- `--type` 必须明确指定；用户意图与类型的映射见下表。
- `--business-type` 仅在 `--type=link` 时有效，不传则返回 link 下全部业务来源。
- 如需完整列表，需分页查询，不能只查第一页。

## 关联类型（--type）说明

| type 值 | 含义 | 典型数据内容 |
|---------|------|-------------|
| `link` | 业务关联 | 文档与外部业务对象的关联，如 iCafe 卡片、会议、GitCase、iAPI、采购单 |
| `reference` | 引用 | 该文档引用了哪些其他文档 |
| `referenced` | 被引用 | 该文档被哪些文档引用 |
| `co_create` | 共创 | 与该文档存在共创协作关系的文档/用户 |
| `read` | 读取 | 读取过该文档的相关方 |

## 业务来源（--business-type）说明

仅当 `--type=link` 时有效：

| businessType 值 | 含义 |
|----------------|------|
| `icafe` | iCafe 卡片 |
| `meeting` | 会议 |
| `gitcase` | GitCase |
| `iapi` | iAPI |
| `purch` | 采购 |

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| type | string | 是 | - | 关联类型：`link` / `reference` / `referenced` / `co_create` / `read` |
| business-type | string | 否 | 全部来源 | 业务来源，仅 `type=link` 时有效：`icafe` / `meeting` / `gitcase` / `iapi` / `purch` |
| page-num | int | 否 | 1 | 页码，从 1 开始 |
| page-size | int | 否 | 50 | 每页条数，最大 50 |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "type": "reference",
        "typeName": "引用",
        "count": 2,
        "total": 2,
        "pageNum": 1,
        "pageSize": 50,
        "totalPage": 1,
        "hasMore": false,
        "currentCount": 2,
        "data": [
            {
                "businessType": "reference",
                "data": {
                    "docGuid": "WKoT7ltTnjU1oW",
                    "docName": "被引用的文档A",
                    "docUrl": "https://ku.baidu-int.com/knowledge/xxx/xxx/xxx/WKoT7ltTnjU1oW"
                }
            },
            {
                "businessType": "reference",
                "data": {
                    "docGuid": "aBcDeFgHiJk",
                    "docName": "被引用的文档B",
                    "docUrl": "https://ku.baidu-int.com/knowledge/xxx/xxx/xxx/aBcDeFgHiJk"
                }
            }
        ]
    },
    "traceId": "727004757787687936"
}
```

## 响应字段说明

`returnCode` 为 200 时，`result` 字段定义如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| type | string | 关联类型，与请求参数一致 |
| typeName | string | 关联类型中文名：业务关联 / 引用 / 被引用 / 共创 / 读取 |
| count / total | long | 当前页条数 / 关联总条数（`total` 可能多于实际总量，见分页规则） |
| pageNum / pageSize | int | 当前页码 / 每页条数 |
| totalPage | int | 总页数 |
| hasMore | boolean | 是否存在下一页（**翻页判断以此字段为准**） |
| currentCount | int | 当前页实际返回的条目数，可能少于 `pageSize` |
| data | array | 关联条目列表 |
| data[].businessType | string | 条目所属来源类型（reference / referenced / co_create / read，或 link 下的 icafe / meeting / gitcase / iapi / purch） |
| data[].data | object | 条目详情，字段结构随 `businessType` 不同而不同，见下表 |

### data[].data 各来源类型字段结构

**① reference（引用）/ referenced（被引用）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| docGuid | string | 文档 ID |
| docName | string | 文档名称 |
| docUrl | string | 文档链接 |

**② link + icafe（iCafe 卡片）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| spaceCode | string | iCafe 空间标识 |
| sequence | string | 卡片序号 |
| title | string | 卡片标题 |
| status | string | 卡片状态 |
| issueType | string | 卡片类型 |
| permission | string | 当前用户对该卡片的权限 |
| link | string | 卡片详情链接 |

**③ link + meeting（会议）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| eventId | string | 会议 ID |
| subject | string | 会议主题 |
| startTime / endTime | long | 开始 / 结束时间（毫秒时间戳） |
| allCount | int | 参会总人数 |
| location | string | 会议地点 |
| detailUrl | string | 会议详情链接 |
| isLoop | boolean | 是否为循环日程 |
| organizer | string | 组织者 |
| attendees | array | 参会人列表，元素含 `email`、`name`、`userId` |

**④ link + iapi（iAPI 接口）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| id | int | iAPI 接口 ID |
| name / type / description | string | 接口名称 / 类型 / 描述 |
| method / path | string | 请求方法 / 接口路径 |
| status | string | 接口状态 |
| projectId / projectName | int / string | 项目 ID / 名称 |
| url | string | 接口详情链接 |
| createdAt / updatedAt / deletedAt | string | 创建 / 更新 / 删除时间 |

**⑤ link + gitcase（GitCase 用例）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| id | long | 用例 ID |
| name | string | 用例名称 |
| mindMapUrl | string | 脑图链接 |

**⑥ link + purch（采购）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| kuDocId | string | 知识库文档 ID |
| businessId | string | 采购业务 ID |
| businessUrl | string | 采购业务链接 |

**⑦ co_create（共创）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| virtualUser | object | 操作人，含 `memberGuid`、`name` |
| type | string | 操作类型 |
| action | string | 具体使用的 api |
| target | object | 操作对象，含 `members` 数组，元素含 `memberGuid`、`name`、`memberType` |
| time | long | 操作时间（毫秒时间戳） |

**⑧ read（读取）**

| 参数名 | 类型 | 描述 |
|---|---|---|
| virtualUser | object | 操作人，含 `memberGuid`、`name` |
| text | string | 读取描述文本 |

## 分页规则

`page-num` 表示第几页，`page-size` 表示每页请求条数（最大 50）。

**部分类型的详细信息由下游服务返回，下游可能对数据进行过滤，因此：**
- 当前页实际返回的条目数（`currentCount`）可能少于请求的 `pageSize`
- 返回的 `total` 可能多于实际总量

**翻页判断必须以 `hasMore` 字段为准**，不要依据"返回条数 < pageSize"或 `total` 推断是否还有下一页。

## 常见错误

| 状态码 | 说明 | 处理措施 |
|--------|------|---------|
| 10201 | 参数错误（type 取值非法、businessType 与非 link 类型组合、pageSize 超过 50 等） | 调整参数后重试 |
| 429 | 触发 API 限流 | 降低调用频率后重试 |
| 60414 | 无权限访问文档 | 核对 doc-id；确认有该文档【可阅读】及以上权限，必要时按权限申请流程处理 |

## CLI 调用示例

```bash
# 查询文档的全部业务关联
ku query-relation --doc-id WKoT7ltTnjU1oW --type link

# 只查询 iCafe 卡片关联
ku query-relation --doc-id WKoT7ltTnjU1oW --type link --business-type icafe

# 查询文档引用了哪些文档
ku query-relation --doc-id WKoT7ltTnjU1oW --type reference

# 查询文档被哪些文档引用
ku query-relation --doc-id WKoT7ltTnjU1oW --type referenced

# 翻页查询
ku query-relation --doc-id WKoT7ltTnjU1oW --type link --page-num 2 --page-size 50
```

## 典型用户 Prompt

| 用户 Prompt | Agent 处理方式 |
|---|---|
| 这篇文档关联了哪些 iCafe 卡片 | `--type link --business-type icafe` 查询并汇总 |
| 查一下这篇文档关联了哪些会议 | `--type link --business-type meeting` 查询并展示会议时间 |
| 这篇文档被哪些文档引用了 | `--type referenced` 查询并列出引用方 |
| 这篇文档引用了什么文档 | `--type reference` 查询并列出被引用文档 |
| 看看文档的全部业务关联 | `--type link` 不传 business-type，返回全部来源后按来源分组展示 |
