# 申请知识库/文档权限

为指定用户申请知识库或文档的访问权限。传入 `doc-id` 则申请文档权限，传入 `repo-id` 则申请知识库权限；若两者均传，以 `doc-id` 优先。

## 使用规则

- **申请对象确定**：若用户未指定申请对象，先调用 `query-apply-member` 获取可申请对象列表，默认取列表第一个对象作为 `target-username`；若用户已明确指定申请对象，直接使用。
- **申请原则**：
  - 用户意图明确是"申请权限"时，可直接发起申请，无需二次确认。
  - 执行读/写/管理类任务因权限受阻时，需先向用户确认所需申请的权限信息（文档、角色、申请对象），用户确认后再发起申请。
  - **批量申请二次确认**：若同一次请求中申请的文档/知识库数量 ≥ 3 个，必须先使用 `AskUserQuestion` 向用户展示完整申请信息（清单、申请理由、默认发送对象）并等待确认，用户确认后才能逐个调用 `apply-member` 发起申请；确认前不得执行任何一次申请。确认示例：

    ```
    我需要为您申请以下 11 篇文档的权限，申请理由：【申请理由】。将默认向管理员发送申请，是否确认？
    📄 【文档1】、【文档2】…… 共 11 篇文档的【阅读权限】

    1. 确认，帮我发送全部申请
    2. 取消，不需要申请了
    3. 其他（如：只申请部分文档权限或指定文档权限申请对象）
    ```

    对应 `AskUserQuestion` 调用：

    ```
    AskUserQuestion(questions=[
        {
            "question": "我需要为您申请以下 11 篇文档的权限，申请理由：【申请理由】。将默认向管理员发送申请，是否确认？\n📄 【文档1】、【文档2】…… 共 11 篇文档的【阅读权限】",
            "header": "批量申请确认",
            "options": [
                {"label": "确认，帮我发送全部申请", "description": "按清单对全部文档/知识库发起申请"},
                {"label": "取消，不需要申请了", "description": "放弃本次批量申请"},
                {"label": "其他", "description": "只申请部分文档权限，或指定不同的申请对象"}
            ],
            "multiSelect": false
        }
    ])
    ```
- **限流规则**：每个用户对同一文档/知识库每天最多可发起 5 次权限申请，超出会触发限流报错。
- **结果告知**：申请发送后必须告知用户申请结果（成功/失败/已有权限/已删除/限流），并展示【目标文档或知识库】【申请权限】【申请对象】等关键信息。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 条件必需 | 要申请权限的文档ID，与 repo-id 二选一 |
| repo-id | string | 条件必需 | 要申请权限的知识库ID，与 doc-id 二选一 |
| target-username | string | 是 | 申请对象的用户名（邮箱前缀/UUAP），未指定时可通过 `query-apply-member` 获取推荐对象 |
| apply-role-name | string | 是 | 要申请的角色：文档为 DocReader/DocMember/DocAdmin；知识库为 RepoReader/RepoMember/RepoAdmin |
| apply-message | string | 否 | 申请原因，不超过 200 字符，会展示在申请卡片中给被申请人查看 |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "LxW8kYj7SMOj76",
        "targetUsername": "zhangsan",
        "applyRoleName": "DocReader",
        "success": true,
        "message": "申请成功"
    },
    "traceId": "1862438216856076288"
}
```

申请知识库权限时，`result` 中对应字段为 `repositoryGuid` 而非 `docGuid`，其余字段结构一致。

## 响应字段说明

| 字段 | 说明 |
|---|---|
| result.docGuid / result.repositoryGuid | 申请的目标文档ID / 知识库ID |
| result.targetUsername | 实际发起申请的对象用户名 |
| result.applyRoleName | 本次申请的角色 |
| result.success | 本次申请是否成功发起 |
| result.message | 申请结果描述，用于判断具体场景（见下表） |

## 常见结果与处理

依据 `returnCode` 与 `result.message` 判断场景并对用户反馈：

| 场景 | returnCode / result.success | result.message（示例） | Agent 处理方式 |
|------|------------------------------|------------------------|---------------|
| 申请发送成功 | 200 / true | 申请成功 | 告知用户已发送申请，注明目标文档/知识库、申请权限、申请对象，等待审批 |
| 申请者已拥有对应权限 | 200 / false | 类似"用户已拥有对应权限" | 告知用户"当前已拥有该权限，无需重复申请"，不重复发起 |

非 200 报错时，依据下方「已知错误状态码」表格中的具体 `returnCode` 判断场景并处理，不再依赖 `result.message` 模糊匹配。

### 已知错误状态码

| 状态码 | 状态信息 | Agent 处理方式 |
|--------|---------|---------------|
| 10201 | 参数错误 | 参考请求参数说明检查字段类型/命名是否正确后重试 |
| 429 | 触发 API 限流 | 告知用户当前请求过于频繁，降低调用频率后再重试，不要立即重试 |
| 20113 | 文档不存在 | 确认 `doc-id` 是否正确，文档可能已被删除或ID有误 |
| 10312 | 该用户在知识库不存在 | 确认申请对象 `target-username` 是否正确，或改用 `query-apply-member` 获取可申请对象 |
| 19003 | 人员无权限（申请对象无权授权） | 告知用户该申请对象无权处理此申请，需更换一个有权限的申请对象 |
| 60107 | 权限角色名称错误 | 检查 `apply-role-name` 是否为合法角色值（见[角色说明](#角色说明)） |

## CLI调用示例

```bash
# 为 zhangsan 申请文档可编辑权限
ku apply-member --doc-id WKoT7ltTnjU1oW --target-username zhangsan --apply-role-name DocMember

# 为 zhangsan 申请知识库只读权限，并附带申请原因
ku apply-member --repo-id repo_xxx --target-username zhangsan \
  --apply-role-name RepoReader --apply-message "需要查阅团队资料"
```

## 角色说明

| 场景 | 可选角色 |
|------|---------|
| 文档 | DocReader（只读/阅读）、DocMember（可编辑）、DocAdmin（管理员） |
| 知识库 | RepoReader（只读）、RepoMember（可编辑/成员）、RepoAdmin（管理员） |

## 典型用户 Prompt

| 用户 Prompt | Agent 处理方式 |
|---|---|
| 帮我申请这篇文档的阅读权限 | 意图明确，直接查询可申请对象（如未指定）并发起申请，返回申请结果 |
| 帮我把这些文档复制到我的知识库 | 若发现目标位置缺少编辑权限，先确认后再申请，不擅自跳过确认 |
