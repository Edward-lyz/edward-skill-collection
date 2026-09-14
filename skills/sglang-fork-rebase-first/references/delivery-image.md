# 交付镜像四件套

厂内 aiak_sglang 的镜像入口固定四个文件。`docker/` 保持社区原样，模型专属资产才开
`docker/<model>/` 子目录（K3 的 DeepEP patch 与 cu12/cu13 Dockerfile 放在那）。

| 文件 | 作用 |
|---|---|
| `ci.yml` | 仓库根目录的流水线入口，`build.command: sh build/build.sh`。所有厂内交付分支上是同一个 blob |
| `build/build.sh` | 流水线打包入口：把 `../aiak_sglang/` 整棵树 tar 成 `output/sglang.tar.gz` |
| `dockerfile/Dockerfile` | 交付镜像层，从内部 base 起 |
| `dockerfile/gpu_requirements.env` | wheel 清单，被 Dockerfile COPY 进镜像做 `pip install -r` |

build.sh 决定了 docker build context 是仓库的**父目录**，所以 Dockerfile 里每个 COPY 都
写 `aiak_sglang/...`。四件套的路径、ci.yml 与 build.sh 的内容都跟着流水线，不要改。

ci.yml 缺了的表现是流水线一开工就停：`[ERROR]can not get ci.yml from iCode`。社区树里
没有这个文件，所以基线直换之后它一定缺，而且**每个 change 的 CI 各自 checkout 自己那条
ref**，栈里排在 ci.yml 之后的卡才继承得到。把四件套那一卡放在栈底，16 张卡的 CI 一次
都能找到它。

## 取模板

```bash
for b in $(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/remotes/origin | head -20); do
  printf '%s | %s | %s\n' "$(git log -1 --format=%ad --date=short "$b")" "$b" \
    "$(git show "$b:dockerfile/Dockerfile" 2>/dev/null | head -1)"
done
```

FROM 行一列排开，挑 base 同类、日期最近的那条当模板。同类的判据是 base 镜像种类：社区
镜像搬进 iregistry（`lmsysorg/sglang:*`）还是厂内 aiak-inference 镜像。两类模板的 COPY
策略和继承项都不一样，抄错类比抄旧版更贵。

## 两种 COPY 策略

| 策略 | 写法 | 用在 |
|---|---|---|
| 整支替换 | `RUN rm -rf /sgl-workspace/sglang` + `COPY aiak_sglang /sgl-workspace/sglang` + editable 重装 | 交付要整棵树（含 csrc、配置、非 .py），base 与交付基线同源。K3 线用这个 |
| Python 覆盖 | `COPY aiak_sglang /tmp/aiak_sglang` → `cp --parents` 覆盖所有 `*.py` 与 `scripts/` → 写 `aiak-last-commit` 留痕 → 删 /tmp | 只改 Python 层，要保住 base 里编好的 kernel 产物。GLM 社区 base 线用这个 |

Python 覆盖下非 .py 文件留在 base 的版本；base 的社区 commit 与交付基线不同源时这里会留
残差，值不值得取决于交付改了什么。

## 继承清单

K3 = aiak-inference base 那条线的模板，GLM = 社区镜像 base 那条线的模板；「类」按 SKILL.md
的三分法，处置列是 DSv4.1（base 换成社区 dsv4.1 dev 镜像搬进 iregistry）那次的判定。

| 步骤 | 出处 | 类 | DSv4.1 处置 |
|---|---|---|---|
| `FROM <base>` | 两条线 | 版本锚 | 换成本次交付指定的内部 base |
| apt 代理 heredoc（`RUN cat >/etc/apt/apt.conf.d/proxy.conf <<EOF`） | K3 | 运行时通用 | 留，照抄 |
| 时区 symlink | 两条线 | 运行时通用 | 留 |
| `scripts/*.sh` 补执行位 | K3 | 运行时通用 | 留（先确认新基线有 `scripts/`，`find` 找不到目录会让构建失败） |
| tokenspeed_mla 精确除法 patch | K3 | base 专属 | 删。那个包只在 aiak-inference base 里，且硬编码 `/usr/local/lib/python3.12/dist-packages` |
| pip 内网 mirror + trusted-host | 两条线 | 运行时通用 | 留 |
| deep_gemm 预编译缓存 tar | 两条线各有自己的包 | base 专属 | 删。缓存按模型编；换模型用 `python3 -m sglang.compile_deep_gemm --model <ckpt> --tp 8 --trust-remote-code` 重编后再挂 |
| prestop py-spy dump 脚本 | K3 | 运行时通用 | 留，平台退出钩子 |
| `gpu_requirements.env` COPY + `pip install -r` | 两条线 | 运行时通用 | 留 |
| AttentionStore SDK wheel | 两条线（cuda12 / cuda13 两个变体） | 版本锚 | 按新 base 的 cuda 版本取 cuda13 那个 |
| FlashKDA wheel | K3 | base 专属 | 删。K3 的 `--linear-attn-prefill-backend flashkda` 依赖，MLA + DSA 用不到 |
| mooncake transfer engine wheel | K3 单独 RUN / GLM 放在 env 文件里 | 运行时通用 + 版本锚 | 留，取 cuda13 变体（PD 分离的传输后端） |
| deep_ep / deep_gemm / flash_mla 覆盖安装 | GLM | base 专属 | 删。社区 dev 镜像自带本版本 kernel，覆盖等于降级 |
| `jsonschema_rs` / `distro` / `decord` / `PyNvVideoCodec` | K3（注释写明「本该在 base 里」） | 运行时通用 | 留。社区 base 确实没有这几个 |
| flashinfer trtllm-gen MoE warmup | K3 | 运行时通用 | 留，自带 `|| echo` 兜底 |
| editable 安装 + `SETUPTOOLS_SCM_PRETEND_VERSION` | 两条线 | 版本锚 | 版本改成构建时读 `importlib.metadata.version("sglang")`；它看 site-packages 的 dist-info，`rm -rf` 源码目录之后照样读得到 |
| `msit_llm` + `onnx --no-deps` | 两条线 | 运行时通用 | 留，精度排查工具 |
| `WORKDIR /sgl-workspace/sglang` | 两条线 | 运行时通用 | 留 |

两条额外约束：`pip install -e --no-build-isolation` 要求 base 里已有 setuptools_scm，换社区
base 时先确认；apt 代理那段 heredoc 用的是 BuildKit 1.4+ 语法，厂内流水线在跑，照抄即可。

## DSv4.1 实账

自创的 `dockerfile/Dockerfile.dsv41` + `dockerfile/build_dsv41.sh`（48 行，镜像内现编
wheel）整卡被打回；改成四件套后是 110 行，其中 `ci.yml` 与 `build/build.sh` 与模板同 blob。
第一版漏了 ci.yml，流水线 `can not get ci.yml from iCode` 才暴露，补的时候顺手把这一卡挪
到栈底——那次 16 张卡全部换 SHA、一次 push 回执 `updated: 16`，Change-Id 集合不变、没有
多开 change。
