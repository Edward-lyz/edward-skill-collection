# upload-datasheet-attachment - 上传数据表附件

上传本地文件到数据表附件存储，返回可写入数据表附件字段的附件参数（如 `id`、`name`、`size`、`mimeType`、`token`、`url`，图片附件额外包含 `width`、`height`）。

> 注意：该命令只负责上传附件，不会直接修改数据表记录。如需把附件写入某条记录的附件字段，请先执行本命令获取附件参数，再参考 [update_datasheet_record.md](./update_datasheet_record.md) 调用 `update-datasheet-records` 更新目标记录。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dist-id | string | 是 | - | 数据表ID，对应接口表单字段 `distId` |
| file | string | 是 | - | 本地文件路径，对应接口表单文件字段 `file` |

**file 参数说明**：
- 仅支持本地文件路径字符串，命令会自动读取文件并作为 multipart file 上传。
- 每次请求只可上传一个附件；如需上传多份文件，需要重复调用本命令。
- 单个附件上传大小上限为 5MB，超过限制时上传会报错。
- 上传命令只返回附件参数，不会自动更新数据表记录。

## CLI 示例

```bash
ku upload-datasheet-attachment \
  --dist-id dst2dkRDo6AEJzFpZM \
  --file /Users/qinqin/Downloads/1.sql
```

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.id | string | 附件ID |
| result.name | string | 附件文件名 |
| result.size | number | 附件大小，单位字节 |
| result.mimeType | string | 附件 MIME 类型 |
| result.token | string | 附件 token，新增或更新记录附件字段时使用 |
| result.url | string | 附件访问地址 |
| result.width | number | 图片附件宽度，仅图片返回 |
| result.height | number | 图片附件高度，仅图片返回 |

## 重复上传与去重机制

附件接口内置重复文件识别去重机制：

- 首次上传：系统完整存储文件，生成唯一附件属性（含 `id`、`name`、`size`、`mimeType`、`token`、`url`，图片附件额外含 `width`、`height`）。
- 重复上传：系统通过文件内容哈希值识别重复文件（与文件名无关），不会重复存储文件内容；已生成的附件属性（如 `id`、`token`）不会更新，以保障附件属性的一致性与稳定性。

## 新增或更新数据表记录附件字段

上传成功后，从响应中取出 `mimeType`、`name`、`size`、`token`、`url` 等附件参数，可作为附件字段的值传给 `add-datasheet-records` 或 `update-datasheet-records`。

新增记录参数结构示例：

```json
{
  "distId": "dst2dkRDo6AEJzFpZM",
  "viewId": "viww2ircw1hng",
  "recordData": {
    "records": [
      {
        "fields": {
          "标题": "测试标题3",
          "附件": [
            {
              "mimeType": "application/octet-stream",
              "name": "1.sql",
              "size": 1918,
              "token": "space/2026/06/30/892545f4e5fa434099f1dfb2xxxxx3b33",
              "url": "https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfxxxxb33"
            }
          ]
        }
      }
    ]
  }
}
```

对应 CLI 示例：

```bash
ku add-datasheet-records \
  --dist-id dst2dkRDo6AEJzFpZM \
  --view-id viww2ircw1hng \
  --records '[{"fields":{"标题":"测试标题3","附件":[{"mimeType":"application/octet-stream","name":"1.sql","size":1918,"token":"space/2026/06/30/892545f4e5fa434099f1dfb2exxxx33","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfb2xxxx33"}]}}]'
```

更新已有记录时，需要在 `records` 中增加 `recordId`，并调用 `update-datasheet-records`。如果目标附件字段已有附件，默认按追加附件处理：先查询已有附件列表，再把已有附件和新增附件一起提交，避免覆盖原附件。如果用户明确希望覆盖附件字段，则可直接使用新增附件数据更新记录，无需查询已有附件：

```bash
ku get-datasheet-records \
  --dist-id dst2dkRDo6AEJzFpZM \
  --view-id viww2ircw1hng \
  --record-ids recaTsKD49BM8

ku update-datasheet-records \
  --dist-id dst2dkRDo6AEJzFpZM \
  --view-id viww2ircw1hng \
  --records '[{"recordId":"recaTsKD49BM8","fields":{"附件":[{"mimeType":"application/octet-stream","name":"已有附件.sql","size":1024,"token":"space/2026/06/30/existing-real-token","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/existing-real-token"},{"mimeType":"application/octet-stream","name":"1.sql","size":1918,"token":"space/2026/06/30/892545f4e5fa434099f1dfb2xxxxb33","url":"https://ku.baidu-int.com/vk-assets-ltd/space/2026/06/30/892545f4e5fa434099f1dfbxxxx3b33"}]}}]'
```

## 注意事项

- `upload-datasheet-attachment` 只负责上传附件并返回附件参数，不会直接插入数据表。
- 写入数据表记录时，可用于新增记录或更新已有记录，目标字段必须是数据表附件字段，否则记录接口可能返回字段类型错误。
- 每次请求只可上传一个附件；如需上传多份文件，需要重复调用本命令。
- 单个附件上传大小上限为 5MB，超过限制时上传会报错。
- 重复上传相同内容的文件时，接口会复用已生成的附件属性（如 `id`、`token`），不会因为文件名变化而重新生成。
- 如果同一附件字段已有内容，默认按追加附件处理：先查询记录并保留已有附件列表，再合并新增附件后使用 `update-datasheet-records` 一起提交，避免覆盖原附件。
- 如果用户明确希望覆盖附件字段，可直接用新增附件数据更新记录，无需查询已有附件。
- 提交新增或更新记录前，需要按 `token` + `url` 对附件列表去重；如果存在 `token` 和 `url` 都相同的重复附件，只保留一份。
- 附件字段中的 `token` 和 `url` 不允许省略或替换，必须使用上传附件接口或查询记录返回的真实值。
