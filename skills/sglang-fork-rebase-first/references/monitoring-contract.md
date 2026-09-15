# 监控与平台契约：案例证据

SKILL.md 第 7 步的支撑材料。所有结论都带取证命令和实际回执，供下一轮换基线时直接复用。
案例来自 DSv4.1-Flash 追社区 `dsv4.1` 分支那轮（旧基线 GLM-5.3-Flash 线，24 个厂内提交
筛到 17 个重放）。

## 一、平台探针：`/ready` 静默丢失

### 现象

POD 起来后 `kubectl get pods` 长期 `0/1`，平台侧服务列表里始终没有实例，网关找不到后端。
直连 `curl http://<pod-ip>:8000/ready` 返回 404（不是连不上，是路由不存在）。冷启动 12
分钟，一轮白等。

### 取证

```bash
routes() { git grep -oh -E "@app\.(get|post|put|delete)\(\"[^\"]+\"" "$1" \
  -- python/sglang/srt/entrypoints | sed 's/.*("//' | sort -u; }
comm -23 <(routes "$FORK_TIP") <(routes "$DELIVERY_BRANCH")
```

差集只有 `/ready` 一条。主 server 41 条路由 vs 40 条，dummy server 少的也正好是它。

### 根因链

1. 台账里 `073d8e98d8 | luno-4515 | non-master get_instance_info | replayed | ef075e74b7`
   这行的 evidence 自己写着 `/ready forwarding dropped`——重放时只搬了同一 commit 里的
   `/get_instance_info`，把 `/ready` 当「缺宿主」丢掉了。
2. `/ready` 最早不是通过独立卡片进 fork 的，而是 `147c4e45af luno-4170 Pick aiak code
   0522` 这类批量搬运提交带进来的，而清单消噪规则专门跳过这种提交。
3. 于是正向台账两条路都看不见它。

### 沉淀

- 反向核对（从平台契约回查代码）必须作为独立门禁步骤，不能只做正向台账。
- 「缺宿主」的改动两条出路：补宿主，或在台账里显式登记为阻塞项并写明平台影响。禁止静默
  丢弃。

## 二、启动参数：两个已不存在的参数

### 现象

`sglang serve: error: unrecognized arguments: --collect-tokens-histogram`，容器起不来。

### 取证

```bash
python3 scripts/check_launch_args.py --repo "$NEW_BASE_WORKTREE" --yaml <发版 YAML>
```

对 15.8.1.2 那份老 GLM 交付 YAML 跑，45 个参数里报出 3 个：

```
--collect-tokens-histogram、--disaggregation-zmq-max-sockets、--disaggregation-zmq-ports
```

### 逐条定性

| 参数 | 归属 | 证据 | 处置 |
|---|---|---|---|
| `--collect-tokens-histogram` | 社区已删 | `6344b546c8 Deprecate --collect-tokens-histogram, auto-collect with --enable-metrics (#23595)`；三个 token 直方图现在在 `TokenizerMetricsCollector.__init__` 里无条件创建，分桶走 `--prompt-tokens-buckets` / `--generation-tokens-buckets` | 删参数，能力不丢 |
| `--disaggregation-zmq-ports` | 厂内私有 | `ed3362f22c luno-3729 [Task] 新增feature: 支持启动参数指定zmq端口及MAX_SOCKETS`；`git branch --contains` 只命中 `glm-0312-w4-v0.5.16-replay` | 删参数，台账记「PD 通道端口不可钉，需要时迁 ed3362f22c」 |
| `--disaggregation-zmq-max-sockets` | 同上 | 同上 | 同上 |

八个 ref 都 grep 过 `collect_tokens_histogram`（GLM 交付分支、community main 0908、
community dsv41 0910、我们的分支、v0.5.15 与 v0.5.16 两条老 replay 线、
dsv4-upgrade-main-0717、kimi-k3-0819），全部为 0 命中——说明那行是更老引擎时代的残留。

### 沉淀

**参考 YAML 不是参数契约。** 老交付 YAML 的参数集反映的是它当年那个镜像，不是这次要出的
镜像。每次换基线都要跑一遍反查。

## 三、指标 label 集合

```bash
for ref in "$PREV_DELIVERY_REF" "$DELIVERY_BRANCH"; do
  git show $ref:python/sglang/srt/observability/metrics_collector.py | rg -n "labels = \{" -A 10
done
```

两边逐字一致：

```python
labels = {
    "model_name": get_serving().served_model_name,
    "engine_type": engine_type,
    "tp_rank": tp_rank,
    "pp_rank": pp_rank,
    "moe_ep_rank": ps.moe_ep_rank,
}
# 条件项：enable_priority_scheduling -> labels["priority"]；dp_rank is not None -> labels["dp_rank"]
```

面板 PromQL 按 label 选序列，少一个图就空，所以这一比对是必需项而不是可选项。

## 四、读 `/metrics` 的三个陷阱

### 1 hostNetwork 下 IP 串台

DSv4.1 这轮我在 POD 被回收后仍按老 IP 取数，得出「tokenizer 侧指标全缺」的错误结论。
实际那两个节点 IP 上跑的是别人的服务：

```
10.95.253.83   -> liuwei88-ds-v4-opt-8-deepseek-suhang09-decode-...
10.51.196.204  -> liuwei88-deepseek-kimi-k3-yuliang07-decode-...
```

正确姿势：`kubectl get pods -o wide` 核 IP 归属，再用 `/metrics` 里的 `model_name`
标签（= `--served-model-name` / `MODEL_ID`）二次确认。

### 2 带 label 的指标要等第一次观测

`/metrics` 由 `add_prometheus_middleware` 挂载，走 prometheus multiprocess 模式
（`PROMETHEUS_MULTIPROC_DIR` + `MultiProcessCollector`）。带 labelnames 的
Histogram / Counter 只有 `.labels()` 被调用过才写进 mmap 文件。所以冷启动后没打过请求
时，请求侧指标家族本来就是空的。验证顺序固定：先打一个成功请求，再取 `/metrics`。

### 3 两个 collector 分开判

| collector | 典型指标 | 出现条件 |
|---|---|---|
| `SchedulerMetricsCollector` | `num_running_reqs`、`gen_throughput`、`kv_used_tokens`、`decode_bs_util` | `--enable-metrics` |
| `TokenizerMetricsCollector` | `time_to_first_token_seconds`、`e2e_request_latency_seconds`、`prompt_tokens_histogram`、`generation_tokens_histogram`、`num_requests_total`、`detokenizer_to_tokenizer_time` | `--enable-metrics` + 请求真的走过 tokenizer manager |

`init_metric_collector_watchdog()` 在 `TokenizerManager` 里无条件调用，只按
`self.enable_metrics = get_observability().enable_metrics` 判断，所以只要
`--enable-metrics` 在，collector 一定建得起来。

### PD 分离下的合法不对称

`collect_metrics()` 里：

```python
if not state.ttft_observed:
    ...observe_time_to_first_token(...)          # 两侧都记
elif self.disaggregation_mode != DisaggregationMode.PREFILL:
    ...observe_inter_token_latency(...)          # ITL 只在非 PREFILL 侧记
```

注释写明理由：prefill 节点上这个间隔跨了一次 KV 交接，当 ITL 上报会污染 decode 侧直方图。
这是厂内 luno-3716 两笔的效果（`5063a923df ttft metric in prefill`、
`1058353184 Remove itl metric in prefill`），核对时别把 prefill 侧没有 ITL 当漏迁。

## 五、监控类台账在 DSv4.1 这轮的实际分布

| SHA | 卡 | 主题 | 决策 |
|---|---|---|---|
| `1058353184` | luno-3716 | Remove itl metric in prefill | replayed |
| `5063a923df` | luno-3716 | ttft metric in prefill | replayed |
| `b2151e080e` | luno-4784 | abort metric with multi tokenizer | replayed |
| `094a32d638` | luno-3716 | Fix detokenizer_to_tokenizer metric | replayed with host |
| `a4fbb425ab` | luno-4170 | Fix generation time metrics | replayed with host |
| `7bd9d768ad` | luno-4395 | unified log schema | replayed |
| `13cdb6224c` | luno-4771 | Trace tool integration | replayed in part |

`13cdb6224c` 留下的是 KV-dump 的 TraceManager 及其 io_struct / scheduler 管线，理由是
调试工具、与 `observability/trace.py` 平行实现。**部分重放必须把留下什么、为什么、需要时
从哪笔捡回来写进 evidence 列**，否则下一轮分不清是有意不要还是漏了。

结论性经验：监控类整体倾向必迁，7 笔里 6 笔全量重放。这类改动通常只碰
`observability/` 与 `managers/`，冲突面小，收益是平台可观测性不回退。

## 六、发版 YAML 监控必查项

```
--enable-metrics                     # 缺了 /metrics 不挂载、collector 不建
--enable-cache-report                # cache 命中类指标
ernie-ops.baidu-int.com/feddeploy-name
ernie-ops.baidu-int.com/inference-service-name
ernie-ops.baidu-int.com/model-name
ernie-ops.baidu-int.com/platform     # 四件套必须用平台注册过的服务名
探针路径 = 代码里真实存在的路由（/ready、/health_forward）
```

两条经验：服务名自创会让网关找不到后端（踩过），区分谁的实例靠 `MODEL_ID` 而不是改服务
名；手工 `kubectl apply` 的 fed 不带平台的
`ernie-ops.baidu-int.com/update-by-job` 注解，是否影响监控清单收录未证实，按疑点记录。
