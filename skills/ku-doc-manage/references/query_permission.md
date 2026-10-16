# 查询用户对文档的权限

查询指定用户列表对某个文档的访问权限。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 是 | 文档ID |
| usernames | array | 是 | 用户名列表(邮箱前缀) |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "1xosIYvQX3qxeI",
        "permissionDetails": [
            {
                "username": "zhangsan",
                "canRead": true,
                "canUpdate": false
            },
            {
                "username": "lisi",
                "canRead": true,
                "canUpdate": true
            }
        ]
    },
    "traceId": "123456789012345678"
}
```

## CLI调用示例

```bash
# 查询单个用户权限
ku query-permission --doc-id WKoT7ltTnjU1oW --usernames zhangsan

# 查询多个用户权限（逗号分隔）
ku query-permission --doc-id WKoT7ltTnjU1oW --usernames zhangsan,lisi
```
## 权限角色说明

| 角色名称 | canRead | canUpdate | 说明 |
|----------|---------|-----------|------|
| DocReader | ✓ | ✗ | 只读成员,可查看文档 |
| DocMember | ✓ | ✓ | 可编辑成员,可查看、编辑文档 |
| DocAdmin | ✓ | ✓ | 页面管理员,可查看、编辑、管理文档和成员 |
