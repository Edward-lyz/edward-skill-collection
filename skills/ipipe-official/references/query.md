# 查询操作

> 本文件包含所有查询场景的执行步骤和关键返回字段说明。
> 输出风格自由，提炼关键信息展示即可，无需固定模板。
> ID 解析链见 [SKILL.md](../SKILL.md#id-自动解析链)。

---

## 通用 ID 推导原则

各场景执行前，若所需 ID 缺失，优先从用户已提供的信息推导，**不要直接报错让用户去找 ID**：

- 需要 `pipeline-id`，用户给了模块名 → `pipeline list --module <模块名>`
- 需要 `pipeline-build-id`，用户给了模块名 → `build history --module <模块名>` 取最近一条
- 需要 `pipeline-build-id`，用户给了模块名+分支 → `build latest --pipeline-id <id>` 按分支过滤
- 需要 `pipeline-build-id`，用户给了 commitId → `build commit --revision <id> --module <模块名>`
- 需要 `pipeline-build-id`，用户给了卡片号 → `build card --card <card>`
- 需要 `stage-build-id`，用户给了 `pipelineBuildId` → `build status --pipeline-build-id <id>` 按条件定位阶段
- 需要 `job-build-id`，用户给了 `pipelineBuildId` → `build tasks --pipeline-build-id <id>`
- 需要 `job-build-id`，用户给了 `stageBuildId` → `build stage --stage-build-id <id>`

---

## 场景一：查询模块下的流水线列表

**适用**：用户问"XX 模块有哪些流水线"、"帮我看看 workflow-project 的流水线"等。

### 执行步骤

```bash
ipipe-cli pipeline list --module <模块名>
```

### 返回字段说明


```
模块 {module} 的流水线列表：
· {pipelineName}（ID: {id}）{聚合标记}
· {pipelineName}（ID: {id}）
...

共 {N} 条。可用 ID 触发构建，例如：ipipe-cli trigger start --pipeline-id {id} --branch master
```

**格式规则**：
- `isAggregation: true` → 名称后追加 `[聚合]`
- `isTemplate: true` → 名称后追加 `[模板]`
- 无数据 → 回复"该模块暂无流水线，请确认模块名是否正确"

---

## 场景二：获取流水线配置信息

**适用**：用户问"流水线有哪些阶段"、"帮我查一下流水线配置"、需要 stageConfId 时。

### 执行步骤

```bash
ipipe-cli pipeline config --module <模块名>
```

### 返回字段说明


```
模块 {module} 的流水线配置：

{pipelineName}（流水线 ID: {id}）
  阶段配置：
  · 阶段 {stageConfId}
  · 阶段 {stageConfId}
  ...
```

---

## 场景三：查询流水线各分支最新一次构建

**适用**：用户问"最新构建状态怎么样"、"pipeline 最近跑了没"等，且已知 pipeline-id。

若用户只提供模块名未提供 pipeline-id，先执行场景一，从结果中确认目标流水线再继续。

### 执行步骤

```bash
ipipe-cli build latest --pipeline-id <id>
```

### 返回字段说明


```
流水线 {pipeline-id} 各分支最新构建：
· {branch}  #{buildNumber}  {status中文}  {startTime格式化}  [查看]({buildUrl})
· {branch}  #{buildNumber}  {status中文}  {startTime格式化}
...
```

**格式规则**：
- `status` 映射：`SUCCEEDING`=成功，`FAILING`=失败，`RUNNING`=进行中，`WAITING`=等待中，`CANCELLED`=已取消
- `startTime` 为毫秒时间戳，转为 `M.D HH:mm` 格式（如 `4.9 18:30`）
- `buildUrl` 存在时展示 `[查看]({buildUrl})` 链接，否则不展示
- 无数据 → 回复"该流水线暂无构建记录"

---

## 场景四：获取模块最近构建记录

**适用**：用户问"最近跑了哪些构建"、"模块的构建历史"等。

### 执行步骤

```bash
ipipe-cli build history --module <模块名>
```

### 返回字段说明


```
模块 {module} 最近构建记录：
· #{buildNumber}  {pipelineName}  {branch}  {status中文}  {buildTime格式化}  [查看]({buildUrl})
· #{buildNumber}  {pipelineName}  {branch}  {status中文}  {buildTime格式化}
...
```

**格式规则**：
- `buildTime` 为毫秒时间戳，转为 `M.D HH:mm` 格式
- `buildUrl` 存在时展示链接，否则不展示
- 接口默认返回 10 条，**不传 `--limit` 即为默认 10 条**；用户明确要看更多（超过 10 条）时才追加 `--limit <N>`（N > 10），如 `ipipe-cli build history --module <模块名> --limit 20`

---

## 场景五：查询流水线构建详情（含各阶段任务状态）

**适用**：用户问"构建状态怎么样"、"哪个阶段失败了"、"产出物在哪"等，已知 pipelineBuildId。

### 执行步骤

```bash
# 查所有阶段
ipipe-cli build status --pipeline-build-id <id>

# 仅查特定阶段（已知 stageConfId 时）
ipipe-cli build status --pipeline-build-id <id> --stage-conf-id <stageConfId>
```

### 返回字段说明


```
流水线构建 #{buildNumber} 状态（pipelineBuildId: {id}）：

【{stageName}】{status中文}
  · {jobName}  {jobType简称}  {status中文}  {duration}
    产出物：{AGILE_PRODUCT_HTTP_URL}   ← 有产出物时展示
  · {jobName}  {status中文}
  ...

【{stageName}】{status中文}
  · {jobName}  {status中文}
```

**格式规则**：
- 阶段 `status` 映射：`SUCC`=✅成功，`FAIL`=❌失败，`RUNNING`=⏳进行中，`WAITING`=⏸️等待中，`SKIP`=⏭️跳过，`CANCEL`=取消
- `jobType` 简称：`AGILE_COMPILE`=编译，`AGILE_SHELL`=脚本，`AGILE_DEPLOY`=部署，其他直接展示原值
- 产出物 `outParams.AGILE_PRODUCT_HTTP_URL` 不为空时展示

---

## 场景六：查询阶段构建详情（含日志链接）

**适用**：用户问"帮我看下这个阶段的日志"、"阶段详情"、已知 stageBuildId。

### 执行步骤

```bash
ipipe-cli build stage --stage-build-id <id>
```

### 返回字段说明


```
阶段构建 {stageBuildId} 详情：

{jobName}（{jobType简称}）  {status中文}  耗时 {duration}
  日志：
  · 摘要日志：{logs[key=summary].url}
  · 详细日志：{logs[key=dev].url}
  产出物：{realJobBuild.productHttpUrl}   ← 有值时展示

{jobName}（{jobType简称}）  {status中文}
  日志：{logs[0].url}
```

**格式规则**：
- `logs` 中 `key=summary` 对应摘要日志，`key=dev` 对应详细日志，无区分时直接展示所有 url
- 日志 url 为空时不展示该行
- `realJobBuild.productHttpUrl` 有值时展示产出物链接

---

## 场景七：查询流水线构建下所有任务

**适用**：用户问"这次构建有哪些任务"、"任务列表"，已知 pipelineBuildId。

### 执行步骤

```bash
ipipe-cli build tasks --pipeline-build-id <id>
```

### 返回字段说明


```
流水线构建 {pipelineBuildId} 的任务列表：
· {jobName}（{jobType简称}）  {status中文}  [控制台]({jobUrl})
  产出物：{outParams.AGILE_PRODUCT_HTTP_URL}   ← 有值时展示
· {jobName}  {status中文}
...
```

---

## 场景八：查询单个任务构建详情

**适用**：用户要查看某个具体任务的详情、日志，已知 jobBuildId。

### 执行步骤

```bash
ipipe-cli build job --job-build-id <id>
```

### 返回字段说明


```
任务构建 {jobBuildId} 详情：
名称：{jobName}（{jobType简称}）
状态：{status中文}
耗时：{duration}
分支：{pluginJobBuild.branch}
日志：
  · 摘要日志：{logs[key=summary].url}
  · 详细日志：{logs[key=dev].url}
产出物：{pluginJobBuild.productHttpUrl}   ← 有值时展示
```

---

## 场景九：获取任务构建 Web 控制台链接

**适用**：用户说"给我构建链接"、"我要打开控制台"，已知 jobBuildId。

### 执行步骤

```bash
ipipe-cli build link --job-build-id <id>
```

### 返回字段说明


```
任务构建 {jobBuildId} 控制台链接：
{url}
```

---

## 场景十：按 commitId/changeId 反查构建记录

**适用**：用户说"这个 commit 触发了哪些构建"、"帮我查下这个 changeId 的流水线"。

### 执行步骤

```bash
ipipe-cli build commit --revision <commitId或changeId> --module <模块名>
```

### 返回字段说明


```
commitId {revision} 关联的构建记录：
· #{buildNumber}  {pipelineName}  {branch}  {status中文}  {buildTime格式化}  [查看]({buildUrl})
...
```

无结果时：`该 commitId 暂无关联的流水线构建记录。`

---

## 场景十一：按 iCafe 卡片反查构建记录

**适用**：用户说"卡片 workflow-14923 的构建"、"帮我查这个卡关联的流水线"。

### 执行步骤

```bash
ipipe-cli build card --card <卡片标识>
```

### 返回字段说明


```
iCafe 卡片 {card} 关联的构建记录（代码评审阶段）：
· #{buildNumber}  {pipelineName}  {branch}  {status中文}  {buildTime格式化}  [查看]({buildUrl})
  关联 commit：{commitBuildInfo.revision}（{commitBuildInfo.triggerUser}）
...
```

无结果时：`该卡片暂无关联的流水线构建记录。`

---

## 场景十二：按 pipelineId + iCafe 卡片精确反查构建

**适用**：用户说"这条流水线下 mapcio-qatools-1381 卡片对应哪些构建"、"帮我查 pipeline 925856 下卡片 xxx 的构建记录"。

### 执行步骤

```bash
ipipe-cli build search --module <模块名> --pipeline-id <id> --card <iCafe卡片>
```

> 若 `--pipeline-id` 未给出，先通过 `pipeline list --module <模块名>` 获取；若有多条流水线需确认具体哪一条。

### 返回字段说明

```
流水线 {pipelineName}（ID: {pipelineId}）中，iCafe 卡片 {card} 命中的构建记录：
· #{buildNumber}  {branch}  {status中文}  {buildTime格式化}
  匹配阶段 stageBuildId={matchedStageBuildId}  [查看]({buildUrl})
...
```

无结果时：`该流水线下未找到 AGILE_ICAFE_ISSUE_KEYS 匹配 {card} 的构建记录。可尝试增大 --limit 扩大搜索范围。`
