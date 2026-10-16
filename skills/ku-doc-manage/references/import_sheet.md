# 导入 Excel 为在线表格

## 功能说明

将本地 Excel 文件（.xlsx, .xls, .csv, .xlsm 格式）上传到知识库，并导入为在线表格文档。

## CLI 命令

```bash
$SKILL_DIR/bin/ku import-sheet --repo-id <repo-guid> --file <excel-file-path>
```

## 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--repo-id` | 是 | 目标知识库 ID | `bXxYz123456` |
| `--file` | 是 | 本地 Excel 文件路径 | `./data.xlsx` |
| `--parent-doc-id` | 否 | 上级目录 ID，不传则导入到根目录 | `WKoT7ltTnjU1oW` |
| `--title` | 否 | 表格名称，不传则使用文件原名 | `销售数据表` |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "3ecc686e297044",
        "taskId": "QxIY9MuWjQeQThhF",
        "progress": 100,
        "status": 0,
        "docInfo": {
            "repositoryGuid": "x4KQsIwk3I",
            "docGuid": "3ecc686e297044",
            "name": "【导入】😊报名及信息收集组件😭_填报统计_全部用户_20251120 (1)",
            "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/hAVa-nq7IH/x4KQsIwk3I/3ecc686e297044",
            "type": 4,
            "childCount": 0,
            "created": 1776862355000,
            "publishTime": 1776862355000
        },
        "finished": true
    },
    "traceId": "702139719391885312",
    "status": 200,
    "msg": "OK",
    "success": true
}
```

## 关键字段说明

| 字段 | 说明 |
|------|------|
| `result.docInfo.url` | **新创建的表格文档访问链接**（核心字段，需要返回给用户） |
| `result.docInfo.name` | 表格文档名称 |

## 注意事项

1. 支持 `.xlsx`、`.xls`、`.csv`、`.xlsm` 格式的文件
2. 导入的文件大小不能超过200个单元格限制
3. 复杂的 Excel 格式（如合并单元格、复杂公式）可能会有兼容性问题
4. 导入操作需要目标知识库的创建文档权限

## 权限要求

- 执行用户需要在目标知识库中具有「成员」或「管理员」权限
- 如无权限，将返回 60421 错误码

## 错误处理

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| 61005 | 文件格式错误或文件为空 | 检查文件是否为有效的 .xlsx/.xls/.csv/.xlsm 格式 |
| 60421 | 无权限访问或创建文档 | 联系知识库管理员添加权限 |
| 500 | 服务端错误 | 稍后重试或联系管理员 |

## 示例

```bash
# 导入到知识库根目录
$SKILL_DIR/bin/ku import-sheet --repo-id bXxYz123456 --file ./sales_data.xlsx

# 导入到指定目录并设置名称
$SKILL_DIR/bin/ku import-sheet --repo-id bXxYz123456 --file ./sales_data.xlsx --parent-doc-id WKoT7ltTnjU1oW --title "2024年销售数据"
```