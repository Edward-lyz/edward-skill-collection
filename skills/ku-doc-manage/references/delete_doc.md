# 删除文档

根据文档ID删除指定文档。

## ⚠️ 风险操作提示

执行删除操作前，Agent **必须**使用 `AskUserQuestion` 工具向用户进行二次确认：

**确认问题示例**：
```
你正在删除文档，请确认你已备份或不再需要该文档。是否确定继续？
```

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 要删除的文档ID |
| username | string | 是 | 当前用户 | 操作者用户名 |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "success": true
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "123456789012345678"
}
```


## CLI调用示例

```bash
# 删除文档
ku delete-doc --doc-id WKoT7ltTnjU1oW --username zhangsan
```

## 注意事项

1. 删除操作不可恢复，请谨慎操作
2. 需要有该文档的删除权限
3. 如果文档有子文档，此操作只删除父文档本身