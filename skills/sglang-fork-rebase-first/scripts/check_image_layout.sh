#!/usr/bin/env bash
# 交付镜像四件套的格式自查，在仓库里跑：
#   check_image_layout.sh <交付 rev> <新基线 rev> <模板分支 rev>
# 查五件事：四件套在位与 mode、ci.yml 与 build.sh 与模板同 blob、相对新基线只动镜像
# 文件、没有自创文件名、Dockerfile 的 COPY 源都在 aiak_sglang/ 下（context 是父目录）。
set -uo pipefail

REV=${1:?usage: check_image_layout.sh <rev> <new-base-rev> <template-rev>}
BASE=${2:?usage: check_image_layout.sh <rev> <new-base-rev> <template-rev>}
TPL=${3:?usage: check_image_layout.sh <rev> <new-base-rev> <template-rev>}

rc=0
fail() { rc=1; printf 'FAIL %s\n' "$1"; }

while read -r want_mode path; do
    entry=$(git ls-tree "$REV" -- "$path")
    if [ -z "$entry" ]; then
        fail "缺文件 $path"
        continue
    fi
    mode=${entry%% *}
    [ "$mode" = "$want_mode" ] || fail "$path mode=$mode，应为 $want_mode"
done <<'TRIO'
100644 ci.yml
100755 build/build.sh
100644 dockerfile/Dockerfile
100644 dockerfile/gpu_requirements.env
TRIO

for path in ci.yml build/build.sh; do
    ours=$(git rev-parse --verify --quiet "$REV:$path" || echo none)
    theirs=$(git rev-parse --verify --quiet "$TPL:$path" || echo none-in-template)
    [ "$ours" = "$theirs" ] || fail "$path 与模板不同：$ours vs $theirs"
done

drift=$(git diff --name-only "$BASE" "$REV" -- ci.yml build docker dockerfile)
if [ -n "$drift" ]; then
    while read -r path; do
        case "$path" in
            ci.yml | build/build.sh | dockerfile/Dockerfile | dockerfile/gpu_requirements.env) ;;
            docker/*/*) ;; # 模型专属资产子目录
            *) fail "镜像文件漂移：$path" ;;
        esac
    done <<<"$drift"
fi

stray=$(git ls-tree -r --name-only "$REV" -- dockerfile |
    grep -vE '^dockerfile/(Dockerfile|gpu_requirements\.env)$')
[ -z "$stray" ] || fail "dockerfile/ 下有自创文件名：$(echo "$stray" | tr '\n' ' ')"

if dockerfile=$(git show "$REV:dockerfile/Dockerfile" 2>/dev/null); then
    bad_copy=$(printf '%s\n' "$dockerfile" | awk '/^COPY /{if ($2 !~ /^aiak_sglang/) print}')
    [ -z "$bad_copy" ] || fail "COPY 源不在 aiak_sglang/ 下：$bad_copy"
    printf 'base %s\n' "$(printf '%s\n' "$dockerfile" | sed -n '1p')"
fi
[ $rc -eq 0 ] && printf 'OK   四件套格式通过\n'
exit $rc
