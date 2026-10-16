# 上传文档附件

上传附件到指定的知识库文档，支持各种文件类型。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| file | string | 是 | - | 文件路径字符串，如 `"/path/to/file.pdf"` |

**file 参数说明**：
- **仅支持文件路径字符串**：传入文件的完整路径，函数会自动读取文件并提取文件名
- ❌ **不支持**：文件对象（open()返回）、字节流（bytes）等其他类型

## 响应示例

```json
{
  "returnCode": 200,
  "returnMessage": "OK",
  "result": {
    "docGuid": "rTgOMg1EhXhrC3",
    "attachId": "f49c39d17cc24d34ae3fef0ebf295fe3",
    "name": "4f0aa189-b877-42a9-bbdf-ced163b6e954.xlsx",
    "extension": "xlsx",
    "size": 3764
  },
  "traceId": "1967920467357294592",
  "status": 200,
  "msg": "OK",
  "success": true
}
```

## CLI调用示例

```bash
# 上传本地文件到指定文档
ku upload-attachment --doc-id WKoT7ltTnjU1oW --file /path/to/file.pdf

# 上传 Excel 文件
ku upload-attachment --doc-id WKoT7ltTnjU1oW --file /path/to/report.xlsx
```