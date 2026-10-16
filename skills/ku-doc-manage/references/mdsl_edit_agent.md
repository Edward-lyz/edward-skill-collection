# mdsl 局部编辑 Agent 指南

本文档是 `editor-mode=mdsl` 模式的使用指南，定义决策规则和约束条件。本文档不直接暴露为 CLI 命令，仅当使用 `ku edit-content --editor-mode mdsl` 时参考。API 参数格式请参考 [edit_content.md](edit_content.md)。

## 工作流程

```bash
# 1. 获取文档内容（使用 mdhtml 协议）
ku query-content --doc-id <DOC_ID> --protocol mdhtml

# 2. 根据用户需求生成编辑指令
ku edit-content --doc-id <DOC_ID> --username <USERNAME> --editor-mode mdsl --operation '<JSON>'
```

## 文档格式说明

原文档为 Markdown + HTML 混合格式，常见元素：

| 类型 | 示例 |
|------|------|
| Markdown | 标题、段落、列表、引用、代码块、链接、图片、加粗、斜体、Markdown 表格 |
| HTML 表格 | `<table><tr><td>…</td></tr></table>` |
| 高亮块 | `<callout><p>…</p></callout>` |
| 布局容器 | `<block>` / `<timeline>`，内部常有 `<cell><p>…</p></cell>` |
| 富格式 | @人、文档预览、外链预览、统计、随心搭、目录、三方嵌入等 |

## 定位规则

### selectionWithEllipsis（按内容定位）

1. **精确定位**：填写完整文本
   - 适合短文本、单行内容

2. **省略定位**：`首部10-20字...尾部10-20字`
   - 用于较长文本块，首尾需能唯一定位目标

**转义**：内容本身包含 `...` 时，用 `\.\.\.` 表示字面量。

**约束**：定位对象必须是完整块/行；定位串必须唯一，不唯一时扩展上下文。

### selectionByTitle（按标题定位）

格式：`## 章节标题`（可带或不带 `#` 前缀）

自动定位整个章节（从该标题到下一个同级或更高级标题之前）。

**示例**：
- `## 功能说明` → 定位二级标题"功能说明"及其下所有内容
- `功能说明` → 定位任意级别的"功能说明"标题及其内容

**约束**：替换时 `markdown` 字段必须包含标题本身，而不是只写新内容。

**适用场景**：替换或删除整节内容时使用。

## 核心约束

1. **定位以块为单位**：块 = 段落/标题/列表项/代码块/完整 `<tr>`/`<td>`/`<cell>`。禁止定位块内局部文本；即使只改一个词，也要定位整个块，`markdown` 输出修改后的完整块。

2. **插入只能在完整块前后**：不支持在单个 `<td>` 或 `<cell>` 前后插入。表格新增行时，在完整 `<tr>` 前后插入。

3. **删除以完整块为单位**：不支持单独删除 `<td>` 或 `<cell>`，否则可能导致结构错乱。

4. **替换前后标签一致**：`<tr>` → `<tr>`；`<td>` → `<td>`；`<cell>` → `<cell>`。替换 `<tr>` 时新旧行的 `<td>` 数量应一致。

5. **markdown 支持范围**：标准 Markdown 和部分 HTML（`<p>`/`<h1>`~`<h6>`/`<table>`/`<tr>`/`<td>`）。

## 表格修改速查

| 需求 | 推荐做法 | 避免做法 |
|------|----------|----------|
| 末尾加行 | `insert_after` 定位最后一个 `<tr>` | 替换整表 |
| 某行前后插行 | `insert_before/after` 定位目标 `<tr>` | 定位 `<td>` 插入 |
| 删除某行 | `delete_range` 定位完整 `<tr>` | 删除单个 `<td>` |
| 修改单元格 | `replace_range` 定位完整 `<td>` | 只替换单元格内文本 |
| 修改一行多个值 | `replace_range` 定位完整 `<tr>` | 替换整表 |
| 替换整表 | 仅用户明确要求时替换完整 `<table>` | 默认整表替换 |

## 决策流程

1. **判断意图**：向前插入 / 向后插入 / 删除 / 替换
2. **判断范围**：段落 / 标题 / 列表项 / 整节 / 表格单元格 / 表格行 / 整表 / 容器块
3. **选择定位方式**：整节用 `selectionByTitle`，其它用 `selectionWithEllipsis`
4. **选择最小安全块**
5. **检查操作限制**
6. **无法定位或执行**：输出 `# ERROR: <原因>`

## CLI调用示例

### 段内文字修正

需求：把"200ms"改成"50ms"（必须定位整段）

```bash
ku edit-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --editor-mode mdsl \
  --operation '{"mode":"replace_range","selectionWithEllipsis":"模块初始化流程目前依赖配置文件 A，加载耗时约 200ms。","markdown":"模块初始化流程目前依赖配置文件 A，加载耗时约 50ms。"}'
```

### 表格末尾新增一行

```bash
ku edit-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --editor-mode mdsl \
  --operation '{"mode":"insert_after","selectionWithEllipsis":"<tr><td>v2.0</td>...架构升级 @张三</td></tr>","markdown":"<tr><td>v2.1</td><td>2026-05-08</td><td>修复登录 bug</td></tr>"}'
```

### 修改单元格

```bash
ku edit-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --editor-mode mdsl \
  --operation '{"mode":"replace_range","selectionWithEllipsis":"<td>10w</td>","markdown":"<td>12.3w</td>"}'
```

单元格不唯一时替换整行：

```bash
ku edit-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --editor-mode mdsl \
  --operation '{"mode":"replace_range","selectionWithEllipsis":"<tr><td>DAU</td><td>10w</td><td>9.5w</td></tr>","markdown":"<tr><td>DAU</td><td>12.3w</td><td>9.5w</td></tr>"}'
```

### 替换整节内容

```bash
ku edit-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --editor-mode mdsl \
  --operation '{"mode":"replace_range","selectionByTitle":"## 项目背景","markdown":"这是替换后的新内容"}'
```

### 无法唯一定位

```bash
# ERROR: 无法唯一定位目标块，请提供更明确的上下文或目标段落
```

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result": {
        "docGuid": "WSuIrx09hfg6zr",
        "success": true
    },
    "traceId": "694507417572758528",
    "status": 200,
    "msg": "OK",
    "success": true
}
```

## 输出规范

- 仅输出 CLI 指令，不要解释、寒暄
- doc-id 未提供时用 `<DOC_ID>` 占位
- 错误格式：`# ERROR: <原因>`（无法执行时输出）
- 多步操作输出多条指令，指令之间空行分隔

## 常见错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 定位失败（不唯一） | selectionWithEllipsis 匹配到多个位置 | 扩展上下文，包含更多前后文字 |
| 定位失败（不存在） | 原文已变化或定位串有误 | 重新 `query-content` 获取最新内容 |
| 替换后结构错乱 | 标签不一致 | 确保 `<tr>` 替换为 `<tr>`，`<td>` 替换为 `<td>` |
| 插入位置错误 | 定位了 `<td>` 或 `<cell>` 内部 | 改为定位完整 `<tr>` 或外层块 |
