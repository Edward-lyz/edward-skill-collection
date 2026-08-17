---
name: op-profiler
description: 远端算子性能采集全流程。触发词："算子采集"、"跑 profiler"、"采集算子"、"跑完没"、"拉回数据"。当用户提到在 B200/H20 远端机器上进行 aiak_ds_tool 的算子性能采集、同步代码、启动/停止 profiler、查询采集进度、拉取结果到本地时，必须使用本 skill。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Op Profiler - 远端算子性能采集

本 skill 封装了在远端开发机（b200Dev）上进行 aiak_ds_tool 算子性能采集的完整工作流。

## 依赖

- **dev-machine-remote skill**：所有远程操作依赖 `rdev.py`（路径 `PRIVATE/scripts/rdev.py`）
- **远端容器**：名为 `grab` 的 Docker 容器（8 卡全见），用指定镜像启动
- **本地代码**：`BAIDU_REPO/aiak_ds_tool/`
- **远端代码目录**：`/home/users/liyanzhen01/aiak_ds_tool/`
- **默认远端数据目录**：`/home/users/liyanzhen01/aiak_ds_tool/data/`（即在远端代码目录下运行 profiler 时的默认 `./data`）
- **备用远端数据目录**：`/home/users/liyanzhen01/profiler_data/`（仅当目标 simulator `run_cfg.yaml` 明确把 `data_dir` 指向这里时使用）
- **远端日志目录**：`/home/users/liyanzhen01/logs/`
- **本地拉取位置**：`profiler_results/`

## 工作流

### 0. 数据目录对齐（MUST）

采集写入目录必须和后续 simulator 读取目录一致。先看目标 `run_cfg.yaml` 的 `data_dir`：

- `data_dir: ./data` 或未显式指定时，在 `/home/users/liyanzhen01/aiak_ds_tool` 下执行 profiler，使用默认 `./data`，不要传 `--data-dir /home/users/liyanzhen01/profiler_data`
- `data_dir` 指向绝对路径时，profiler 的 `--data-dir` 必须使用同一个绝对路径
- 除非用户明确要求把采集结果放到独立数据目录，否则不要使用 `/home/users/liyanzhen01/profiler_data`

### 1. 同步代码到远端

全量覆盖同步 `aiak_ds_tool` 目录（含 app.py 和所有配置文件）：

```bash
python3 PRIVATE/scripts/rdev.py sync push --host b200Dev --dest /home/users/liyanzhen01/aiak_ds_tool --src /Users/liyanzhen/baidu/BAIDU_REPO/aiak_ds_tool
```

同步 profiler 配置文件目录（`profiler_configs/`）：

```bash
python3 PRIVATE/scripts/rdev.py sync push --host b200Dev --dest /home/users/liyanzhen01/aiak_ds_tool/profiler_configs --src /Users/liyanzhen/baidu/BAIDU_REPO/aiak_ds_tool/profiler_configs
```

同步 prefill 配置文件（`deepseek_v4/prefill.yaml`）：

```bash
python3 PRIVATE/scripts/rdev.py sync push --host b200Dev --dest /home/users/liyanzhen01/aiak_ds_tool/aiak_infer_tools/extensions/apps/op_profiler/configs/deepseek_v4 --src /Users/liyanzhen/baidu/BAIDU_REPO/aiak_ds_tool/aiak_infer_tools/extensions/apps/op_profiler/configs/deepseek_v4
```

### 2. 管理远端进程

**停止已有 profiler**：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'docker exec grab sh -c "pkill -f profiler 2>/dev/null"'
```

**停止 grabGPU**：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'docker exec grab sh -c "pkill -f \"./gg\" 2>/dev/null"'
```

### 3. 启动 grabGPU 占卡（可选）

8 卡各占 10GB，利用率 10%，持续 24 小时：

```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'nohup docker exec grab sh -c "cd /home/users/liyanzhen01/grabGPU && ./gg 10 24 -1 0.1" > /home/users/liyanzhen01/logs/gpu_keeper.log 2>&1 &'
```

### 4. 管理远端 DB 数据

**清理旧 DB（全新采集）**：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'docker exec grab sh -lc "rm -rf /home/users/liyanzhen01/aiak_ds_tool/data/b200/*.db /home/users/liyanzhen01/aiak_ds_tool/data/.tmp 2>/dev/null"'
```

**保留旧 DB（增量采集）**：默认不做任何操作，profiler 自动增量跳过已有 shape。

### 5. 启动 profiler 采集

**使用 prefill.yaml**（完整批量采集）：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'LOGFILE="/home/users/liyanzhen01/logs/op_profiler_$(date +%Y%m%d_%H%M%S).log" && docker exec -d grab sh -lc "cd /home/users/liyanzhen01/aiak_ds_tool && python -m aiak_infer_tools profiler --config-bundle aiak_infer_tools/extensions/apps/op_profiler/configs/deepseek_v4/prefill.yaml > \"$LOGFILE\" 2>&1" && echo "LOG=$LOGFILE"'
```

**使用 single/batch 配置文件**（profiler_configs 目录下的）：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'LOGFILE="/home/users/liyanzhen01/logs/op_profiler_$(date +%Y%m%d_%H%M%S).log" && docker exec -d grab sh -lc "cd /home/users/liyanzhen01/aiak_ds_tool && python -m aiak_infer_tools profiler --config-bundle profiler_configs/<CONFIG_FILE> > \"$LOGFILE\" 2>&1" && echo "LOG=$LOGFILE"'
```

如果目标 `run_cfg.yaml:data_dir` 是绝对路径，例如 `/home/users/liyanzhen01/profiler_data`，才显式传同一个目录：

```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'LOGFILE="/home/users/liyanzhen01/logs/op_profiler_$(date +%Y%m%d_%H%M%S).log" && docker exec -d grab sh -lc "cd /home/users/liyanzhen01/aiak_ds_tool && python -m aiak_infer_tools profiler --data-dir /home/users/liyanzhen01/profiler_data --config-bundle profiler_configs/<CONFIG_FILE> > \"$LOGFILE\" 2>&1" && echo "LOG=$LOGFILE"'
```

**注意**：使用 `--new-run` 参数创建新 DB 快照，不覆盖已有数据；默认增量模式跳过已有 shape。

### 6. 查询采集进度

```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'ps aux | grep "profiler" | grep -v grep'
```

查看日志：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'tail -30 /home/users/liyanzhen01/logs/$(ls -t /home/users/liyanzhen01/logs/ | grep profiler | head -1)'
```

查看 DB 数量：
```bash
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'docker exec grab sh -lc "ls /home/users/liyanzhen01/aiak_ds_tool/data/b200/*.db 2>/dev/null | wc -l"'
```

### 7. 拉取结果到本地

```bash
python3 PRIVATE/scripts/rdev.py sync pull --host b200Dev --dest /home/users/liyanzhen01/aiak_ds_tool/data --src /Users/liyanzhen/baidu/profiler_results/<SUBDIR>
```

## 常见操作模式

### 模式 A：全新批量采集（最常用）

```bash
# 1. 同步代码
python3 PRIVATE/scripts/rdev.py sync push --host ...

# 2. 停止旧进程 + 清理旧 DB
python3 PRIVATE/scripts/rdev.py exec --host b200Dev 'docker exec grab sh -lc "pkill -f profiler 2>/dev/null; rm -rf /home/users/liyanzhen01/aiak_ds_tool/data/b200/*.db /home/users/liyanzhen01/aiak_ds_tool/data/.tmp 2>/dev/null"'

# 3. 启动 grabGPU
# 4. 启动 profiler
```

### 模式 B：增量补采（已有 DB 时）

不清理 DB，直接启动 profiler，自动跳过已有 shape。

### 模式 C：更新代码后重采

```bash
# 1. 停 profiler
# 2. 同步代码
# 3. 启动 profiler（保留 DB，增量模式）
```

## 重要提醒

- rdev.py exec 的 exit code 非 0 不代表远端任务失败——nohup 已启动的进程不受影响
- 采集日志在远端 `/home/users/liyanzhen01/logs/`，带上时间戳
- 默认采集数据在远端 `/home/users/liyanzhen01/aiak_ds_tool/data/b200/`，SQLite DB 格式，必须与 simulator `run_cfg.yaml:data_dir` 保持一致
- 如果 `--config-bundle` 指向的 YAML 解析失败，先本地 `python3 -c "import yaml; yaml.safe_load(open('...'))"` 验证
- profiler 进程在 `grab` 容器内运行，该容器需预先存在并安装 aiak_ds_tool（`pip install -e /home/users/liyanzhen01/aiak_ds_tool`）
- 每次同步后检查远端文件是否到位，特别是新增的配置文件
