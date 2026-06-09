---
name: lsp-callgraph
description: |
  使用 Language Server Protocol 的 callHierarchy 从目标函数快速生成交互式
  HTML 调用图。适合首次接触项目、梳理入口函数、分析跨文件调用主干。
  触发词：LSP 调用图、callgraph html、项目导航图、调用栈 HTML。
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# LSP Callgraph — 目标驱动调用图

## 目标

从一个 seed 函数出发，用 LSP `callHierarchy` 做有限 BFS，生成可交互
HTML。不要扫全仓库。优先用于项目首次导航和入口函数阅读路线生成。

## 依赖

- Node.js
- 对应语言的 LSP server
- Python 推荐命令：

```bash
npx --yes --package pyright pyright-langserver --stdio
```

## 授权说明

本 skill vendored Crabviz renderer/wasm/assets。Crabviz 使用 AGPL-3.0，
license 文件位于 `assets/crabviz/LICENSE.txt`。

## 命令

```bash
python3 skills/lsp-callgraph/scripts/lsp_callgraph.py \
  --root /path/to/repo \
  --seed-file relative/or/absolute/file.py \
  --seed-line 144 \
  --seed-character 8 \
  --language-id python \
  --language-name Python \
  --lsp-command 'npx --yes --package pyright pyright-langserver --stdio' \
  --direction outgoing \
  --depth 3 \
  --max-nodes 80
```

`--seed-line` 是 1-based，`--seed-character` 是 0-based。
不传 `--output` 时，默认写到 `/tmp/lsp-callgraph/`。

## 工作流

1. 用 `rg`/`nl -ba` 找入口函数位置。
2. 从入口生成 `outgoing depth=2`。
3. 如果主干太浅，再对关键节点生成 `depth=3`。
4. 输出 HTML 和同名 `.json` payload。
5. 解析 JSON，总结模块边界、关键节点、断裂点。

## 解释规则

- `nodes` 越多，图越难读。默认 `max_nodes=80`。
- LSP 无法解析动态 dispatch、注册表、反射调用；这些属于断裂点。
- 全文件 overview 不使用本 skill；改画 import/file dependency graph。
- 生成失败要直接报错，不做 AST/code2flow hidden fallback。

## 示例

```bash
cd /Users/liyanzhen/baidu
python3 PUBLIC_REPO/edward-skill-collection/skills/lsp-callgraph/scripts/lsp_callgraph.py \
  --root BAIDU_REPO/aiak_ds_tool \
  --seed-file aiak_infer_tools/extensions/apps/simulator_v2/app.py \
  --seed-line 144 \
  --seed-character 8 \
  --language-id python \
  --language-name Python \
  --lsp-command 'npx --yes --package pyright pyright-langserver --stdio' \
  --direction outgoing \
  --depth 3 \
  --max-nodes 80
```
