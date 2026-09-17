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

## 七、面板驱动的反向核对：DSv4.1 13 个空面板逐条定性

label 逐字比对只能保证 series 选得到，保证不了「平台画的每张图都有数」。第四节三个陷阱
排除后仍然空的面板，要从**面板清单**倒查，别从指标名猜。

### 取到权威 PromQL

契约是 dashboard 的 JSON，不是面板标题。两条捷径都会失败：`/api/dashboards/uid/<uid>`
被浏览器侧拦（`net::ERR_BLOCKED_BY_CLIENT`）；页面内只读求值环境没有 `fetch` /
`XMLHttpRequest`，也拿不到 `window.grafanaBootData`。可行路径是 UI 的 JSON Model 视图
加剪贴板：

1. 打开 `<dashboard-url>&editview=dashboard_json`
2. 焦点给 Monaco 的隐藏输入区 `.monaco-editor textarea`（直接点 `.monaco-editor` 会报
   `target token mismatch`），全选复制
3. 读剪贴板落盘，再按 panel 解析成「面板 → 指标名 → label 过滤」的映射

```javascript
const walk = (list, section) => { for (const p of list || []) {
  if (p.type === 'row') { walk(p.panels, p.title); continue; }
  const expr = (p.targets || []).map(t => t.expr || '').join(' ; ');
  out.push({ section, title: p.title, expr,
             names: [...new Set(expr.match(/sglang:[a-zA-Z0-9_]+/g) || [])] });
} };
```

DSv4.1 与厂内 K3 用的是**同一个 dashboard**（uid 相同，只换 `var-model_id`），所以
「对齐 K3 的面板状态」= 让我们的 model_id 在同一组查询下有数，不是去抄 K3 的指标清单。
本轮 80 个 panel 里与缺失清单相关的 25 个，逐条定性后落到五类。

### 空面板的五类根因

| 类 | 判据 | 本轮实例 |
|---|---|---|
| A 缺观测点 | 指标族在 `/metrics` 里，但少了某一侧/某一路径 | `kvcache_transfer_time` 只在 prefill 侧观测，D 实例面板过滤 `pod=~".*decode.*"` 恒空；K3 两侧各观测一次 |
| B label 值不匹配 | 族在、label 名在，值对不上面板的等值过滤 | 面板要 `cached_tokens_total{cache_source="storage_MooncakeStore"}`，我们把所有 L3 命中打成扁平 `storage`；K3 打 `storage_{backend}`，backend 取 `cached_tokens_details["storage_backend"]` |
| C label 集由拓扑决定 | 面板过滤的 label 只在某种拓扑下才进 label 字典 | DP 情况四个面板全过滤 `dp_rank="0"`，而 `dp_rank` 只在 `dp_rank is not None`（DP attention / dp_size>1）时加；TP8/dp_size=1 没有，K3 rd4 的 dump 同样没有 |
| D 部署开关未开 | 代码与观测点都在，创建条件不满足 | EPD 专属：`mm_receiver_embedding_transfer_time`、`gpu_buffer_pool_{used,total}_bytes`、`mm_receiver_waiting_requests`（`mm_receiver` 只在 encoder/EPD 参数下创建，1P1D 是 None）；HiCache 专属：`cache_source="host"`；mooncake store 专属：`storage_*` |
| E 计数器未预热 | 带 label 的 Counter 首次观测前不出现在 `/metrics` | `num_aborted_requests_total`、`num_bootstrap_failed_reqs_total`、`num_transfer_failed_reqs_total`、`evicted_tokens_total` 全部在构造时 `labels(**labels).inc(0)`，K3 就是这么做的 |
| F 看板自身写错 | 同一查询对任何 model 都渲染不出来 | `num_used_tokens{...}[1m] / num_running_reqs{...}[1m]`：两侧 range vector 相除，PromQL 非法。报看板 owner，别在引擎侧找原因 |

两个容易误判成缺失的情况：`sum by(...)(num_used_tokens)/sum by(...)(num_running_reqs)`
在空闲实例上是 `0/0`，要有流量才有数；`cache_hit_rate` / `device_cache_hit_rate` 这类
`multiprocess_mode="mostrecent"` 的 gauge 显示的是最近一个 prefill batch 的瞬时值，来
一条无命中请求就掉回 0，不是新指标坏了。

### 对齐不等于照抄坏实现

K3 的 `engine_startup_time` / `engine_load_weights_time` 是
`emit_constants(..., engine_startup_time=0.0, engine_load_weights_time=0.0)` 硬编码 0，
面板长期是 0。我们改成从 scheduler 的启动计时汇总取真值（实测 prefill 97.5s / 48.3s，
与 `startup_time_seconds{phase="scheduler_e2e"|"load_weight"}` 逐位一致），并且必须在
`init_startup_timing_summary` 里发——`emit_metrics_constants` 跑在启动计时汇总之前，
放那儿只能发 0。K3 侧还有 `num_running_reqs_offline_batch` 这类两边都恒 0 的死指标，
本基线没有离线批队列，直接记「结构性不发」而不是造一个永远 0 的 gauge。

## 八、监控代码的高危写法（线上事故 + 评审实证）

1. **属性名错写成 `self.enable_metrics`**。本基线 Scheduler 只有
   `self.metrics_reporter.enable_metrics`。迁过来的监控代码写错属性，第一个真实请求进
   `handle_generate_request` 就 AttributeError → SIGQUIT → 崩溃转储 → P/D 双双重启。
   迁监控代码后先 `rg "self\.enable_metrics"` 全仓核一遍。
2. **时间戳 helper 缺分支隐式返回 None**。`get_request_first_token_forward_time` 只写
   NULL / PREFILL，DECODE 落到函数尾返回 None → `Histogram.observe(None)` TypeError，
   炸在调度器批结果主循环上。同文件的兄弟函数 `get_request_waiting_time` 写了 DECODE
   分支和 `return 0.0` 兜底，照它写。
3. **msgspec Struct 配 Union 形参**。字段只声明在 `TokenizedGenerateReqInput`，而
   `_send_one_request` 的形参是
   `Union[TokenizedGenerateReqInput, TokenizedEmbeddingReqInput]`，无 `isinstance` 守卫
   地赋值会让 embedding / rerank 请求 AttributeError（未声明字段不能动态赋值）。批量
   路径已有守卫时，两条路径必须一致。
4. **跨进程时间戳用 `perf_counter`**。原点按主机，tokenizer 与 scheduler 分布在不同
   node 时差值无意义（恒 0 或落进 +Inf 桶）。跨进程量一律用 wall clock，
   `detokenizer_to_tokenizer_time` 就是这么做的。
5. **计时行落在分支外**。`all_gather_latency` 的计时包住了整个准备块，`dp_size==1` 走
   `finalize_local()` 或 `skip_all_gather` 时把本地准备耗时当成了跨机通信延迟。计时要
   贴着真正的集合通信调用，本地路径保持 0。
6. **除法不兜零**。`decode_bs_util` 除 `max_running_requests` 没保护，而隔壁
   `prefill_chunk_util` 用的是 `max(1, ...)`；同一文件里两种写法就是漏改的信号。
7. **首 tick 时间戳还是 0**。`iter_finish_time - iter_start_time` 在事件循环打点之前触发
   会把进程 uptime 当 `generation_time`（日志里是上亿毫秒），上报前校验并 clamp 到非负。

LLM 评审的 BLOCK 报告要逐条核实再改。本轮 9 条里 7 条成立、2 条是误报：`used_bytes` 用
`self._lock` 被疑属性不存在，实际类里 `self._lock = threading.Lock()` 加
`self._cond = threading.Condition(self._lock)`，是同一把锁；`prompt_calculation_time`
被疑只统计最后一个 chunk，实际 `set_forward_entry_time` 只在字段为 0 时赋值、不覆盖写，
本来就覆盖全部 chunk。误报也要把判据写进回复，别照着改出真 bug。

## 九、不重启 POD 的监控验收闭环

sleep 模式的 pod（主进程 `sleep inf`、探针已删、服务用 `/shared/<start>.sh` 手动起）可以
只热替文件加重起服务，把一次监控改动的验收压到分钟级。可信度靠三方 md5：

1. pod 里的文件 md5 == 老栈某 commit 的版本 → 确认 pod 基线是哪一版；
2. `git diff --numstat <老 commit> <新 commit>` 的逐文件增删行 == commit stat → 确认逐
   文件热替等价于精确打进那一个 commit，不引入跨版本漂移；
3. 替完的 md5 == 本地 worktree → 确认线上跑的与送审的是同一份。

替之前把原文件备份到 `/shared/backup_<round>/<stage>/`，替之后清 `__pycache__` 并用容器
内解释器 `ast.parse` 过一遍语法，再重起服务。

取数按族名（去掉 `_bucket` / `_count` / `_sum` / `_total` 后缀）做前后 diff，并且要在
**造过流量之后**取：本轮一条普通 chat 加一条带图 PD 请求后，族数 101 → 111，反向无丢失；
新增里有两族（`inter_token_latency_seconds`、`spec_verify_calls`）是流量带出来的，不是本次
改动，diff 时要分清。

送审侧一条硬规则：改已推过的评审必须保留原 Change-Id。换消息文件时 hook 会生成新的
Change-Id，icode 会拒并提示 `git fetch ... refs/changes/<nn>/<change>/<ps>` 重放；带着原
Change-Id 再 `git commit --amend` 就是正常的下一个 patchset。
