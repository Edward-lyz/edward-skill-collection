# get_datasheet_records - 获取数据表记录

查询数据表中的记录，支持分页、筛选、排序等多种查询条件。

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| --dist-id | string | 是 | - | 数据表ID |
| --view-id | string | 否 | null | 视图ID，不指定则使用默认视图 |
| --page-num | int | 否 | 1 | 页码，从1开始 |
| --page-size | int | 否 | 100 | 每页条数，范围1~1000 |
| --max-records | int | 否 | null | 最多返回记录数 |
| --sort | list | 否 | null | 排序条件数组 |
| --record-ids | list | 否 | null | 指定记录ID列表 |
| --fields | list | 否 | null | 限制返回的字段列表 |
| --filter | string | 否 | null | 智能公式筛选条件 |
| --cell-format | string | 否 | "json" | 单元格格式，"json"或"string" |
| --field-key | string | 否 | "name" | 字段标识类型，"name"或"id" |

### 排序参数说明 (sort)

JSON 数组格式：
```json
[{"field": "字段名称", "order": "asc"}, {"field": "字段名称", "order": "desc"}]
```

| 字段 | 说明 | 可选值 |
|------|------|--------|
| field | 排序字段 | 字段名称 |
| order | 排序方向 | `asc` 升序 / `desc` 降序 |

### 筛选公式说明 (filterByFormula)

支持智能公式语法，例如：
- `{字段名}="值"` - 等于
- `{字段名}!="值"` - 不等于
- `{字段名}>100` - 大于
- `{字段名}<100` - 小于
- `AND({条件1}, {条件2})` - 与
- `OR({条件1}, {条件2})` - 或

## 返回值说明

成功时返回：

```json
{
    "msg": "SUCCESS",
    "result": {
        "pageNum": 1,
        "pageSize": 2,
        "records": [
            {
                "createdAt": 1773914441000,
                "fields": {
                    "成员": [
                        {
                            "avatar": "https://ku.baidu-int.com/wiki/as/users/XoBS3OZRDJ/avatar",
                            "id": "1947281378740871170",
                            "name": "v_申佳怡",
                            "type": "Member",
                            "unitId": "54bc759f8a8f469bb8c6673dcf3b8aac"
                        }
                    ],
                    "标题": "测试标题1",
                    "选项": [
                        "A"
                    ]
                },
                "recordId": "recSmPFjuorW4",
                "updatedAt": 1773914856000
            },
            {
                "createdAt": 1773914441000,
                "fields": {
                    "成员": [
                        {
                            "avatar": "https://ku.baidu-int.com/wiki/as/users/vwgyJXRmo9/avatar",
                            "id": "1607941619916406786",
                            "name": "魏敏",
                            "type": "Member",
                            "unitId": "04dfd48f1cbe11eeaeaafa20202bc3bb"
                        }
                    ],
                    "标题": "测试标题2",
                    "选项": [
                        "B"
                    ]
                },
                "recordId": "recrB59TklpkK",
                "updatedAt": 1773914867000
            }
        ],
        "total": 2
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689805806015403008"
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
| result.total | int | 记录总数 |
| result.records | list | 记录列表 |
| result.records[].recordId | string | 记录唯一 ID |
| result.records[].createdAt | long | 记录创建时间（毫秒时间戳） |
| result.records[].updatedAt | long | 记录最后更新时间（毫秒时间戳） |
| result.records[].fields | object | 记录字段内容，key 为字段名，value 取决于字段类型 |

### fields 字段类型说明

| 字段类型 | 返回值类型 | 示例 |
|----------|------------|------|
| 文本/数字/日期等基础类型 | string / number | `"测试标题1"` |
| 单选 / 多选 | list\<string\> | `["A"]` |
| 成员字段 | list\<object\> | 见下方成员对象说明 |

**成员对象字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 成员用户 ID |
| name | string | 成员显示名称 |
| avatar | string | 成员头像 URL |
| type | string | 固定为 `"Member"` |
| unitId | string | 组织单元 ID |

## CLI调用示例

```bash
# 基础查询
ku get-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ

# 分页查询
ku get-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --page-num 1 --page-size 50

# 使用筛选和排序
ku get-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --filter '{标题}="测试"' --sort '[{"field": "创建时间", "order": "desc"}]'

# 限制返回字段
ku get-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --fields "标题,状态,负责人"
```

## 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查参数格式和类型 |
| 401 | 未授权 | 刷新token或检查认证配置 |
| 403 | 无权限 | 确认是否有数据表访问权限 |
| 404 | 数据表不存在 | 检查distId是否正确 |
| 500 | 服务器错误 | 稍后重试或联系管理员 |

## 注意事项

1. **分页限制**: pageSize最大为1000，建议使用100-500之间的值
2. **性能优化**: 使用fields参数限制返回字段，减少数据量
3. **筛选公式**: 复杂公式可能影响查询性能
4. **大数据量**: 记录数较多时，建议使用分页查询
5. **权限要求**: 需要对数据表有读取权限
6. **视图筛选**: 指定viewId时，会应用视图的筛选和排序规则

## 相关API

- [add_datasheet_record](./add_datasheet_record.md) - 添加数据表记录
- [update_datasheet_record](./update_datasheet_record.md) - 更新数据表记录
- [delete_datasheet_record](./delete_datasheet_record.md) - 删除数据表记录
- [get_datasheet_views](./get_datasheet_views.md) - 获取数据表视图
