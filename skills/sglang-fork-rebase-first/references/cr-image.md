# CR 提交与镜像地址

2026-10-10 在 baidu/hac-aiacc/aiak_sglang 上用 ipipe-cli 0.5.0 实测。

## 镜像从哪来

每个推到 refs/for 的 change 触发 `ChangePipeline-dev/dp 分支（集成流水线）【GPU】`
（pipelineConfId 2205943）。它的阶段里「构建镜像」（AGILE_SHELL）用 CR 的 ref 打出一个
镜像，地址在该任务的 `outParams.NORMAL_IMAGE_VERSION`，`message` 里同一个值：

```
iregistry.baidu-int.com/hac_test/aiak-inference-sglang:zhongyuanming_20261008_174307
```

整条流水线状态可以是 SKIPPED 或 FAIL 而「构建镜像」仍然 SUCC（实测 build 273187211 总体
SKIPPED、镜像 SUCC；build 273165601 镜像 SUCC 但「版本上报&CR质检」FAIL）。所以取镜像
看这一个任务的状态，不看整条流水线。

## 手工等价命令

```bash
ipipe-cli build commit --module baidu/hac-aiacc/aiak_sglang --revision <tip-sha|change-id>
ipipe-cli build tasks --pipeline-build-id <id>   # 找 jobName == 构建镜像
```

`build commit` 返回按 commit 触发的全部构建，脚本按 pipelineConfId 过滤后取 buildTime
最大的一条（最新 patchset）。patchset 刚推上去时可能还没有构建，脚本按 NO-BUILD-YET 继续轮询。

## 不要混淆

- BranchPipeline（rb-ds_* 发布分支）的「打包项目到bos」产出的是 `sglang.tar.gz` 的 BOS
  地址，不是镜像。CR 阶段只认 ChangePipeline 的 NORMAL_IMAGE_VERSION。
- 镜像里装的是 tip 那个 change 的整栈代码，前提是四件套卡在栈底（SKILL.md 第 6 步）。
  缺 ci.yml 时流水线在 `can not get ci.yml from iCode` 停下，根本没有镜像任务。
