# 修改文档公开范围

修改文档的公开范围设置。

## ⚠️ 风险操作提示

当修改公开范围为 **公开可读（scope=public-read）** 或 **公开可编辑（scope=public-edit）** 时，
Agent **必须**使用 `AskUserQuestion` 工具向用户进行二次确认：

**确认问题示例**：
```
你正在将文档设为公开，公开后公司全员可见，存在信息泄露风险，请确认文档不包含敏感信息。是否确定继续？
```

**scope=private（私密）** 不需要二次确认。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 是 | 文档ID |
| scope | string | 是 | 权限范围："public-read"=公开可读, "public-edit"=公开可编辑, "private"=私密 |
| username | string | 否 | 操作者用户名,不传则使用ak对应的用户名 |

## 响应示例

```json
{
  "returnCode": 200,
  "returnMessage": "SUCCESS",
  "result": {}
}
```

## CLI调用示例

```bash
# 设为公开可读
ku change-scope --doc-id WKoT7ltTnjU1oW --scope public-read

# 设为公开可编辑
ku change-scope --doc-id WKoT7ltTnjU1oW --scope public-edit

# 设为私密
ku change-scope --doc-id WKoT7ltTnjU1oW --scope private
```