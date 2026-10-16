# 查询知识库目录树结构

查询指定知识库的目录树结构。与 `query-repo`（分页列出某一层文档）不同，本命令按目录层级返回**树状结构**，可通过 `depth` 控制递归深度，一次性获取多层目录。

> 🚨 **深度默认只查一层（depth=1），不要擅自查全量**：用户未明确要求「完整目录树 / 所有层级 / 全部子目录 / 递归展开」时，**必须使用默认 `depth=1` 只查一层**，禁止自行改用 `depth=-1` 或更大深度。全量目录可能非常庞大、返回慢且触发 `DOWNLOAD` 模式，绝大多数「看看目录 / 有哪些文档 / 目录结构」类请求只需要一层即可。
> - ✅ 判定为「只查一层」（用 depth=1）：如"看下这个知识库的目录""有哪些文档""目录结构是怎样的""列一下下面的内容"
> - ⚠️ 仅在用户**明确表达全量意图**时才用 `depth=-1`：如"完整目录树""所有层级""把所有子目录都展开""递归列出全部"
> - 需要更深但非全量时，按用户说的层数设置具体 `depth`（如"展开两层"→`depth=2`），不要图省事直接 -1
> - 若一层结果中存在 `childCount>0` 的节点或 `hasMoreDescendants=true`，可告知用户"还有下级目录，需要展开可指定层级或查看某个子目录"，由用户决定是否深入，而非自动拉全量

> **快捷用法**：如果用户提供的是某个目录的文档 URL 或文档 ID，可直接从中解析出 `repo-id`（`repositoryGuid`）和 `parent-doc-id`（`docGuid`），无需用户单独传入。
>
> 知识库文档 URL 格式为：
> `https://ku.baidu-int.com/knowledge/{spaceGuid}/{categoryGuid}/{repositoryGuid}/{docGuid}`
>
> 示例：`https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/E3d4LRExEl/1xosIYvQX3qxeI`
> - `repo-id` = `E3d4LRExEl`（倒数第二段）
> - `parent-doc-id` = `1xosIYvQX3qxeI`（最后一段）

## 请求参数

`repo-id` 与 `parent-doc-id` **至少提供其一**即可定位查询范围。

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| repo-id | string | 否 | - | 知识库ID(repositoryGuid)，与 parent-doc-id 传一个即可 |
| depth | int | 否 | 1 | 查询的目录深度。**默认 1 只查一层，用户无明确全量意图时必须保持默认**；仅当用户明确要求完整目录树时才用 -1；需要指定层数时传具体数值（如 2） |
| parent-doc-id | string | 否 | - | 父文档ID，传代表查询该父文档的子目录；不传等价于根目录 `00000000000000` |

## 响应示例

```json
{
    "msg": "OK",
    "result": {
        "data": [
            {
                "childCount": 0,
                "children": [],
                "docGuid": "ECrcVtxIZ82_le",
                "name": "未命名",
                "parentDocGuid": "cghuZEnPCNfZGO",
                "type": 1,
                "typeDesc": "普通文档",
                "url": "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/hAVa-nq7IH/x4KQsIwk3I/ECrcVtxIZ82_le"
            }
        ],
        "dataMode": "INLINE",
        "depth": 1,
        "docCount": 1,
        "hasMoreDescendants": false,
        "parentDocGuid": "cghuZEnPCNfZGO",
        "repositoryGuid": "x4KQsIwk3I"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "741972587758973952"
}
```

## 响应字段说明

### result 顶层字段

| 参数名 | 类型 | 描述 |
|--------|------|------|
| repositoryGuid | string | 知识库ID |
| parentDocGuid | string | 父文档ID，查知识库根目录时返回 `00000000000000` |
| depth | int | 返回的目录深度 |
| docCount | int | 返回文档的数量 |
| hasMoreDescendants | bool | 是否还有未展开的目录（`true` 表示还有更深层级未返回） |
| dataMode | string | 返回的数据模式：`INLINE`=直接返回结果（默认）；`DOWNLOAD`=返回 BOS 下载链接 |
| data | array | INLINE 模式下的响应数据（目录/文档节点列表） |
| download | object | DOWNLOAD 模式下的响应数据 |

### data 节点字段（INLINE 模式）

| 参数名 | 类型 | 描述 |
|--------|------|------|
| repositoryGuid | string | 文档所属知识库ID |
| docGuid | string | 文档ID |
| parentDocGuid | string | 父文档ID |
| name | string | 文档标题 |
| type | int | 文档类型：1=普通文档，2=知识本目录，4=普通表格，6=PPT，7=数据表 |
| childCount | int | 当前文档的子文档数量，大于 0 表示该文档下还有子文档 |
| url | string | 文档链接 |
| children | array | 子节点列表（随 `depth` 递归展开） |

### download 字段（DOWNLOAD 模式）

| 参数名 | 类型 | 描述 |
|--------|------|------|
| url | string | 下载链接 |
| fileName | string | 文件名称 |
| contentType | string | 请求体的媒体类型 |
| expiresAt | string | 过期时间 |

## 结果汇总要点（面向用户输出）

汇总接口返回信息给用户时，需重点关注以下字段：

- **定位信息**：
  - 若 `parentDocGuid` **不等于** `00000000000000`，返回 `parentDocGuid` 信息（表示查询的是某个父文档下的子目录）
  - 若 `parentDocGuid` **等于** `00000000000000`，返回 `repositoryGuid` 信息（表示查询的是知识库根目录）
- **`docCount`**：返回的文档数量，用于概述本次目录规模
- **`dataMode`（决定如何读取目录数据）**：
  - `dataMode = INLINE`：直接读取 `data` 里的目录/文档节点内容
  - `dataMode = DOWNLOAD`：返回所有目录数据的 BOS 下载链接（`download.url`），需引导智能体读取该 BOS 文件链接以获取完整目录数据

## CLI调用示例

```bash
# 查询知识库根目录下一层目录
ku query-repo-dir --repo-id E3d4LRExEl

# 查询完整目录树（所有层级）
ku query-repo-dir --repo-id E3d4LRExEl --depth -1

# 查询指定父目录下的子目录树，深度 2 层
ku query-repo-dir --repo-id E3d4LRExEl --parent-doc-id 1xosIYvQX3qxeI --depth 2

# 仅凭父文档ID查询其子目录（repo-id 与 parent-doc-id 至少提供其一）
ku query-repo-dir --parent-doc-id 1xosIYvQX3qxeI
```
