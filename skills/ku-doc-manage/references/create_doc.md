# 创建文档

在指定知识库中创建新文档，支持三种创建模式。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| repo-id | string | 否* | - | 知识库ID（不提供则自动查询用户个人知识库） |
| username | string | 否 | - | 创建者用户名（邮箱前缀） |
| create-mode | string | 否 | content | 创建模式："empty"=空文档, "content"=指定内容, "copy"=复制文档 |
| parent-doc-id | string | 否 | null | 父目录ID（详见下方父目录识别规则） |
| title | string | 否 | null | 文档标题（不传则为"未命名文档"） |
| content | string | 否 | "" | 文档正文（create-mode=content时使用） |
| template-doc-id | string | 否** | null | 源文档ID（create-mode=copy时必填） |
| set-top | boolean | 否 | false | 是否置顶到当前目录 |
| process-images | boolean | 否 | true | 是否自动处理Markdown中的图片 |
| base-dir | string | 否 | null | 本地图片相对路径的基础目录 |
| md-file | string | 否 | null | 直接从本地Markdown文件读取内容（自动兼容 UTF-8 BOM / GBK 等编码） |

*不提供 repo-id 时，自动调用 query-user-info 获取用户个人知识库ID
**create-mode=copy 时必填

> ⚠️ **传参约定**
> - 布尔标志（`process-images`、`set-top`）传值**必须用等号形式**：`--process-images=true`。不能写成 `--process-images true`——空格后的 `true` 会被当作位置参数导致解析提前停止，**其后的 `--md-file` 等参数会被静默丢弃**（表现为文档创建成功但文件内容没写进去）。`process-images` 默认即为 `true`，可直接省略。
> - `--content` 的多行内容：换行写成字面 `\n`（CLI 自动还原为真实换行），**不要在命令行参数中传真实换行**（Windows 下 cmd.exe 会按换行截断命令，之后的内容全部丢失）。多行内容较长或含特殊字符时优先改用 `--md-file` 从文件读取。

## 父目录识别规则

- 用户提供了文档ID → 直接用作 `parent-doc-id`
- 用户提供了文档URL（4段path）→ 取最后一段作为 `parent-doc-id`
- 用户提供了知识库首页URL（3段path）或明确提到根目录 → `parent-doc-id` 固定为 `00000000000000`
- 用户明确提到目录，但未能找到对应文档 → 回退到个人知识库根目录下的「智能体创作空间」
- 未提及目录 → 默认写入个人知识库根目录下的「智能体创作空间」
- 当前会话存在最近一次明确、可唯一解析且未被否定的路径 → 优先复用该路径
- 个人知识库根目录不存在「智能体创作空间」→ 先创建该工作区，再以其为父文档创建新文档

> `parent-doc-id` 是目录文档的ID，不是知识库ID。创建完成后应返回文档标题、实际创建位置和链接，不要猜测位置。

## 创建模式说明

- **"empty"**：创建空文档，不需要额外参数
- **"content"**：指定内容创建，需提供 `content`（纯文本或Markdown）
- **"copy"**：复制现有文档，需提供 `template-doc-id`

## 流程图（draw.io）支持

`content` 参数支持插入 draw.io 格式（XML）流程图。**当用户要求插入流程图时，默认使用 draw.io 格式；仅当用户明确要求 mermaid 时才使用 mermaid。**

支持两种语法格式：

**HTML 格式（推荐）** — 使用 `<diagram>` 标签包裹 mxGraphModel XML：

```html
<diagram>
<mxGraphModel dx="1000" dy="600" ...>
<root>
<mxCell id="0"/>
<mxCell id="1" parent="0"/>
<!-- 节点和连线 -->
</root>
</mxGraphModel>
</diagram>
```

**Markdown 格式** — 使用 ` ```mxGraph ` 代码块包裹 mxGraphModel XML：

````markdown
```mxGraph
<mxGraphModel dx="600" dy="400" ...><root>...</root></mxGraphModel>
```
````

> 详细格式规范、硬性要求、布局参数及位置限制参见 `edit_content.md` 中的「流程图（draw.io）支持」章节。

## 图片处理说明

**自动检测规则**：当用户待写入的 `content` 中包含任意格式的图片时（包括 Markdown 图片 `![](url)`、HTML `<img>` 标签、Base64 内嵌图片等），`process_images` 自动设为 `true`，无需手动指定。

当 `process-images=true` (默认) 且 `create-mode=content` 时，会自动处理Markdown中的图片：

1. **处理流程**：先处理图片，再创建文档
2. **图片规则**：
   - 内部域名图片 (`rte.weiyun.baidu.com`): 跳过，保留原链接
   - 本地路径图片: 读取文件并上传
   - 外部URL图片: 下载后上传

使用 `base-dir` 参数可以指定基础目录，用于解析相对路径的本地图片。

## md-file 参数说明

当使用 `md-file` 参数时：

1. **自动读取文件内容**：从指定的 Markdown 文件读取内容作为 `content`
2. **自动设置 base_dir**：自动将 `base-dir` 设为文件所在目录，便于处理相对路径的本地图片
3. **自动推断标题**：如果未提供 `title`，将使用文件名（不含扩展名）作为文档标题
4. **自动兼容文件编码**：
   - 文件带 UTF-8 BOM → 自动去除 BOM
   - 文件为 GBK / GB2312 / GB18030 编码（Windows 记事本等默认保存格式）→ 自动转换为 UTF-8 后上传，无需手动转码
   - 无法识别的编码按原字节处理

## 响应示例

```json
{
    "returnCode": 200,
    "result": {
        "docGuid": "1xosIYvQX3qxeI",
        "repositoryGuid": "E3d4LRExEl",
        "title": "示例文档",
        "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/E3d4LRExEl/1xosIYvQX3qxeI",
        "processedContent": "处理后的Markdown内容（图片URL已替换，仅process_images=true时返回）",
        "imageUrls": {"./images/pic.png": "https://rte.weiyun.baidu.com/image/xxx"}
    }
}
```

## CLI调用示例

```bash
# 创建到个人知识库（推荐，无需指定 repo-id）
ku create-doc --title "我的笔记" --content "笔记内容"

# 创建到指定知识库的指定目录
ku create-doc --repo-id E3d4LRExEl --parent-doc-id ParentDocId --title "新文档"

# 直接从 Markdown 文件创建（推荐）
ku create-doc --md-file /path/to/document.md

# 创建空文档
ku create-doc --title "新空文档" --create-mode empty

# 置顶文档到目录顶部
ku create-doc --title "置顶文档" --content "内容" --set-top

# 如果图片在其他目录，可手动指定 base-dir
ku create-doc --title "带图片的文档" --content "# 标题\n\n![图片](./images/pic.png)" --base-dir /path/to/images
```