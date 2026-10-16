# 查询知识库/文档权限申请列表

查询指定知识库或文档下，某个角色可发起申请的**目标对象列表**（即可以向谁申请该角色权限），用于 `apply-member` 申请前确定申请对象。

## 使用规则

- 返回的 `targetList` 是可申请对象列表，顺序与知识库前端展示逻辑一致；**未指定申请对象时，默认向列表第一个对象发起申请**。
- 通常作为 `apply-member` 的前置查询：先确定申请对象，再发起申请；若用户已明确指定申请对象（如具体用户名），可跳过此步骤直接调用 `apply-member`。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| repo-id | string | 条件必需 | 知识库ID，与 doc-id 二选一传入；若两者均传，以 doc-id 优先 |
| doc-id | string | 条件必需 | 文档ID，与 repo-id 二选一传入；若两者均传，以 doc-id 优先 |
| apply-role-name | string | 是 | 申请角色名称：知识库为 RepoAdmin/RepoMember/RepoReader；文档为 DocAdmin/DocMember/DocReader |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "targetList": [
            {
                "memberType": 5,
                "roleName": "DocAdmin",
                "username": "v_shenjiayi02"
            },
            {
                "memberType": 5,
                "roleName": "DocAdmin",
                "username": "v_liuxiao17"
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "734307739717180416"
}
```

## 响应字段说明

| 字段 | 说明 |
|---|---|
| result.targetList | 可申请对象列表，按推荐顺序排列 |
| targetList[].username | 申请对象的用户名，用于 `apply-member --target-username` |
| targetList[].roleName | 该对象当前拥有的角色 |
| targetList[].memberType | 成员类型（内部枚举值） |

## CLI调用示例

```bash
# 查询文档可编辑角色的可申请对象列表
ku query-apply-member --doc-id WKoT7ltTnjU1oW --apply-role-name DocMember

# 查询知识库管理员角色的可申请对象列表
ku query-apply-member --repo-id repo_xxx --apply-role-name RepoAdmin
```

## 角色说明

| 场景 | 可选角色 |
|------|---------|
| 文档 | DocReader（只读/阅读）、DocMember（可编辑）、DocAdmin（管理员） |
| 知识库 | RepoReader（只读）、RepoMember（可编辑/成员）、RepoAdmin（管理员） |

## 典型用户 Prompt

| 用户 Prompt | Agent 处理方式 |
|---|---|
| 帮我申请这篇文档的阅读权限 | 先调用 `query-apply-member` 获取可申请对象列表，默认取第一个对象，再调用 `apply-member` 发起申请 |
| 告诉我可以向谁申请这个知识库的权限 | 调用 `query-apply-member`，将 `targetList` 中的用户名返回给用户，由用户决定申请对象 |
