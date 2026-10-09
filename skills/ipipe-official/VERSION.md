# 版本记录

## 0.5.0 (2026-09-16)

### 变更内容
- 支持多用户共享环境：`~/.config/uuap/` 存在多个凭证时可通过全局 `--user <username>` 指定使用哪个用户
- 单用户场景保持不变，无需任何新参数，自动使用唯一凭证
- 多用户下未指定 `--user` 执行业务命令时返回 `multiple_credentials` 错误并附带候选用户列表
- 指定不存在的用户返回 `auth_failed` 并附带候选列表
- `login status` 增强：多用户时列出所有已登录用户
- `logout` 支持 `--user`，多用户环境下必须指定要登出的用户
- Skill 文档更新：认证章节补充多用户说明，错误处理表新增 `multiple_credentials`

---

## 0.4.0 (2026-07-28)

### 变更内容
- CLI 新增 `build search` 命令，支持按 pipelineId + iCafe 卡片精确反查构建
- 通过构建详情接口 `stageBuilds[].inParams/outParams` 中的 `AGILE_ICAFE_ISSUE_KEYS` 做精确卡片匹配
- 查询策略：路径 A（按卡片反查过滤 pipelineConfId）→ 路径 B（模块最近构建过滤 pipelineConfId）→ 逐条查详情匹配
- `build latest`、`build commit`、`build card`、`build history` 新增 `--limit` 可选参数（接口默认 10 条，仅需超过 10 条时才传）
- Skill 文档更新：新增 `build card` vs `build search` 选择指引、示例 5、触发条件表、query.md 场景十二、commands.md 参数表

---

## 0.3.0 (2026-06-24)

### 变更内容
- CLI 新增 `branch` 命令组，支持 SCM_FLOW 分支创建能力
- 新增 `branch builds` 查询最近 7 天构建记录
- 新增 `branch create` 非交互式创建 SCM_FLOW 分支，支持 `version` 和 `custom` 两种模式
- `branch create` 内置代码库工作流校验，非 SCM_FLOW 返回 `unsupported_workflow`
- Skill 新增 SCM_FLOW 分支创建固定选择模板和错误处理规范

---

## 0.2.0 (2026-05-26)

### 变更内容
- Description 优化为单行字符串，长度 694 字符
- 移除 frontmatter 中的 `allowed-tools` 非标准字段
- 新增"核心能力"章节，描述5个核心能力
- 新增"使用示例"章节，提供4个具体示例
- "触发场景"章节改为"触发条件"，使用表格展示
- 安装命令环境变量改为独立 export 语句
- completion 命令格式优化，避免误判为管道命令
- 新增 VERSION.md 版本记录文件
- cli新增埋点功能

---

## 0.1.0 (2025-05-07)

### 初始版本
- 支持 iPipe 流水线配置查询
- 支持流水线触发（按 commitId/changeId 或分支）
- 支持构建状态、阶段详情、任务详情、日志链接查询
- 支持构建管理（取消任务、重新执行阶段）
- 支持 commit/iCafe 卡片反查