# 导出在线表格为 Excel

## 功能说明

将知识库中的在线表格（Sheet）导出为 Excel 文件，并返回 Excel 文件的下载链接。

## CLI 命令

```bash
$SKILL_DIR/bin/ku export-sheet --doc-id <doc-guid>
# 或
$SKILL_DIR/bin/ku export-sheet --url <sheet-url>
```

## 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--doc-id` | 是（与 url 二选一） | 在线表格文档 ID | `WKoT7ltTnjU1oW` |
| `--url` | 是（与 doc-id 二选一） | 在线表格完整 URL | `https://ku.baidu-int.com/knowledge/repo/doc/sheet` |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "docGuid": "9a5cbba3a05f42",
        "downloadUrl": "https://ku-sheet-server.baidu-int.com/uploader/f/AIpYXIibM3pHkPDT.xlsx?accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6ImEwZTkyODg3MGJiZjRmNzRiMTFiYjUyODFhNDdjMzA0IiwiYXVkIjoiYWNjZXNzX3Jlc291cmNlIiwiZXhwIjoxNzc2OTE3MTA2LCJpYXQiOjE3NzY5MTY1MDYsInVzZXJJZCI6IjEwMDAwMDAwMTI4In0.upCTPtxLGIH1NHyhgsAsEmB_54t4H0bcJZr_Y7_z5Bc&download=1",
        "finished": true,
        "progress": 100,
        "taskId": null
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "702368100654014464"
}
```

## 关键字段说明

| 字段 | 说明 |
|------|------|
| `downloadUrl` | **Excel 文件下载链接**（核心字段，Agent 必须使用此链接下载文件） |

## Agent 处理指引

1. 获取 `downloadUrl` 后，必须使用该链接下载 Excel 文件
2. 可根据用户需求：
   - 直接返回下载链接给用户
   - 下载文件后读取内容并分析/展示给用户
3. 注意链接有效期较短，需及时下载

## 注意事项

1. 仅支持知识库中的在线表格类型文档
2. `doc-id` 和 `url` 参数至少需要提供一个
3. 导出的 Excel 文件通过临时链接提供，链接有效期较短，请及时下载

## 错误处理

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| 404 | 表格文档不存在 | 检查文档 ID 或 URL 是否正确 |
| 60414 | 获取在线表格数据需编辑权限 | 不要继续尝试导出，直接告知用户：获取在线表格数据需编辑权限，请开通后重试 |
| 60421 | 无权限访问该表格 | 确认当前用户是否有该文档的查看权限 |
| 500 | 服务端错误 | 稍后重试或联系管理员 |