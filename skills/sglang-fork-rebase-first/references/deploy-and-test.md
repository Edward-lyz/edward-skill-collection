# 部署与测试（外部阶段）

来源：DSv4.1 flash 基线直换（2026-10，分支 ds-dev-rebase-loop-1013，E1P1D1-TP8-EPD，B200）一轮实跑。
静态契约全绿之后，运行期还抓出 4 个缺陷；下表列出每个缺陷哪一道门本该拦住它，后面的步骤就是按这张
表排的。

| 缺陷 | 症状 | 静态契约为什么没拦住 | 现在由谁拦 |
|---|---|---|---|
| BASE_IMAGE 版本锚落后 | 服务一启动就退出：`sglang-kernel 0.4.6.post1 is less than the minimum required version 0.4.9`；整轮 CR 镜像白建 | 硬规则 13 只确认「地址是它」，不看里面装了什么 | `check_base_image_pins.py`，提交 CR 前 |
| 搬来的代码引用社区已重构的符号 | E 角色 health 检查报 `cannot import name 'decode_image'`（社区把它重构成 `patchify_image`） | `from X import 不存在的名字` 不是 F821，契约脚本只看「能力在不在」 | 步骤 9.1 的 import 冒烟 |
| 组件类里读了 Scheduler 才有的字段 | 非 PD 部署的 Prefill 读 `self.server_args.enable_metrics`，调度器退出 | PD 路径不经过这行；同 SKILL 常见坑最后一条，这一轮在另一处复发 | 步骤 7 的集中式起服务或静态检查，对每张监控卡都做 |
| 社区改了行为，厂内测试用例随之失败 | 功能回归多出 9 个失败：社区把 V4.1 工具调用约束换成 xgrammar 内置 XML 约束，`tool_choice=required` 时非标识符参数名被改写 | 行为变化不改代码结构，契约和残差都看不到 | 步骤 9.3 的功能回归，逐用例对上一发版差分 |

## 9.1 起服务之前

1. `check_base_image_pins.py`（见步骤 6）零退出码。BASE_IMAGE 取与新基线同代的社区 nightly；沿用旧厂内
   dev 基础镜像，torch / sglang-kernel 一定落后。这一轮最终用的是
   `iregistry.baidu-int.com/lyz/sglang-community-nightly:nightly-dev-cu13-20261011-d32d8fa0`，用户逐字确认。
2. 在 BASE_IMAGE 里把候选 tip 覆盖上去，对三个角色的入口模块逐个 `python3 -c "import …"`，再跑
   `check_launch_args.py` 对发版 YAML 反查。E 角色单卡就能起到 health，最便宜，也最先暴露悬空引用。
3. 启动参数的兼容性有一类 argparse 看不出来：模型维度约束和特性组合。V4.1 Flash 的 moe_intermediate
   是 2304，W4A4 megamoe 要求 512 的倍数；DSPARK + megamoe + swa-bounded-replay 组合直接崩；CP 不支持
   vision。这类参数按「去掉、记入报告 3.2.2、写明根因是否已隔离」处理，不要在报告里写成「已验证不兼容」。
   参考 YAML 不是参数契约：P 的并行方式也要重排（v15.9.3.1 是 tp4/ep4 + `--fake-dp 2`，新基线不认
   `--fake-dp`，8 卡独占时改 tp8/ep8，D 保持 tp8/dp8/ep8）。

### 9.1.1 社区单测是第四道门

第二轮（基线直换到 1017 main）起，起服务之后、跑 ipipe 之前，把候选 tip 的改动文件拷进已部署的 P/D pod，
用 `scripts/run_unit_files.sh` 逐文件跑 `observability entrypoints function_call managers disaggregation parser`
的 CPU 单测。整目录跑会被第一个收集错误或挂起的文件拖住，所以脚本是一文件一进程加超时。结果落在
容器重启也不丢的卷上（`/shared`），因为启动探针一直失败的 pod 约每 50 分钟重启一次，`/tmp` 随之清空。

这一道门第二轮抓出两类问题，静态契约和 ipipe 都发现不了：

- **真缺陷**：社区把多 tokenizer 的批输出拆分改成按 dataclass 字段通用切片，厂内给 `BatchStrOutput` 加的批级
  标量 `detokenize_completed_time` 被当成逐请求列表切，Detokenizer 报 `object of type 'float' has no len()`
  退出，P 和 D 的 `/health_forward` 永远 503。修法是把批级标量放进 `_NOT_SPLIT_FIELDS` 并整份带进子批
  （`test_multi_tokenizer_mixin.py` 已补用例）。以后给 `Batch*Output` 加字段，先问它是批级还是逐请求。
- **测试桩与新代码不匹配**：厂内加的 `self.metrics_reporter.enable_metrics`、`iter_start_time`、
  `_build_metrics_labels` 等读取，让社区用 `SimpleNamespace` / `__new__` 搭的桩缺属性。逐个补桩，不要给产品代码
  加 `getattr` 兜底；真实 Scheduler 在 `__init__` 里都有这些属性。

另有一类要判断是不是「该改测试」还是「该改代码」：厂内行为刻意偏离社区时（例如 luno-4784 把中止计数从发起时
挪到生效时），改测试并在注释里写明；社区测试钉住的是社区想要的行为时（例如事件循环里的轮询顺序），厂内改动
应该让路，不要改测试。

## 9.2 部署

- kubectl 经 virtualMachine 开发机；命名空间、kubeconfig 取该机已有配置。先 `kubectl apply --dry-run=server`
  三份 YAML。
- FedDeployment 名必须含 `deepseek`，监控按这个关键词抓 pod。沿用团队前缀，例如
  `liuwei88-ds-v4-opt-8-deepseek-<user>-<tag>-{encode,prefill,decode}`。
- model_id 取 AIQA 的 `GET /api/v1/modelid/feddeployments` 里 `unused_model_ids` 的槽位，不抢别人占着的；
  部署完成后 `GET /api/v1/model/status?model_id=M` 的 `engine_ready` 与 `as_ready` 都为 true 才算就绪。
- 要用别人的节点：请对方自己缩容；删除 FedDeployment（先缩到 0 再删）每一条都要用户逐条输入「我同意删除」，
  授权只覆盖点名的那几个 fed。
- 每修一个缺陷都要 CR → 新镜像 → 三角色滚动重部署，代价高。缺陷攒一批再出镜像，但功能回归要先跑（9.3）。

## 9.3 测试顺序与判读

触发全部走 `ipipe-run-pipeline` skill。集群环境经 AS（填 model_id）；开发机直连的环境不经 AS，用 `inference_host`
指向 router。默认顺序（用户指定）：

1. 精度 OpenCompass（think / nothink）。
2. FC 精度 EvalScope general_fc（think / nothink）。基线是 V3.2，count 类指标对基线不达标时，上一发版自己也
   不达标，就以上一发版为比较对象，并如实写「对 V3.2 基线不达标」。
3. 功能回归（think / nothink 各一次）。逐用例对上一发版差分，新增失败逐个定性（代码缺陷 / 用例本身波动 /
   环境），不要只看失败总数。这一轮 4 个缺陷里只有它抓到了行为变化；如果环境紧、预计要多轮重部署，把它提前到
   第一位，因为它最便宜、最先暴露问题。
4. 长稳：`stress` 场景，默认值见 ipipe-run-pipeline 的「Stress (长稳) defaults」：12 h，数据集取最近 10 次
   执行里出现最多的，发压 pod 为 Prefill pod。占用环境 12 h，触发前要用户确认并给 qps。

判读规则：阶段状态不是结论，平台判「不达标」的原样写进报告（这一轮 OpenCompass think 的 SuperGPQA 71 对基线
77）；每个结果写明用的是哪个镜像 tag，修复后没有重跑的项标「推断，未实测」；pipeline 日志按
ipipe-run-pipeline 的方法取，不要用 `result` 下载 GB 级日志。

## 9.4 经验补充（1017 轮）

- 二次追新：上一轮已审的候选栈整套 cherry-pick 到新 main，再补新卡，冲突很少；pick 前先看新 main 的
  pyproject，核对 base 镜像的 sglang-kernel / torch / flashinfer 是否覆盖（`check_base_image_pins.py`），
  版本不够就换更新的社区 nightly，BASE_IMAGE 要用户逐字确认。
- 取镜像：`cr_image.py` 可能一直报 NO-BUILD-YET。改用 `ipipe-cli build history --module <模块>` 找
  pipelineConfId 对应本分支的最新构建，再 `ipipe-cli build tasks --pipeline-build-id N`，读「构建镜像」任务的
  `outParams.NORMAL_IMAGE_VERSION`。
- 社区重写的批处理会让厂内批级标量字段（如 `detokenize_completed_time`）被按 dataclass 字段切片，表现为
  Detokenizer 退出、`/health_forward` 一直 503。部署后先看 P/D 的 `/health_forward`，不通就看进程日志。
- 检测器/语法类改动先在集群 pod 里做探针：把文件打包同步进 pod（`COPYFILE_DISABLE=1 tar`，rdev sync 到
  virtualMachine，`kubectl cp`），在 pod 里跑 xgrammar 单测和含 `$ # & < "` 的参数名探针，再出镜像。
- 带图请求：`scripts/mm_probe.py <P_IP> <D_IP>` 在 D 内运行，扮演路由给 P、D 发同一 `bootstrap_room`
  的带图 chat 请求，回答写进报告。PE 不分离时 P 自己做图像编码。
- 长稳（压测自动化）的「参数校验」阶段有 `model_path_local` / `model_nextn_path_local` 两个手填参数，默认值是上一个人
  遗留的（如 GLM 路径 + V4-Pro nextn），与当前集群类型不匹配会让阶段失败。skip_deploy_env=true 时把两个都置空
  （`--set model_path_local= --set model_nextn_path_local=`）即跳过校验。
- 结果日志太大时，用 `ipipe-cli build job` 取 logonline URL，流式读取并只保留关键行，或用 Range 读尾部。
- 修复后的最终镜像应把精度/FC/回归整套重跑，报告只列最终镜像的结果，更早镜像的结果只在一句话里说明。

## 9.5 没覆盖到的

性能压测。不要把它们写成已验证；报告里写「未做」。
