# 移动文档

将文档移动到指定知识库或目录。

## ⚠️ 风险操作提示

执行移动操作前，Agent **必须**使用 `AskUserQuestion` 工具向用户进行二次确认：

**确认问题示例**：
```
你正在移动文档，此操作可能打乱原有目录结构，且移动后无法自动恢复到原位置，请确认你已核对目标位置无误。是否确定继续？
```

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 待移动的源文档ID |
| target-repo-id | string | 是 | - | 目标知识库ID |
| username | string | 是 | 当前用户 | 操作者用户名 |
| parent-doc-id | string | 否 | 根目录 | 目标父目录ID |
| adjacent-doc-id | string | 否 | null | 目标相邻文档ID |
| upper | boolean | 否 | false | 是否移动到目标上方 |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "success": true,
        "docInfo": {
            "repositoryGuid": "E3d4LRExEl",
            "docGuid": "1xosIYvQX3qxeI",
            "name": "示例文档",
            "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/pKzJfZczuc/E3d4LRExEl/1xosIYvQX3qxeI",
            "type": 1,
            "childCount": 0,
            "created": 1640966400000,
            "publishTime": 1641052800000
        }
    },
    "traceId": "123456789012345678",
    "status": 200,
    "msg": "OK",
    "success": true
}
```

## CLI调用示例

```bash
# 移动文档到目标知识库根目录
ku move-doc --doc-id WKoT7ltTnjU1oW --target-repo-id E3d4LRExEl --username zhangsan

# 移动到指定父目录
ku move-doc --doc-id WKoT7ltTnjU1oW --target-repo-id E3d4LRExEl --parent-doc-id parent_doc_id --username zhangsan
```