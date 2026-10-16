# 查询用户个人知识库信息

查询指定用户的个人知识库信息,包括个人知识库ID等。当需要创建文档但不知道目标知识库ID时,可以使用此API获取用户的个人知识库ID。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名(邮箱前缀) |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "userGuid": "userGuid",
        "username": "zhangsan",
        "nickname": "张三",
        "email": "zhangsan@baidu.com",
        "userPersonalRepo": {
            "spaceGuid": "HFVrC7hq1Q",
            "groupGuid": "pKzJfZczuc",
            "repositoryGuid": "repositoryGuid",
            "name": "张三的知识库",
            "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/pKzJfZczuc/repositoryGuid",
            "ownerType": 5
        }
    }
}
```

## 返回字段说明

- `username`: 用户名
- `nickname`: 用户昵称
- `repositoryGuid`: **用户个人知识库ID** - 可用于创建文档到用户个人空间
- `userGuid`: 用户唯一标识

## CLI调用示例

```bash
# 查询当前用户信息（自动从环境变量获取用户名）
ku query-user-info

# 查询指定用户信息
ku query-user-info --username zhangsan
```