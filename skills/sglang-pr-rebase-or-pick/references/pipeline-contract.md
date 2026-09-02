# 跨组件契约

`merge-case-taxonomy.md` 的 9 类缺陷，契约两端都在仓库里，所以门禁扫得到。这一份讲另一
类：契约的另一端在别的团队的进程里，也就是推理链路网关、评测框架和发版 YAML。一次上游合
并会同时换掉三处东西：reasoning parser 的实现、chat template 的消费逻辑、`protocol.py`
里请求字段的规范化，而这三处恰好都压在同一条契约上。这类问题 `git diff` 看不出来，静态
门禁一个都报不出来，因为最终树自洽、服务起得来、直连引擎还正常。唯一的发现手段是把同一
条请求打穿整条链路，逐层比对输出。

## 一、先做「谁在加工数据」的实验，再动代码

三个观测点必须都建立，缺一个就会误判责任方：

1. 裸 prompt 与裸 output token。用引擎自己的 tokenizer 渲染同一条 messages 并打印 token
   id，再把 output 的原始 token 落盘，不经过任何 detector。这一层回答「模型和模板到底吐
   了什么」。
2. 直连引擎端口。router 或 tokenizer manager 的 HTTP 端口，绕过网关。这一层回答「引擎的
   OpenAI 兼容层切成了哪些字段」。
3. 经网关。本次是 AS 网关 `10.178.29.70:80`。这一层回答「业务实际收到什么」。

同一条请求（同 prompt、`temperature=0`、同 `max_tokens`）在三个观测点各打一次，把三份输
出 diff。哪一层的字段和上一层不一样，责任方就锁定在这两层之间。只建立观测点 2 和 3，会
把模板的行为算到引擎头上；只建立 1 和 3，会把引擎兼容层的行为算到网关头上。

反向对照和正向观察一样重要，而且更有说服力：改一版镜像，只动引擎侧的输出形状，再看网关
输出有没有跟着变。跟着变，网关就是透传的。输出「看起来对」可以是任意一层修补出来的，不
能当证据用。

反面教材，本次最贵的教训。patchset 9 / 10 / 11 三版都建立在「网关会按 `<think>` /
`</think>` 标记自行切分」这个从没验证过的假设上，写的是在引擎侧 passthrough 拼标记的代
码。ps10 镜像下网关原样返回了只有 `<think>` 没有 `</think>` 的 content；ps11 补上
`</think>` 之后网关原样返回了双标记。这两轮实测恰好反证出网关既不切分也不修补，只透传引
擎给的字段。ps12 把三版代码全部删掉，只留一个 early return。代价是三轮镜像打包和三次
pod 重启。教训只有一句：跨组件问题先用最小实验确定谁在加工数据，再动代码；router 直连就
是那个决定性实验手段，它把网关从变量里摘出去。

## 二、GLM-5.3-Flash 思考链契约的实测事实

每条都注明出处。换 checkpoint 或换链路版本时按同样的方式重测一遍，不要直接沿用结论。

1. chat_template.jinja（257 行，从 pod 内 `/GLM-5.3-Flash-20260827/` cat 出来）只读
   `reasoning_effort`，白名单只有 `low` 和 `high`，其它值一律回落 `max`；模板里根本没有
   `enable_thinking` 和 `thinking` 变量。所以客户端传
   `chat_template_kwargs.enable_thinking` 对 prompt 毫无影响，用
   `rg -n 'reasoning_effort|enable_thinking' chat_template.jinja` 一条命令就能确认。
2. 模板末尾是无条件的 `<|assistant|>{{- '<think>' -}}`。裸 prompt 实证 16 token：
   `[gMASK]<sop><|system|>Reasoning Effort: Max<|user|>你是什么模型?<|assistant|><think>`
   其中 `<think>`（token 154841）是 prompt 的最后一个 token，不在 output 里；output 只
   有「思考文本 + `</think>` + 答案」，开标记从来不出现在生成侧。
3. 引擎侧 `Glm45Detector` 声明 `thinks_internally=True`、
   `reasoning_default="enable_thinking"`，正则是 `(<think>)*(.*)</think>`，正是为上面这个
   「只有闭标记」的形状设计的。这两件事必须一起看：模板把开标记放进 prompt，detector 就
   必须按 thinks_internally 处理；合并只改动其中任何一侧都会破契约，而且两侧的文件离得很
   远，diff 上不会挨在一起。
4. 网关只透传，不切分也不修补。证据是第一节的 ps10 / ps11 反证，不是读网关代码得到的。
5. 真因在引擎侧：`_get_reasoning_from_request()` 返回 False 时就不切分。而 `protocol.py`
   的 `normalize_reasoning_inputs` 会从转发过来的 reasoning 字段合成
   `chat_template_kwargs`，所以网关流量天然带这个字段，即使客户端一个思考参数都没传。这
   就是「同一条请求直连 IP 正常、走网关不正常」的真实来源，看到这种差异不要第一反应怀疑
   网关。
6. `thinking: {"type": "enabled"}` 和 `{"type": "disabled"}` 是网关协议字段，引擎的
   `ChatCompletionRequest` 里根本没有这个字段，Pydantic 直接忽略，上游社区 SGLang 同样没
   有。所以网关侧的协议字段名和引擎侧的字段名要分开记，混着说必然得出错误结论。
7. 这个 checkpoint 没有任何写法能真正关闭思考，因为模板不接受关闭，只能用
   `reasoning_effort: "low"` 把思考压短。这一条要报给链路 owner，不要在引擎里造一个假的
   开关去迎合调用方。

## 三、思考与工具调用这条链的合并硬规则

`--reasoning-parser <name>` 不许因为「看起来只是输出格式化」就从启动参数里删掉。实测证
据：删掉后 function call 完全失效，同一条请求在参考 pod（带 parser）上 78 token 就发出
tool call，我们这边（不带）8000 token 打满、`tool_calls=0`、思考文本原地重复；把
`tool_choice=none` 一加立刻恢复正常，说明坏的是 tool call 路径而不是模型或权重。这条和
M9 的区别在于，flag 两端都在仓库里时 `flag_inventory.py` 扫得到，而这里删的是发版 YAML
里的启动参数，仓库门禁完全看不见，只能拿参考 pod 做 A/B。

`--enable-strict-thinking` 依赖 reasoning parser 才有意义：它通过 xgrammar 的 token
filter 屏蔽思考段内的 `<tool_call>` 等标记，而且是 `SGLANG_MAX_THINK_TOKENS` 唯一的生效
入口。这两个参数是一组，不能只删一个，也不要只加一个就宣称等价。

精度评测里的「结果为空」先看 finish_reason 和 output_len 再谈链路。本次 36 个空结果里 29
个是 `finish=length` 加 `output_len=65536~65539`，是思考把 token 预算吃干了：评测没传
`max_tokens`，引擎按 `max_new_tokens=65536` 跑，`temperature=1.0`，模板给的又是
`Reasoning Effort: Max`。这类属于采样与预算问题，不是合并缺陷，写进 CR 时必须和合并引入
的问题分开归因，否则会为了一个不存在的 bug 去改代码。

## 四、合并后必跑的验证矩阵

非流式 8 种写法，逐条打同一个 prompt：

```text
不传任何思考字段
thinking.type=enabled
thinking.type=disabled
chat_template_kwargs.enable_thinking=true
chat_template_kwargs.enable_thinking=false
chat_template_kwargs.thinking=true
reasoning_effort=low
reasoning_effort=none（非白名单值，验证模板回落到 max）
```

流式重跑其中 5 种（不传 / thinking enabled / thinking disabled /
`chat_template_kwargs.enable_thinking=true` / `reasoning_effort=low`），再加 router 直连
3 种，用来把网关摘出去做对照。

判定点三条，缺一条都不算通过：`reasoning_content` 是独立字段而不是拼在 content 里；
content 里零残留 `<think>` 和 `</think>`；同一个 prompt 在所有写法下 reason 长度和
content 长度一致（本次基线 reason=337 / content=105，router 直连三种写法同样是这两个值）。

检查命令固定这几条，把响应存成文件再查，不要在管道里目测：

```bash
jq '.choices[0].message | keys' resp.json
jq -r '.choices[0].message.reasoning_content | length' resp.json
jq -r '.choices[0].message.content | length' resp.json
jq -r '.choices[0].message.content' resp.json | grep -c '<think>'
jq -r '.choices[0].message.content' resp.json | grep -c '</think>'
```

本次全绿的形态是 `keys` 里同时有 `content` 和 `reasoning_content`，两条 `grep -c` 都是
0（记作 open=0 close=0）。

必须写下这个坑：终端里单行 JSON 会把 `reasoning_content` 和 `content` 在视觉上连成一片，
本次因此误判过一次「网关没切分」，实际字段是分开的。一定要用 `jq` 取字段判定，不要肉眼
看整行输出。

## 五、这一类问题在流程里的位置

门禁全绿只说明仓库内部自洽，跟这条契约通不通没有关系。跨组件契约要在交付清单里单独列成
一项，和门禁表并列，写清用了哪三个观测点、跑了矩阵里哪几种写法、基线长度是多少。

验证环境是 P / D 两个 pod 加一个 router；抢资源、起 pod、拷脚本这些操作不属于本 skill，
见 `dev-machine-remote` skill。环境跑不起来就按 L11 记 deferred，并点名具体哪几种写法没
验证过，不要因为「router 直连正常」就推断整条链路正常。这两件事在本次是分离的：ps9 到
ps11 期间直连一直是正常的，坏的一直是走网关那条路。
