# 创建知识本

在指定知识库的目标目录下创建知识本（知识本是一种目录型文档，可用于组织和管理子文档）。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| repo-id | string | 是 | - | 知识库ID |
| create-mode | string | 否 | inherit | 创建模式："inherit"=权限继承, "public"=公开, "private"=保密 |
| username | string | 是 | - | 创建者用户名（邮箱前缀），传入当前用户 |
| parent-doc-id | string | 否 | 知识库根目录 | 目标上级目录ID（目录文档的ID，不是知识库ID） |
| title | string | 否 | 未命名知识本 | 知识本标题（名称冲突时自动递增编号后缀） |
| set-top | boolean | 否 | false | 是否置顶到当前目录 |

## 创建模式说明

- **"inherit"（权限继承，默认）**：知识库成员默认有权访问知识本及其子页面，子页面强制继承知识本权限
- **"public"（公开）**：知识本及其子页面默认企业内全员可见，⚠️ 存在信息泄露风险，执行前需向用户二次确认
- **"private"（保密）**：知识库成员默认无知识本及其子页面权限，仅对知识本内添加的成员可见

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "docGuid": "MTNldvOuF7nxqK",
        "parentDocGuid": "00000000000000",
        "repoName": "知识库SKILL默认知识库",
        "repositoryGuid": "E3d4LRExEl",
        "title": "未命名知识本(14)",
        "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/hAVa-nq7IH/E3d4LRExEl/MTNldvOuF7nxqK"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "746971116663487488"
}
```

## 响应字段说明

| 字段 | 说明 |
|---|---|
| returnCode / status / success | 状态标识，200 / true 表示创建成功 |
| msg / returnMessage | 响应描述信息，成功时为 "OK" |
| traceId | 链路追踪ID，用于问题排查 |
| result.docGuid | 新建知识本的文档ID，可作为 `parent-doc-id` 在其下创建子文档 |
| result.parentDocGuid | 父目录ID，`00000000000000` 表示知识库根目录 |
| result.repositoryGuid / repoName | 所属知识库 ID 与名称 |
| result.title | 知识本最终标题（名称冲突时服务端已追加编号后缀） |
| result.url | 新建知识本的访问链接 |

## 业务规则

1. **权限要求**：创建者需要在目标知识库中拥有【成员】或【管理员】权限，否则返回 60421 错误
2. **标题冲突**：同名知识本不会报错，服务端自动追加递增编号后缀（如"未命名知识本1"）
3. **目录语义**：知识本创建后即是一个目录文档，可继续通过 `create-doc --parent-doc-id <知识本ID>` 在其下创建子文档
4. **公开模式风险**：`create-mode=public` 创建的知识本企业内全员可见，Agent 执行前必须使用 `AskUserQuestion` 向用户确认

## CLI调用示例

```bash
# 在指定知识库根目录创建知识本（默认权限继承模式）
ku create-book --repo-id E3d4LRExEl --title "项目文档集"

# 在指定目录下创建保密知识本
ku create-book --repo-id E3d4LRExEl --parent-doc-id ParentDocId --title "内部资料" --create-mode private

# 创建公开知识本（需先向用户确认风险）
ku create-book --repo-id E3d4LRExEl --title "团队规范" --create-mode public

# 创建并置顶到当前目录
ku create-book --repo-id E3d4LRExEl --title "置顶知识本" --set-top

# 指定创建者
ku create-book --repo-id E3d4LRExEl --title "我的知识本" --username zhangsan
```
