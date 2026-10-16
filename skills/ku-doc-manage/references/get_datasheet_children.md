# get-datasheet-children - 查询数据表表夹下子表

分页查询「数据表表夹」类型文档下的子表（数据表 / 仪表盘）列表。

> ⚠️ **使用限制**
>
> 此命令**仅在识别到数据表 URL 后可用**，用于查询该数据表所在表夹下的所有子表。
>
> - `--doc-id` 参数**必须从数据表 URL 中提取**（即 `?tb=...` 参数前的 path 段，表示数据表表夹所在文档）
> - **`--doc-id` 不是数据表 ID**：传入数据表自身的 `dist-id`（`tb=` 下划线前部分）会因类型不匹配而报错，必须传入表夹所在文档的 doc-id
> - 返回结果为当前用户**有权限访问**的子表（源数据分页后再做权限过滤），因此某页返回条数可能少于 `page-size`，属正常现象
>
> **错误示例**：使用 `tb=` 下划线前的 `dst...` 作为 `--doc-id` 调用此命令
> **正确用法**：先从用户提供的 `https://ku.baidu-int.com/knowledge/A/B/C?tb=xxx&type=dst` 中提取 `C` 作为 `--doc-id`（与 `create-datasheet` 一致）

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| --doc-id | string | 是 | - | 数据表表夹的文档ID（从数据表URL中提取，即 `?tb=` 前的 path 段） |
| --page-num | int | 否 | 1 | 分页页码，从1开始 |
| --page-size | int | 否 | 10 | 每页条数，最大100 |

## 返回值说明

成功时返回：

```json
{
    "msg": "SUCCESS",
    "result": {
        "pageNum": 1,
        "pageSize": 10,
        "hasMore": true,
        "currentCount": 2,
        "data": [
            {
                "nodeId": "dstxRvKjhSZZJDNvpZ",
                "nodeName": "项目任务表",
                "nodeType": 2,
                "nodeTypeDesc": "数据表"
            },
            {
                "nodeId": "dashbQwErTyUiOpLk",
                "nodeName": "项目仪表盘",
                "nodeType": 4,
                "nodeTypeDesc": "仪表盘"
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689806969574147072"
}
```

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"SUCCESS"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.pageNum | int | 当前页码 |
| result.pageSize | int | 每页条数 |
| result.hasMore | bool | 是否还有下一页（翻页依据） |
| result.currentCount | int | 当前页实际返回条数 |
| result.data | list | 子表列表（已按当前用户权限过滤） |
| result.data[].nodeId | string | 子节点ID，数据表为 `dst` 开头、仪表盘为 `dashb` 开头；数据表 ID 可直接用于字段/记录/视图等命令 |
| result.data[].nodeName | string | 子节点名称 |
| result.data[].nodeType | int | 节点类型：2=数据表，4=仪表盘 |
| result.data[].nodeTypeDesc | string | 节点类型描述，如 `"数据表"`/`"仪表盘"` |

## CLI调用示例

```bash
# 查询数据表表夹下的子表（默认第1页，每页10条）
ku get-datasheet-children --doc-id C

# 分页查询
ku get-datasheet-children --doc-id C --page-num 2 --page-size 50
```

## 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查 --doc-id 是否为「数据表表夹」类型文档的ID |
| 401 | 未授权 | 刷新token或检查认证配置 |
| 403 | 无权限 | 确认是否有该表夹的访问权限 |
| 404 | 文档不存在 | 检查 --doc-id 是否正确 |
| 500 | 服务器错误 | 稍后重试或联系管理员 |

## 注意事项

1. **文档类型**: `--doc-id` 必须是「数据表表夹」类型的文档，传入普通文档或数据表自身 ID 会报错
2. **翻页规则**: 以 `result.hasMore` 判断是否还有下一页，翻页时递增 `--page-num`；`--page-size` 最大 100
3. **权限过滤**: 返回结果已按当前用户权限过滤，某页条数（`currentCount`）可能小于 `page-size`，不能据此判断是否查完
4. **子表类型**: 表夹下除数据表（`nodeType=2`）外还可能有仪表盘（`nodeType=4`），两者均为子表；子表的数据表 ID 可用于 `get-datasheet-*` 系列命令

## 相关API

- [create_datasheet](./create_datasheet.md) - 在数据表表夹下创建新数据表
- [get_datasheet_views](./get_datasheet_views.md) - 获取数据表视图
- [get_datasheet_fields](./get_datasheet_fields.md) - 获取数据表字段
- [get_datasheet_records](./get_datasheet_records.md) - 获取数据表记录