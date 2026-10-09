---
name: ipipe-official
description: iPipe 官方流水线助手，支持流水线配置查询、触发构建、构建状态查询、构建管理和 SCM_FLOW 分支创建。当用户涉及以下场景时使用此技能：查询模块下的流水线列表或配置、触发流水线（按 commitId/changeId 或按分支触发）、查询构建状态/阶段详情/任务详情/日志链接、查询最新构建/最近记录/按 commit 或 iCafe 卡片反查、按 pipelineId + iCafe 卡片精确反查构建、取消任务/重新执行阶段、创建 SCM_FLOW 分支、代码提交后触发编译部署流水线。例如："帮我触发一下 MasterPipeline"、"workflow-project 的流水线构建状态怎么样"、"这个 commitId 触发了哪些流水线"、"这条流水线下 mapcio-qatools-1381 卡片对应哪些构建"、"把这个阶段重新跑一下"、"取消这个任务"、"帮我创建 SCM_FLOW 分支"。
metadata:
  cli_version: 0.5.0
  security_level: L0
---

# iPipe 流水线助手

## 安装与认证

**CLI 默认安装路径**：`~/.ipipe-cli/bin/ipipe-cli`，安装脚本自动加入 PATH。

### 版本检查（每次会话首次调用 CLI 前执行一次）

```bash
ipipe-cli version
```

| 结果 | 处理 |
|------|------|
| command not found | 再试 `~/.ipipe-cli/bin/ipipe-cli version`；仍失败则运行安装命令 |
| 版本低于 `0.5.0` | 提示用户版本过低，运行安装命令覆盖更新 |
| 版本符合 | 记住可用路径，本次会话不再重复检查 |

安装命令：

```bash
export IPIPE_CLI_VERSION=0.5.0
bash -c "$(curl -fsSL 'https://bep-qa.bj.bcebos.com/ipipe-cli/install_ipipe-cli.sh')"
```

安装后若 PATH 未生效，后续命令用完整路径 `~/.ipipe-cli/bin/ipipe-cli`。

### 认证错误处理

CLI 返回 `{"error":"auth_failed",...}` 时，提示用户登录：

```bash
ipipe-cli login --token <ugate-token>   # 非交互式（Agent/脚本推荐）
ipipe-cli login                          # 交互式
```

UGate Token 获取：https://uuap.baidu.com/agent/token
Token 保存至 `~/.config/uuap/`，后续命令无需再传。

### 多用户共享环境

当 `~/.config/uuap/` 下存在多个用户凭证（多人共用一个 Agent 空间）时：

- **单用户**：无需任何额外参数，自动使用唯一凭证。
- **多用户**：所有业务命令必须用全局 `--user <username>` 指定身份，例如：
  ```bash
  ipipe-cli pipeline list --module <模块名> --user zhangsan
  ```
- 未指定时 CLI 返回 `{"error":"multiple_credentials","message":"...","candidates":["zhangsan","lisi"]}`，
  应从 `candidates` 中确认当前应使用的身份（无法判断时反问用户），再重试并带上 `--user`。
- 查看有哪些已登录用户：`ipipe-cli login status`。
- 登出指定用户：`ipipe-cli logout --user <username>`。

---

## 行为约束

- 调用 CLI 时**禁止省略必填参数**，**禁止自行推断或替换参数值**
- **禁止**直接将 CLI 原始 JSON 输出给用户，应提炼关键信息以自然语言呈现
- 一般输出风格自由；SCM_FLOW 分支创建必须使用 `references/build-ops.md` 中的固定选择模板

---

## 核心能力

### 流水线查询
- 查询模块下的流水线列表及配置
- 获取流水线阶段信息（stageConfId）
- 按分支查询最新构建记录
- 获取模块最近构建历史

### 构建触发
- 按 commitId/changeId 触发流水线构建
- 按分支触发流水线构建
- 支持二次确认流程

### 构建状态追踪
- 查询流水线构建状态和进度
- 查询阶段构建详情及日志链接
- 查询所有任务构建信息
- 获取任务 Web 控制台链接

### 构建管理
- 取消正在执行的任务
- 重新执行失败的阶段

### SCM_FLOW 分支管理
- 查询模块最近 7 天构建记录，供用户选择构建版本
- Skill 层先用固定模板让用户选择创建方式和构建版本，CLI 层在 `branch create` 时再次校验仓库是否为 SCM_FLOW
- 自动获取版本号（三段式，内部使用，不暴露给用户）
- 非交互式创建 SCM_FLOW 分支（version 版本号命名 / custom 自定义名称）

### 反向查询
- 按 commitId/changeId 反查触发的流水线
- 按 iCafe 卡片标识反查关联构建（`build card`：**不限流水线**，走 commit message 关联，返回该卡片在整个模块/空间下关联的构建）
- 按 pipelineId + iCafe 卡片精确反查构建（`build search`：**限定某一条流水线**，逐条比对构建详情里 `AGILE_ICAFE_ISSUE_KEYS` 精确命中该卡片的构建）

> **`build card` vs `build search` 如何选**：
> - 用户只给卡片、没指定具体是哪条流水线 → `build card`
> - 用户同时点名了某条流水线（流水线名或 pipeline-id）+ 卡片，问"这条流水线下这个卡片对应哪些构建" → `build search`（缺 pipeline-id 时先 `pipeline list` 让用户选）

---

## 使用示例

### 示例 1：查询流水线列表
**用户**："workflow-project 有哪些流水线？"

**执行步骤**：
```bash
ipipe-cli pipeline list --module workflow-project
```

**返回结果**：流水线列表，包含 pipelineName 和 pipelineId

---

### 示例 2：触发流水线
**用户**："帮我触发一下 MasterPipeline"

**执行步骤**：
1. 查询流水线 ID：`ipipe-cli pipeline list --module <模块名>`
2. 确认触发信息（二次确认）
3. 执行触发：`ipipe-cli trigger run --pipeline-id <id> --revision <commitId>`

---

### 示例 3：查看构建状态
**用户**："workflow-project 的流水线构建状态怎么样"

**执行步骤**：
```bash
ipipe-cli build latest --pipeline-id <id>
```

**返回结果**：各分支最新构建状态，包含 pipelineBuildId

---

### 示例 4：重跑阶段
**用户**："把这个阶段重新跑一下"

**执行步骤**：
1. 获取 stageBuildId：`ipipe-cli build status --pipeline-build-id <id>`
2. 确认重跑（二次确认）
3. 执行重跑：`ipipe-cli build retry --stage-build-id <id>`

---

### 示例 5：按流水线 + iCafe 卡片精确反查
**用户**："ChangePipeline 里 mapcio-qatools-1381 这个卡片对应哪些构建？"

**执行步骤**：
1. 查询流水线 ID：`ipipe-cli pipeline list --module <模块名>` → 按名称匹配 `ChangePipeline` 取 id
2. 精确反查：`ipipe-cli build search --module <模块名> --pipeline-id <id> --card mapcio-qatools-1381`

**返回结果**：命中该卡片的构建记录列表（含 pipelineBuildId、构建号、分支、状态、Web 链接）

---

## 触发条件

| 关键词 | 用户意图 | 适用命令 |
|--------|----------|----------|
| 流水线、pipeline、构建、build | 查询流水线信息或构建状态 | pipeline list/config, build status/latest/history |
| 查流水线列表、有哪些流水线 | 查询模块下的流水线 | pipeline list |
| 触发流水线、跑一下流水线、按分支/commitId 触发 | 触发流水线构建 | trigger run/start |
| 查构建状态、看构建结果、构建进行到哪了 | 查询构建进度和状态 | build status/stage/tasks/job |
| 重新执行阶段、重跑、retry | 重新执行失败的阶段 | build retry |
| 取消任务、cancel | 取消正在执行的任务 | build cancel |
| 这个 commitId 触发了哪些流水线 | 按 commitId 反查流水线 | build commit |
| 查某个 iCafe 卡片关联的构建 | 按 iCafe 卡片反查构建（不限流水线） | build card |
| 指定流水线 + 卡片精确反查 | 按 pipelineId + iCafe 卡片精确反查命中的构建（限定流水线，查 AGILE_ICAFE_ISSUE_KEYS） | build search |
| 获取构建日志链接、看任务链接 | 获取 Web 控制台链接 | build link |
| 创建分支、SCM_FLOW 分支、创建版本分支 | 创建 SCM_FLOW 分支 | branch builds, branch create |

---

## 命令总览

```
ipipe-cli
├── pipeline
│   ├── list      查询模块下的流水线列表（--module）
│   └── config    获取流水线配置，含阶段 stageConfId（--module）
├── trigger
│   ├── run       按 commitId/changeId 触发流水线
│   └── start     按分支触发流水线
├── build
│   ├── latest    查询各分支最新一次构建（--pipeline-id）
│   ├── history   获取模块最近构建记录（--module）
│   ├── status    获取流水线构建信息，含各阶段任务（--pipeline-build-id）
│   ├── stage     查询阶段构建详情，含日志链接（--stage-build-id）
│   ├── tasks     查询流水线构建下所有任务（--pipeline-build-id）
│   ├── job       查询单个任务构建详情（--job-build-id）
│   ├── link      获取任务构建 Web 控制台链接（--job-build-id）
│   ├── commit    按 commitId/changeId 查询构建信息（--revision, --module）
│   ├── card      按 iCafe 卡片标识查询关联构建（--card）
│   ├── cancel    取消任务（--job-build-id）
│   ├── retry     重新执行阶段（--stage-build-id）
│   └── search    按 pipelineId + iCafe 卡片精确反查命中该卡片的构建（--module, --pipeline-id, --card）
├── branch
│   ├── builds    查询模块最近 7 天构建记录（--module）
│   └── create    非交互式创建 SCM_FLOW 分支（--module, --scm-mode, --build-id, --revision）
├── login [--token <token>]
│   └── status              查看登录状态（多用户时列出所有已登录用户）
├── logout [--user <username>]
├── version
└── completion <shell>    # shell 可选值: bash, zsh

全局参数（所有命令可用）：
  --user <username>   多用户共享环境下指定使用哪个已登录用户的凭证
```

---

## 核心参数 说明

### --module 模块名
**格式**：`XXXX/XXXXX/项目名称`，如 `baidu/soqa/workflow-project`
**用途命令**：`pipeline list`、`pipeline config`、`build history`、`build commit`
**获取方式**：
1. **自动推导（推荐）**：当前目录为 git 仓库时，从 git remote 提取
git remote 示例
ssh://xiaowang@icode.baidu.com:8235/baidu/ide/comate-plugin-host
→ 提取为 baidu/ide/comate-plugin-host
2. **人工输入**：非 git 仓库或 git 命令不可用等无法自动推导时，直接询问用户提供

**注意事项**：
- 为必填参数，无默认值
- 区分大小写
- 若模块名错误，命令会返回 `http_404` 错误或空结果

---

### --card iCafe 卡片标识

**格式**：`空间标识-编号`，如 `bbbbb-14923`、`aaa-23041`
**用途命令**：`build card`、`build search`
**获取方式**：用户提供
**注意事项**：必填，错误会返回空结果

---

### --branch 分支名

**格式**：任意 git 分支名，如 `master`、`stable`、`feature/xxx`、`release/1.0`
**用途命令**：`trigger start`、`trigger run`（可选）
**获取方式**：
1. git 仓库：可通过 `git branch --show-current` 获取当前分支
2. 用户指定
**注意事项**：分支不存在时触发失败

---

### --event-type 事件类型

**格式**：枚举值，仅支持
- `NEW_COMMIT`：代码合入后的 merge commit
- `GERRIT_CHANGE`：gerrit change 关联
**用途命令**：`trigger run`（可选）
**注意事项**：默认根据 revision 格式自动识别，一般无需指定


## ID 关系速查

```
pipeline list → entities[].id = --pipeline-id
                                      ↓
            trigger start/run → pipelineBuildId ──→ build status/tasks --pipeline-build-id
                              → stageBuildIds[] ──→ build stage/retry  --stage-build-id
                              → jobBuildIds[]   ──→ build job/link/cancel --job-build-id

build status → jobBuildBeans[].id  = --job-build-id
build stage  → realJobBuilds[].id  = --job-build-id
build tasks  → entities[].id       = --job-build-id

pipeline config → stageConfBeans[].stageConfId = --stage-conf-id（build status 可选筛选）
```

---

## ID 自动解析链

**用户不必提供所有 ID，根据用户给出的信息逐步查询推导：**

| 用户给的信息 | 缺的 ID | 解析方法 |
|------------|--------|---------|
| 模块名 | `--pipeline-id` | `pipeline list --module <模块名>` 取 `entities[].id` |
| 模块名 | `--pipeline-build-id` | `build history --module <模块名>` 取最近一条或符合条件的 `id` |
| 模块名 + 分支名 | `--pipeline-build-id` | `build latest --pipeline-id <id>` 按分支过滤取 `id` |
| `pipelineBuildId` | `--stage-build-id` | `build status --pipeline-build-id <id>` 取 `entities[].id`（stageBuildId） |
| `pipelineBuildId` | `--job-build-id` | `build tasks --pipeline-build-id <id>` 取 `entities[].id` |
| `stageBuildId` | `--job-build-id` | `build stage --stage-build-id <id>` 取 `realJobBuilds[].id` |
| commitId / changeId + 模块名 | `--pipeline-build-id` | `build commit --revision <id> --module <模块名>` 取结果中的 `id` |
| iCafe 卡片标识 | `--pipeline-build-id` | `build card --card <card>` 取结果中的 `id` |
| 流水线名称（非 ID） | `--pipeline-id` | `pipeline list --module <模块名>` 按 `pipelineName` 匹配 |

**解析原则**：
- 优先使用用户已提供的信息，**仅在必要时才调用额外命令补全 ID**
- 若一步查询能同时获得多个 ID（如 `build status` 同时返回 `stageBuildId` 和 `jobBuildId`），直接复用，不重复查询
- 若查询结果有多条，根据用户描述（分支名、流水线名称、时间、状态等）过滤；仍有歧义时询问用户确认

---

## 错误处理

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 未登录或认证失败 |
| 2 | CLI 参数校验失败（缺必填参数等） |
| 4 | API 请求失败（HTTP 非 2xx） |

业务错误：HTTP 200 但响应 `code ≠ 200`，错误描述在 `msg` 字段。

| 错误信息 | 解决方案 |
|---------|---------|
| `auth_failed` | `ipipe-cli login --token <token>`；若响应含 `candidates`，说明指定的 `--user` 不存在，从中选正确用户名重试 |
| `multiple_credentials` | 多用户共享环境未指定身份，从响应 `candidates` 中确认当前用户，重试并带上 `--user <username>`（无法判断时反问用户） |
| `missing_parameter` | 补充必填 flag，查看 `ipipe-cli <命令> --help` |
| `unsupported_workflow` | 代码库不是 SCM_FLOW，不能使用 iPipe SCM_FLOW 分支创建能力，直接向用户说明 CLI 返回的工作流类型 |
| `http_401` | Token 过期，重新登录 |
| `http_403` | 当前账号无权限操作该资源 |
| `http_404` | 资源不存在，确认 ID 是否正确 |
| `http_500` | 服务端内部错误，稍后重试 |

---

## 参考文件

| 文件 | 内容 |
|------|------|
| [references/query.md](references/query.md) | 查询场景：执行步骤 + 输出模板（pipeline list/config、build status/stage/tasks/job/link/history/latest/commit/card/search） |
| [references/trigger.md](references/trigger.md) | 触发场景：二次确认流程 + 执行步骤 + 输出模板（trigger run/start） |
| [references/build-ops.md](references/build-ops.md) | 构建操作：二次确认流程 + 执行步骤 + 输出模板（build cancel/retry） |
| [references/commands.md](references/commands.md) | 所有命令的完整参数表和返回字段说明 |
