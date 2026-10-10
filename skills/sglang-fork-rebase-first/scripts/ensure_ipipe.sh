#!/usr/bin/env bash
# Print the path of a working ipipe-cli; install it from the official skill package if absent.
# The package is the ipipe-official skill zip; its SKILL.md carries the pinned CLI version
# and installer URL, so the pin lives in one place (the official package).
set -euo pipefail

skill_zip_url=${IPIPE_SKILL_URL:-https://mcp-proxy.baidu-int.com/api/v1/skills/download/permanent/2e14fa93-8db5-4548-831a-50f9e9fdb98c/ipipe-official.zip}

find_cli() { command -v ipipe-cli || { [ -x "$HOME/.ipipe-cli/bin/ipipe-cli" ] && echo "$HOME/.ipipe-cli/bin/ipipe-cli"; }; }

if cli=$(find_cli); then echo "$cli"; exit 0; fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl -fsSL -m 60 -o "$work/skill.zip" "$skill_zip_url" >&2 \
  || { echo "cannot download ipipe-official from $skill_zip_url" >&2; exit 1; }
unzip -q "$work/skill.zip" -d "$work" >&2
skill_md="$work/ipipe-official/SKILL.md"
version=$(sed -n 's/^export IPIPE_CLI_VERSION=\(.*\)$/\1/p' "$skill_md" | head -1)
installer=$(sed -n "s/.*curl -fsSL '\([^']*install_ipipe-cli.sh\)'.*/\1/p" "$skill_md" | head -1)
[ -n "$version" ] && [ -n "$installer" ] \
  || { echo "install command not found in official SKILL.md" >&2; exit 1; }

IPIPE_CLI_VERSION=$version bash -c "$(curl -fsSL "$installer")" >&2
find_cli || { echo "ipipe-cli install finished but binary not found" >&2; exit 1; }
