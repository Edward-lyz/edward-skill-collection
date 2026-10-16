# 添加文档成员

为文档添加成员并设置访问权限，支持用户和如流群混合添加。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| member-list | JSON数组 | 是 | - | 官方格式成员列表，元素为 `{"memberType": "user"或"group", "memberGuid": "用户名或群ID"}`，支持混合添加不同类型成员 |
| role | string | 否 | DocReader | 角色名称:DocReader(可读)、DocMember(可编辑)、DocAdmin(管理员)。如流群成员不可设置为DocAdmin |

> memberType 支持 `user`（用户，等价于旧接口的5）和 `group`（如流群，等价于旧接口的10）两种取值，CLI层会自动转换为后端所需的数字。
> CLI 另外支持 `--usernames`（逗号分隔用户名列表）作为兼容旧格式的参数，用于兼容历史脚本；SKILL 场景下只需使用 `member-list`。

## 如流群名称解析

`memberType=group` 的 `memberGuid` 必须是如流群ID（群号），**不能直接传群名称**：

- 用户提供如流群名称时，先使用 **企业搜索** 技能（enterprise-search）按群名称搜索如流群，解析出群号后再构造 `member-list`
- 搜索无结果或命中多个群时，向用户展示候选群（群名称+群号）确认后再执行，不得猜测或默认取第一个
- 企业搜索不可用（未安装、不支持搜如流群、调用失败或超时）时，直接向用户说明并请其提供如流群ID（群号），不得重试轰炸或编造群号
- 禁止将群名称直接作为 `memberGuid` 传入

**示例**（用户说"把「智能研发交流群」加为可读"）：

```bash
# 1. 先通过企业搜索技能解析群名称：智能研发交流群 → 群号 12345678
# 2. 再用解析出的群号执行添加
ku add-member --doc-id WKoT7ltTnjU1oW --member-list '[{"memberType":"group","memberGuid":"12345678"}]' --role DocReader
```

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "memberResultList": [
            {
                "eventGuid": "71632de6fc",
                "memberGuid": "zhangsan",
                "memberType": 5,
                "roleName": null
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "735788538791206912"
}
```

## CLI调用示例

```bash
# 添加只读成员（默认 DocReader）
ku add-member --doc-id WKoT7ltTnjU1oW --member-list '[{"memberType":"user","memberGuid":"zhangsan"},{"memberType":"user","memberGuid":"lisi"}]'

# 添加可编辑成员
ku add-member --doc-id WKoT7ltTnjU1oW --member-list '[{"memberType":"user","memberGuid":"zhangsan"}]' --role DocMember

# 混合添加用户与如流群成员
ku add-member --doc-id WKoT7ltTnjU1oW --member-list '[{"memberType":"user","memberGuid":"zhangsan"},{"memberType":"group","memberGuid":"groupGuid123"}]' --role DocReader
```
