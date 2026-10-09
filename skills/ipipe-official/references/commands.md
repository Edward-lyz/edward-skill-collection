# 命令参数完整参考

> 本文件列出所有命令的参数表和关键返回字段。
> 操作规范（执行步骤、输出模板）见各场景文件。

---

## pipeline 命令组

### pipeline list

```bash
ipipe-cli pipeline list --module <模块名>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名，如 `baidu/soqa/workflow-project` |

**关键返回字段**（`entities[]`）：

| 字段 | 说明 |
|------|------|
| `id` | 流水线 ID，即 `--pipeline-id` |
| `pipelineName` | 流水线名称 |
| `moduleName` | 模块名 |
| `isAggregation` | 是否聚合流水线 |
| `isTemplate` | 是否模板流水线 |

---

### pipeline config

```bash
ipipe-cli pipeline config --module <模块名>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名 |

**关键返回字段**（`entities[]`）：

| 字段 | 说明 |
|------|------|
| `id` | 流水线 ID |
| `name` | 流水线名称 |
| `stageConfBeans[].stageConfId` | 阶段配置 ID，可传给 `build status --stage-conf-id` |
| `workspaceId` | 工作空间 ID |

---

## trigger 命令组

### trigger start

```bash
ipipe-cli trigger start --pipeline-id <id> --branch <branch> [--param key=value ...]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pipeline-id` | int | 是 | 流水线 ID（来自 `pipeline list` 的 `entities[].id`） |
| `--branch` | string | 是 | 分支名，如 `master`、`stable` |
| `--param` | string | 否 | 自定义参数，格式 `key=value`，可多次指定 |

> `username` 自动从 UGate Token 解析，无需传入。

**关键返回字段**（`entities`）：

| 字段 | 说明 |
|------|------|
| `pipelineBuildId` | 流水线构建 ID，用于 `build status/tasks` |
| `stageBuildIds[]` | 各阶段构建 ID，用于 `build stage/retry` |
| `jobBuildIds[]` | 各任务构建 ID，用于 `build job/link/cancel` |
| `buildNumber` | 构建编号 |

---

### trigger run

```bash
ipipe-cli trigger run \
  --pipeline-id <id> \
  --revision <commitId或changeId> \
  [--branch <branch>] \
  [--event-type <NEW_COMMIT|GERRIT_CHANGE>] \
  [--param key=value ...]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pipeline-id` | int | 是 | 流水线 ID |
| `--revision` | string | 是 | commitId 或 changeId |
| `--branch` | string | 否 | 分支名 |
| `--event-type` | string | 否 | `NEW_COMMIT`（merge 合入）或 `GERRIT_CHANGE`（gerrit change） |
| `--param` | string | 否 | 自定义参数，格式 `key=value`，可多次指定 |

> `triggerUser` 自动从 UGate Token 解析。

**关键返回字段**：

| 字段 | 说明 |
|------|------|
| `success` | 是否触发成功 |
| `limited` | 是否被限流（true 时触发无效） |
| `pipelineBuildId` | 流水线构建 ID |
| `buildNumber` | 构建编号 |
| `errorMessage` | 失败原因 |

---

## build 查询命令

### build latest

```bash
ipipe-cli build latest --pipeline-id <id> [--limit <N>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pipeline-id` | int | 是 | 流水线 ID |
| `--limit` | int | 否 | 返回记录条数。接口默认 10 条；仅当需要超过 10 条时才传（如 `--limit 20`），传了会以 `_limit` 透传给服务端 |

返回各分支最新一次构建的数组，字段见下方 `build history` 公共字段。

---

### build history

```bash
ipipe-cli build history --module <模块名> [--limit <N>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名 |
| `--limit` | int | 否 | 返回记录条数。接口默认 10 条；仅当需要超过 10 条时才传（如 `--limit 20`），传了会以 `_limit` 透传给服务端 |

**公共构建记录字段**：

| 字段 | 说明 |
|------|------|
| `id` | pipelineBuildId |
| `buildNumber` | 构建编号 |
| `branch` | 分支 |
| `status` | 构建状态（见状态枚举表） |
| `buildTime`/`startTime` | 触发时间（毫秒时间戳） |
| `buildUrl` | Web 控制台链接 |
| `name` | 流水线名称 |
| `pipelineConfId` | 流水线配置 ID |

---

### build status

```bash
ipipe-cli build status --pipeline-build-id <id> [--stage-conf-id <stageConfId>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pipeline-build-id` | int | 是 | 流水线构建 ID（来自 `trigger run/start` 的 `pipelineBuildId`） |
| `--stage-conf-id` | int | 否 | 阶段配置 ID，仅查特定阶段（来自 `pipeline config` 的 `stageConfBeans[].stageConfId`） |

**关键返回字段**（`entities[]`，每项为一个阶段）：

| 字段 | 说明 |
|------|------|
| `id` | stageBuildId |
| `stageName` | 阶段名称 |
| `status` | 阶段状态 |
| `jobBuildBeans[]` | 该阶段下的任务列表 |
| `jobBuildBeans[].id` | jobBuildId |
| `jobBuildBeans[].jobName` | 任务名称 |
| `jobBuildBeans[].jobType` | 任务类型（见任务类型枚举表） |
| `jobBuildBeans[].status` | 任务状态 |
| `jobBuildBeans[].outParams` | 产出物参数（含 `AGILE_PRODUCT_HTTP_URL` 等） |

---

### build stage

```bash
ipipe-cli build stage --stage-build-id <id>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--stage-build-id` | int | 是 | 阶段构建 ID |

**关键返回字段**（`entities.realJobBuilds[][]`，二维数组）：

| 字段 | 说明 |
|------|------|
| `id` | jobBuildId |
| `jobName` | 任务名称 |
| `jobType` | 任务类型 |
| `status` | 任务状态 |
| `duration` | 耗时字符串（如 `41s`） |
| `logs[]` | 日志列表，`key=summary` 摘要日志，`key=dev` 详细日志 |
| `realJobBuild.productHttpUrl` | 产出物下载链接 |

---

### build tasks

```bash
ipipe-cli build tasks --pipeline-build-id <id>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pipeline-build-id` | int | 是 | 流水线构建 ID |

**关键返回字段**（`entities[]`）：

| 字段 | 说明 |
|------|------|
| `id` | jobBuildId |
| `jobName` | 任务名称 |
| `jobType` | 任务类型 |
| `status` | 任务状态 |
| `pipelineName` | 所属流水线名称 |
| `jobUrl` | 任务链接 |
| `outParams` | 产出物参数 |
| `realJobBuild` | 编译/部署详情 |

---

### build job

```bash
ipipe-cli build job --job-build-id <id>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--job-build-id` | int | 是 | 任务构建 ID（来自 `build stage/status/tasks` 的 id 字段） |

**关键返回字段**：

| 字段 | 说明 |
|------|------|
| `id` | jobBuildId |
| `pipelineBuildId` | 所属流水线构建 ID |
| `logs[]` | 日志列表 |
| `pluginJobBuild` | 编译详情（含 branch、compileBuildId、productHttpUrl 等） |

---

### build link

```bash
ipipe-cli build link --job-build-id <id>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--job-build-id` | int | 是 | 任务构建 ID |

返回：字符串 URL（iPipe Web 控制台链接）。

---

### build commit

```bash
ipipe-cli build commit --revision <commitId> --module <模块名> [--limit <N>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--revision` | string | 是 | commitId 或 changeId |
| `--module` | string | 是 | 模块名 |
| `--limit` | int | 否 | 返回记录条数。接口默认 10 条；仅当需要超过 10 条时才传（如 `--limit 20`），传了会以 `_limit` 透传给服务端 |

返回：构建记录数组（同 `build history` 字段）。

---

### build card

```bash
ipipe-cli build card --card <卡片标识> [--limit <N>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--card` | string | 是 | iCafe 卡片标识，如 `workflow-14923` |
| `--limit` | int | 否 | 返回记录条数。接口默认 10 条；仅当需要超过 10 条时才传（如 `--limit 20`），传了会以 `_limit` 透传给服务端 |

返回：构建记录数组，含 `commitBuildInfo` 字段（关联的 commit 信息）。

---

### build search

```bash
ipipe-cli build search --module <模块名> --pipeline-id <id> --card <iCafe卡片> [--limit <N>]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名，如 `baidu/soqa/workflow-project` |
| `--pipeline-id` | int | 是 | 流水线配置 ID（来自 `pipeline list` 的 `entities[].id`） |
| `--card` | string | 是 | iCafe 卡片标识，如 `mapcio-qatools-1381` |
| `--limit` | int | 否 | 候选构建最多扫描数（默认 30，上限 100）。越大查询越全但耗时越长 |

> 匹配逻辑：先通过卡片反查或最近构建列表过滤出目标 pipeline 的候选，再逐条查构建详情中 `stageBuilds[].inParams/outParams` 里的 `AGILE_ICAFE_ISSUE_KEYS` 字段做精确卡片匹配。

**关键返回字段**（`entities[]`）：

| 字段 | 说明 |
|------|------|
| `pipelineBuildId` | 流水线构建 ID |
| `buildNumber` | 构建编号 |
| `branch` | 分支 |
| `status` | 构建状态（见状态枚举表） |
| `name` | 流水线名称 |
| `buildTime` | 触发时间（毫秒时间戳） |
| `buildUrl` | Web 控制台链接 |
| `icafeKeys` | 命中的 AGILE_ICAFE_ISSUE_KEYS 原值 |
| `matchedStageBuildId` | 命中的阶段构建 ID |

---

## build 操作命令

### build cancel

```bash
ipipe-cli build cancel --job-build-id <id>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--job-build-id` | int | 是 | 任务构建 ID |

> ⚠️ 需 HARD-GATE-3 二次确认，`username` 自动从 UGate Token 解析。

---

### build retry

```bash
ipipe-cli build retry --stage-build-id <id> [--param key=value ...]
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--stage-build-id` | int | 是 | 阶段构建 ID |
| `--param` | string | 否 | 自定义参数，格式 `key=value`，可多次指定 |

> ⚠️ 需 HARD-GATE-3 二次确认，`username` 自动从 UGate Token 解析。

---

## branch 命令组

### branch builds

```bash
ipipe-cli branch builds --module <模块名>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名，如 `baidu/soqa/workflow-project` |

**关键返回字段**（数组项）：

| 字段 | 说明 |
|------|------|
| `compileBuild.id` | 编译构建 ID，即 `branch create --build-id` |
| `revision` | 构建 revision，即 `branch create --revision` |
| `compileBuild.branch` | 构建分支 |
| `compileBuild.buildStatus` | 构建状态 |
| `comment` | 构建备注 |
| `tagTime` | 构建时间，毫秒时间戳 |

---

### branch create

版本号命名创建：

```bash
ipipe-cli branch create \
  --module <模块名> \
  --scm-mode version \
  --build-id <compileBuildId> \
  --revision <revision> \
  [--remarks <备注>]
```

自定义名称创建：

```bash
ipipe-cli branch create \
  --module <模块名> \
  --scm-mode custom \
  --build-id <compileBuildId> \
  --revision <revision> \
  --branch <分支名>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--module` | string | 是 | 模块名 |
| `--scm-mode` | string | 是 | 创建方式：`version` 或 `custom` |
| `--build-id` | int | 是 | 编译构建 ID，来自 `branch builds` 的 `compileBuild.id` |
| `--revision` | string | 是 | 构建 revision，来自 `branch builds` 的 `revision` |
| `--branch` | string | custom 必填 | 自定义分支名，仅 `custom` 模式使用 |
| `--remarks` | string | 否 | 分支备注，仅 `version` 模式可用 |

> `version` 模式会由 CLI 内部自动获取版本号，不暴露独立版本号命令。
> `branch create` 是非交互式命令，不读取 stdin；固定选择模板和二次确认由 Skill/Agent 层完成。
> `branch create` 会先查询代码库配置并校验工作流类型，非 `SCM_FLOW` 时返回 `unsupported_workflow`，不要继续创建。

---

## 枚举值

### 构建状态（status）

| 原始值 | 中文展示 |
|--------|---------|
| `SUCCEEDING` / `SUCC` | ✅ 成功 |
| `FAILING` / `FAIL` | ❌ 失败 |
| `RUNNING` | ⏳ 进行中 |
| `WAITING` | ⏸️ 等待中 |
| `CANCELLED` / `CANCEL` | 已取消 |
| `SKIP` | ⏭️ 跳过 |

### 任务类型（jobType）

| 原始值 | 简称 |
|--------|------|
| `AGILE_COMPILE` | 编译 |
| `AGILE_SHELL` | 脚本 |
| `AGILE_DEPLOY` | 部署 |
| `AGILE_TEST` | 测试 |
| 其他 | 直接展示原值 |
