# 更新文档成员权限

更新文档已有成员（用户或如流群）的访问权限。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 是 | 文档ID |
| username | string | 是 | 待更新的成员ID（用户UUAP或如流群ID） |
| role | string | 是 | 新的角色名称:DocReader、DocMember、DocAdmin。如流群成员不可设置为DocAdmin |
| member-type | string | 否 | 成员类型，默认user。user:用户，group:如流群 |

## 如流群名称解析

`--member-type group` 时，`--username` 必须是如流群ID（群号），**不能直接传群名称**：

- 用户提供如流群名称时，先使用 **企业搜索** 技能（enterprise-search）按群名称搜索如流群，解析出群号后再以群号作为 `--username` 调用
- 搜索无结果或命中多个群时，向用户展示候选群（群名称+群号）确认后再执行，不得猜测或默认取第一个
- 企业搜索不可用（未安装、不支持搜如流群、调用失败或超时）时，直接向用户说明并请其提供如流群ID（群号），不得重试轰炸或编造群号
- 禁止将群名称直接作为 `--username` 传入

**示例**（用户说"把「智能研发交流群」的权限改为只读"）：

```bash
# 1. 先通过企业搜索技能解析群名称：智能研发交流群 → 群号 12345678
# 2. 再用解析出的群号执行更新
ku update-member --doc-id WKoT7ltTnjU1oW --username 12345678 --role DocReader --member-type group
```

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "1xosIYvQX3qxeI",
        "success": true,
        "memberResultList": [
            {
                "memberType": 5,
                "memberGuid": "zhangsan"
            }
        ]
    },
    "traceId": "123456789012345678"
}
```

## CLI调用示例

```bash
# 将成员升级为可编辑权限
ku update-member --doc-id WKoT7ltTnjU1oW --username zhangsan --role DocMember

# 降级为只读
ku update-member --doc-id WKoT7ltTnjU1oW --username zhangsan --role DocReader

# 更新如流群成员权限
ku update-member --doc-id WKoT7ltTnjU1oW --username groupGuid123 --role DocReader --member-type group
```
