# 构建操作

> 本文件说明取消任务、重新执行阶段和 SCM_FLOW 分支创建的执行步骤。
> 取消/重试输出风格自由；SCM_FLOW 分支创建必须使用本文固定选择模板。
> ID 解析链见 [SKILL.md](../SKILL.md#id-自动解析链)。

---

## 场景一：取消任务（build cancel）

**适用**：用户说"取消这个任务"、"把这个 job 取消掉"。

### ID 推导

执行前需要 `--job-build-id`，按以下优先级推导：

| 用户提供的信息 | 推导方法 |
|-------------|---------|
| 直接给 job-build-id | 直接使用 |
| `pipelineBuildId` | `build tasks --pipeline-build-id <id>`，展示任务列表，用户确认目标任务 |
| `stageBuildId` | `build stage --stage-build-id <id>`，展示任务列表，用户确认目标任务 |
| 模块名 + 分支（最新构建） | `build latest --pipeline-id <id>` 得到 `pipelineBuildId`，再 `build tasks` |
| 模块名（最近构建） | `build history --module <模块名>` 得到 `pipelineBuildId`，再 `build tasks` |

### 执行步骤

```bash
ipipe-cli build cancel --job-build-id <id>
```

### 结果处理

- 成功 → 告知取消成功
- 失败 → 告知错误原因（常见：任务已结束、权限不足、ID 不存在）

---

## 场景二：重新执行阶段（build retry）

**适用**：用户说"重跑这个阶段"、"把这个阶段再执行一次"、"retry"。

### ID 推导

执行前需要 `--stage-build-id`，按以下优先级推导：

| 用户提供的信息 | 推导方法 |
|-------------|---------|
| 直接给 stage-build-id | 直接使用 |
| `pipelineBuildId` | `build status --pipeline-build-id <id>`，展示各阶段状态，按用户描述（阶段名、失败状态等）定位 `stageBuildId` |
| 上次 trigger start 的响应 | 直接取响应中的 `stageBuildIds[]` |
| 模块名 + 分支（最新构建） | `build latest --pipeline-id <id>` 得到 `pipelineBuildId`，再 `build status` 找阶段 |
| 模块名（最近构建） | `build history --module <模块名>` 得到 `pipelineBuildId`，再 `build status` 找阶段 |

若用户描述的是"失败的阶段"，`build status` 返回后按 `status=FAIL` 自动定位，无需用户再指定。

### 执行步骤

```bash
# 不带自定义参数
ipipe-cli build retry --stage-build-id <id>

# 带自定义参数
ipipe-cli build retry --stage-build-id <id> --param key=value [--param key=value ...]
```

### 结果处理

- `code: 200` → 告知触发成功，提示可用 `build stage --stage-build-id <id>` 查询执行状态
- 失败 → 告知错误原因（常见：ID 失效、权限不足、当前状态不允许重试）

---

## 场景三：创建 SCM_FLOW 分支（branch create）

**适用**：用户说"创建分支"、"创建 SCM_FLOW 分支"、"创建版本分支"。

### 执行原则

- `ipipe-cli branch create` 是非交互式命令，禁止期待 CLI 读取 stdin。
- 固定选择模板、用户二次确认、创建方式选择、构建版本选择均由 Skill/Agent 层完成。
- 用户提供了分支名时，只能作为 custom 模式候选值展示；不能直接默认 custom 创建。
- 版本号命名模式无需向用户暴露版本号获取接口，CLI 会在 `--scm-mode version` 时内部获取版本号。

### 第一步：查询最近 7 天构建

```bash
ipipe-cli branch builds --module <模块名>
```

从返回数组中提取：

| 字段 | 用途 |
|------|------|
| `compileBuild.id` | `branch create --build-id` |
| `revision` | `branch create --revision` |
| `compileBuild.branch` | 展示给用户选择 |
| `compileBuild.buildStatus` | 展示构建状态 |
| `comment` | 展示构建备注 |
| `tagTime` | 展示构建时间 |

### 第二步：展示固定选择模板

```text
检测到当前代码库 <module> 需要通过 iPipe SCM_FLOW 流程创建分支。

请选择创建方式：
  1. 通过版本号命名创建
     - version 由 CLI 自动获取
     - 分支备注可选
  2. 自定义名称方式创建
     - branch 使用用户指定的新分支名：<branch 或 未提供>

请选择构建版本（最近 7 天构建）：
  1. buildId=<compileBuild.id> revision=<revision前8位> branch=<branch> status=<status> comment=<comment> time=<时间>
  2. buildId=<compileBuild.id> revision=<revision前8位> branch=<branch> status=<status> comment=<comment> time=<时间>
  3. buildId=<compileBuild.id> revision=<revision前8位> branch=<branch> status=<status> comment=<comment> time=<时间>
  4. buildId=<compileBuild.id> revision=<revision前8位> branch=<branch> status=<status> comment=<comment> time=<时间>
  5. buildId=<compileBuild.id> revision=<revision前8位> branch=<branch> status=<status> comment=<comment> time=<时间>

请回复：创建方式编号 + 构建版本编号 + 分支备注（仅方式 1 生效，可空）
例如：1 2 release分支
```

### 第三步：执行创建

版本号命名创建：

```bash
ipipe-cli branch create \
  --module <模块名> \
  --scm-mode version \
  --build-id <compileBuild.id> \
  --revision <revision> \
  [--remarks <备注>]
```

自定义名称创建：

```bash
ipipe-cli branch create \
  --module <模块名> \
  --scm-mode custom \
  --build-id <compileBuild.id> \
  --revision <revision> \
  --branch <分支名>
```

### 结果处理

- 成功 → 告知创建请求已提交，并提炼接口返回中的关键字段。
- `unsupported_workflow` → 直接告知用户该代码库不是 SCM_FLOW，不能使用 iPipe SCM_FLOW 分支创建能力，并展示 CLI 返回的工作流类型。
- 失败 → 告知错误原因（常见：无可用构建、权限不足、分支名不合法、所选构建不可用于创建分支）。

---

## 典型工作流

### 用户只说"重跑失败的阶段"，未给任何 ID

```
用户：workflow-project 最新的构建，失败的阶段帮我重跑一下
  ↓
Agent：pipeline list --module baidu/soqa/workflow-project（获取 pipeline-id）
  ↓
Agent：build latest --pipeline-id <id>（获取最新 pipelineBuildId）
  ↓
Agent：build status --pipeline-build-id <id>（找 status=FAIL 的阶段，得到 stageBuildId）
  ↓
Agent：build retry --stage-build-id <stageBuildId>
  ↓
Agent：告知重试结果
```

### 用户提供了 pipelineBuildId，要取消其中一个任务

```
用户：帮我取消流水线构建 248265440 里的编译任务
  ↓
Agent：build tasks --pipeline-build-id 248265440（展示任务列表）
  ↓
Agent：按 jobType=AGILE_COMPILE 或 jobName 匹配，确认 jobBuildId
  ↓
Agent：build cancel --job-build-id <id>
  ↓
Agent：告知取消结果
```

### 用户给了 stageBuildId，要重试

```
用户：阶段 591141242 重新跑一下
  ↓
Agent：build retry --stage-build-id 591141242（直接执行，无需额外查询）
  ↓
Agent：告知结果
```
