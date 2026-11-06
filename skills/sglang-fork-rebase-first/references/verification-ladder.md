# 三个验证点

重放的正确性判据不是「像某份规范」，而是**与源提交等价，除了上游改了接口的地方**。这句话把
一个开放问题变成差分问题：判准是源分支本身，不用手写期望值。三个验证点按顺序过，每个只回答
一个问题，也各有拦不住的东西。

| 验证点 | 问题 | 怎么跑 | 拦不住 |
|---|---|---|---|
| 1 字段都能取到 | 平台要的字段还在不在 | `verify_platform_contract.py` | 值失真、观测点位置错 |
| 2 line-by-line 一致 | 选中的 PR 内容都落地了吗 | `replay_residual.py` | 语义等价但写法不同的改写 |
| 3 起服务实测 | 值和能力真的对吗 | 起 EPD 服务打请求取数 | 要真实部署，分钟到小时级 |

## 验证点 1：所需的字段都能够被 get 到

```bash
python3 "$SKILL_DIR/scripts/verify_platform_contract.py" --repo "$WORKTREE" --ref HEAD \
  --contract "$SKILL_DIR/assets/contract-dsv41.json" -o "$ARTIFACTS/contract-verify.md"
```

六类字段：主 server 与 dummy server 路由、有定义且有写入点的指标族、按 rid 的 stage trace 行、
token id dump 点、日志 schema、厂内环境变量读取点。**完成判据：退出码 0。** 缺项分两种报法——
族名不存在报 MISSING，族在但没人写它报「无写入点」，面板上都是 No data 但修法不同。

拦的是整块漏迁：族名漂了、探针少一条、计数器没预热、trace 行断在某一段。拦不住值失真。

## 验证点 2：对比源 PR 集，line-by-line 一致

```bash
python3 "$SKILL_DIR/scripts/replay_residual.py" --repo "$WORKTREE" \
  --new-base "$NEW_BASE_SHA" --tip HEAD --source-commit <选中的每一笔> \
  --accept "$ARTIFACTS/accepted-residual.tsv" -o "$ARTIFACTS/residual.md"
```

两侧各算净改动行集合再求差。**完成判据：漏迁与「该删没删」两类为零**，例外只有一种——上游改了
接口，且例外清单里那条理由必须点名上游那处变更（没写理由的规则脚本直接拒绝）。「新造」不进
判据，整行搬家会让它出假阳性。

DSv4.1 实测：18 笔源提交 vs `main..codex/dsv41-replay-on-main-0921`，净加 5,264 / 5,269 行，
残差 13 行：

| 类 | 行数 | 解释 |
|---|---:|---|
| 漏迁 | 4 | 全在 `http_server.py`：`@app.get("/ready")` 别名、它的 507 分支和两行注释。社区已自己收了 `/ready`，重放时改成保留社区 handler 再叠排水，这 4 行有意不搬 |
| 新造 | 9 | 5 行是上面那个改写的新 `ready()`；4 行是整行搬家造成的假阳性（见下） |
| 该删没删 | 0 | — |

例外清单见 `assets/accepted-residual-dsv41-main.tsv`：上游那处接口变更是社区 main 自己新增了
`/ready`（`async def ready()` 调 `tokenizer_manager.is_ready()`），所以厂内那版「把 /ready 挂成
health_generate 的别名」整段作废，改成保留社区 handler、把排水判断叠在它前面。挂上清单后漏迁
归零，退出码 0。

这一版检查器是改过一次的。第一版把「源侧逐笔 diff 的并集」当作源侧意图，报出 33 行漏迁；逐条
读完发现 20 行是中间态——前一笔加进去、后一笔又改掉，重放侧只有最终形态，当然对不上。改成
**加集减删集**（净意图）后降到 4 行。这件事本身说明：检查器的判据也要被检验，而检验它的唯一
办法是把每条输出都读懂。

已知盲点：**整行搬家在源侧自相抵消**。某笔把一行加在 A 处、后一笔原样移到 B 处，源侧加集与
删集各含一次、相减为空，重放侧却有一次，于是报成「新造」。所以漏迁与该删没删是必须归零的信号，
新造是复核清单。

## 验证点 3：实际启动 EPD 服务，测试能力和字段

前两个验证点只看代码长什么样，看不出值对不对。第三个要真起服务：EPD 三角色拉起来、打一个带图
请求、然后逐项取数——探针回什么码、`/metrics` 多出哪些族、rid 能不能串起全链路、两份 token id
能不能 dump 出来且与平台 dump 逐位一致。判据取「PD 两端该有的有、该没有的没有」这类可预期的
不对称：P 侧要有 TTFT、P 侧不该有 ITL、带 label 的计数器在空闲实例上是 0 而不是 No data。
完整步骤、逐项判据与取数陷阱见 references/epd-runtime-acceptance.md。跑不起来记 deferred，
不记 pass。

## 怎么知道验证点 1 自己是对的：变异探针

「核对通过」只有在核对会因为真缺陷变红时才有意义。`verify_mutations.py` 拿一个已通过的分支，
逐个种入**一类真实发生过的缺陷**，跑验证点 1，看它是否变红。变异表里每行都对应线上见过的
形态，不是凭空造的语法错。

这一轮 10 条变异跑出了核对脚本自己的一个 bug：删掉主 server 的 `@app.get("/health_forward")`
居然过了。原因是路由只按路径记 key，而 EPD 的 encode server 上也有同名路由，两处路由并成了
一项，删一个还剩一个。改成按「上一级目录/文件名 + 路径」记 key 后变红，主 server 路由也从
3 项变成 5 项——契约同时变严了。

当前结果：8 条应拦的全部 CAUGHT，2 条登记在案的盲点 SURVIVED。

| 变异 | 结果 |
|---|---|
| 删主 server 探针路由 / 删 dummy server 自省路由 | CAUGHT |
| 改指标族名 / 删计数器预热 | CAUGHT |
| 删一条 rid trace 行 / 删 token id dump 点 | CAUGHT |
| 删日志组件前缀 / 改厂内环境变量名 | CAUGHT |
| 跨进程时间戳换回 `perf_counter` | SURVIVED（盲点，交给验证点 3） |
| 除法去掉兜零 | SURVIVED（盲点，交给单测或验证点 3） |

盲点不是放着不管，是**明确移交给验证点 3**：值失真那一类静态永远看不见，只能靠造流量后的
`/metrics` 前后 diff，或者该指标自己的单测。把盲点写进变异表，好处是下一轮谁想把它补上时，
表里已经有一条现成的失败样例。

## 判据顺序

1. 验证点 1 零退出码——不过就别往下走，缺的东西先补或先登记。
2. 验证点 2 漏迁与该删没删归零，例外逐条点名上游接口变更。
3. 变异探针全部与预期一致——不用每轮跑，改过核对脚本或加过能力类之后必须跑。
4. 验证点 3 在有机器时跑，跑不起来记 deferred，不记 pass。
