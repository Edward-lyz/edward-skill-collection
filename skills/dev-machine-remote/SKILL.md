---
name: dev-machine-remote
description: 在已配置 remote-exec 的远端开发机上执行命令、同步文件、跑 GPU/NCCL/DeepEP 测试时使用。覆盖 H20/B200/H200/H100 等无 SSH 通路但开放 remote-exec 和 rsync 端口的本地 Mac 到远端开发工作流。
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - AskUserQuestion
---

# Dev Machine Remote

## CLI 工具

统一入口：`python3 PRIVATE/scripts/rdev.py`（零外部依赖）

```bash
# 列出所有机器别名
python3 PRIVATE/scripts/rdev.py ls

# 检查目标机器连通性
python3 PRIVATE/scripts/rdev.py health --host <alias>

# 远程执行命令（前台，仅用于快速命令如 nvidia-smi / ls / 小文件操作）
python3 PRIVATE/scripts/rdev.py exec --host <alias> "COMMAND"
python3 PRIVATE/scripts/rdev.py exec --host <alias> --timeout 600 --cwd /path "COMMAND"

# 长耗时命令必须走后台模式（见下方 "长耗时命令与后台执行" 章节）

# 文件同步（push 本地到远端）
python3 PRIVATE/scripts/rdev.py sync push --host <alias> --dest /remote/path
python3 PRIVATE/scripts/rdev.py sync pull --host <alias> --dest /remote/path

# JSON 输出（Agent 友好）
python3 PRIVATE/scripts/rdev.py --json exec --host h20-dev "nvidia-smi"
```

## Machines

- Local workspace: `/Users/liyanzhen/baidu`
- Machine list source: `~/.ssh/issh_config.yaml`
- 别名解析：subGroup `name` -> `hosts[0].ip`
- 默认机器：环境变量 `RDEV_HOST` 或 `b200-dev-2`

所有机器均已配置：
- remote-exec: port `8600`
- rsync daemon: port `8599`, module `root`（path=/，可写任意目录）

## 全局参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `b200-dev-2` | 机器别名或完整 hostname |
| `--exec-port` | 8600 | remote-exec 端口 |
| `--sync-port` | 8599 | rsync daemon 端口 |
| `--json` | false | JSON 输出模式 |

## 长耗时命令与后台执行（MUST）

### 识别规则

以下命令类别视为**长耗时**，必须挂后台执行，禁止前台阻塞：

| 类别 | 典型命令 |
|------|---------|
| GPU benchmark/压测 | `python bench_*.py`, `torchrun`, `deepep_*` |
| 模型训练/推理 | `python train.py`, `vllm serve`, `sglang.launch_server` |
| NCCL/集合通信测试 | `nccl-tests`, `all_reduce_perf`, `alltoall_perf` |
| 编译构建 | `make -j`, `pip install .`, `cmake --build .` |
| 大数据处理 | 处理 >1GB 数据的脚本 |
| 显式大超时 | 命令携带 `--timeout > 120` |

模糊情况判断标准：如果命令**预期执行超过 30 秒**，按长耗时处理。

### 执行方式

**第一步**：构造远端后台命令。使用 nohup 将实际命令在远端机器上后台运行，输出重定向到带时间戳的日志文件：

```bash
python3 PRIVATE/scripts/rdev.py exec --host <alias> --timeout 10 \
  'mkdir -p /tmp/rdev_logs && LOGFILE="/tmp/rdev_logs/$(date +%Y%m%d_%H%M%S)_<简短描述>.log" && nohup sh -c "<ACTUAL_COMMAND>" > "$LOGFILE" 2>&1 & echo "PID=$! LOG=$LOGFILE"'
```

要点：
- `--timeout 10` 只覆盖 remote-exec HTTP 响应（nohup 几乎瞬间返回），实际命令在远端持续执行不受影响
- 使用单引号包裹整个命令字符串，避免本地 shell 展开 `$()` 和 `$!`
- `<简短描述>` 使用英文小写+下划线，如 `nccl_allreduce`、`deepep_bench`
- `<ACTUAL_COMMAND>` 是原始要执行的命令

**第二步**：使用 Bash 工具的 `run_in_background: true` 执行上述命令，确保本地不阻塞。

**第三步**：从返回输出中解析 `PID=<pid> LOG=<path>`，然后**必须**用以下格式告知用户：

```
已提交后台任务到 <host>：
  PID:  <pid>
  日志: <LOGFILE>

查看日志：
  rdev exec --host <alias> "tail -f <LOGFILE>"

检查进程：
  rdev exec --host <alias> "ps -p <pid>"
```

### 用户查看进度的后续交互

用户要求查看进度时，使用：

```bash
# 查看最新日志
python3 PRIVATE/scripts/rdev.py exec --host <alias> "tail -100 <LOGFILE>"

# 检查进程是否存活
python3 PRIVATE/scripts/rdev.py exec --host <alias> "ps -p <pid> && echo running || echo done"
```

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 1 | 远程命令失败（rc != 0） |
| 2 | 连接/配置错误 |

## Baseline GPU Checks

```bash
python3 PRIVATE/scripts/rdev.py exec --host <alias> "nvidia-smi -L && nvidia-smi topo -m && python3 --version"
```
