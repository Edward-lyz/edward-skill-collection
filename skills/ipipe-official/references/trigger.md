# 触发操作

> 本文件说明触发流水线的执行步骤。
> 输出风格自由，提炼关键信息展示即可，无需固定模板。
> ID 解析链见 [SKILL.md](../SKILL.md#id-自动解析链)。

---

## 场景一：按分支触发流水线（trigger start）

**适用**：用户说"触发 master 分支"、"跑一下 MasterPipeline"、"按分支触发"等。

### ID 推导

执行前需要 `--pipeline-id`，按以下优先级推导：

1. 用户直接给了 pipeline-id → 直接使用
2. 用户给了**模块名 + 流水线名称** → `pipeline list --module <模块名>`，按 `pipelineName` 匹配
3. 用户只给了**模块名** → `pipeline list --module <模块名>`，展示列表让用户选择
4. 用户给了**模块名**且只有一条流水线 → 自动选定，无需询问

### 执行步骤

```bash
ipipe-cli trigger start --pipeline-id <id> --branch <branch> [--param key=value ...]
```

### 结果处理

- `code=200` → 告知 `pipelineBuildId`、`buildNumber`，提示可用 `build status --pipeline-build-id <pipelineBuildId>` 查询进度
- `code≠200` → 告知 `msg` 中的错误原因

---

## 场景二：按 commitId/changeId 触发流水线（trigger run）

**适用**：用户说"用这个 commit 触发流水线"、"按 commitId 跑一下"、"gerrit change 触发"等。

### ID 推导

执行前需要 `--pipeline-id`，推导规则同场景一。

若用户**未明确说明触发哪条流水线**，可先调用 `build commit --revision <id> --module <模块名>` 查看该 commit 历史上触发过哪些流水线，辅助用户选择。

### 执行步骤

```bash
ipipe-cli trigger run \
  --pipeline-id <id> \
  --revision <commitId或changeId> \
  [--branch <branch>] \
  [--event-type <NEW_COMMIT|GERRIT_CHANGE>] \
  [--param key=value ...]
```

**event-type 选择规则**：
- 用户提到 Gerrit change / CR / 评审 → `GERRIT_CHANGE`
- 用户提到 merge / 合入 → `NEW_COMMIT`
- 用户未指定 → 不传此参数

### 结果处理

- `success: true` → 告知 `pipelineBuildId`、`buildNumber`
- `success: false, limited: true` → 触发被限流，稍后重试
- `success: false, limited: false` → 告知 `errorMessage` 中的失败原因

---

## 典型工作流

### 用户只提供模块名和分支

```
用户：帮我触发 baidu/soqa/workflow-project 的 master 分支
  ↓
Agent：pipeline list --module baidu/soqa/workflow-project（列出所有流水线）
  ↓
Agent：若有多条，询问用户选哪条；若只有一条，自动选定
  ↓
Agent：trigger start --pipeline-id <id> --branch master
  ↓
Agent：告知触发结果和 pipelineBuildId
```

### 用户提供流水线名称而非 ID

```
用户：帮我触发 MasterPipeline，分支 master，模块 baidu/soqa/workflow-project
  ↓
Agent：pipeline list --module baidu/soqa/workflow-project，匹配 pipelineName=MasterPipeline，得到 id=925854
  ↓
Agent：trigger start --pipeline-id 925854 --branch master
  ↓
Agent：告知触发结果
```

### 代码提交后按 commit 触发

```
用户：commitId b62cee14 帮我触发一下流水线，模块是 baidu/soqa/workflow-project
  ↓
Agent：若用户未指定流水线，先 build commit --revision b62cee14 --module ... 查历史触发记录辅助选择
  ↓
Agent：pipeline list 确认 pipeline-id
  ↓
Agent：trigger run --pipeline-id <id> --revision b62cee14
  ↓
Agent：告知触发结果，提示可用 build status 跟踪进度
```
