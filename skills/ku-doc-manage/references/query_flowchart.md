# 导出流程图数据

导出文档中指定流程图的原始数据(mxGraph格式的XML文本)。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| flowchart-id | string | 是 | - | 流程图ID |

## 自动获取流程图ID（用户未提供时）

若用户只提供了文档ID/URL，**未提供 flowchartId**，按以下步骤自动推导：

**Step 1**：用 `protocol=json` 查询文档编辑器JSON，获取文档结构化内容：

```bash
ku query-content --doc-id <docId> --protocol json
```

**Step 2**：在返回的 `result.content` 数组中，找出所有 `"type": "diagram"` 的 block，提取其中的 `id` 字段。

编辑器JSON中流程图block结构示例：

```json
{
  "type": "diagram",
  "id": "1338847479f84644a8efb69a7eb4ffde",
  "blockId": "docyg-c6b7c290-3afb-11f1-a0ae-e15964f18260",
}
```

**Step 3**：
- 若文档中**只有一个**流程图，直接使用该 `id` 调用导出接口
- 若文档中**有多个**流程图，对每个 `id` 依次调用导出接口，汇总所有结果后一并返回给用户
- 若文档中**没有**流程图，提示用户该文档不包含流程图

## 响应示例

```json
{
  "returnCode": 200,
  "returnMessage": "SUCCESS",
  "result": {
    "docGuid": "doc_id",
    "flowchartId": "flowchart_id",
    "content": "<mxGraphModel>...</mxGraphModel>"
  }
}
```

## CLI调用示例

```bash
# 已知流程图ID，直接导出
ku query-flowchart --doc-id WKoT7ltTnjU1oW --flowchart-id flowchart_123

# 未知流程图ID时，先查文档JSON，从 type=diagram 的 block 中提取所有 id，再逐一导出
ku query-content --doc-id WKoT7ltTnjU1oW --protocol json
# 假设找到两个流程图 id1 和 id2，依次请求：
ku query-flowchart --doc-id WKoT7ltTnjU1oW --flowchart-id <id1>
ku query-flowchart --doc-id WKoT7ltTnjU1oW --flowchart-id <id2>
```