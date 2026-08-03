#!/bin/sh
# Print the platform, the Nsys CLI, and the bundled Python interpreter
set -eu

here=$(cd "$(dirname "$0")" && pwd -P)
root=$(cd "$here/../../.." && pwd -P)

platform=unknown
# 1. The host-<platform> directory names the platform authoritatively
for d in "$root"/host-*; do
    if [ -d "$d" ]; then platform=${d##*/host-}; break; fi
done
# 2. Else derive it from this host's OS and architecture
if [ "$platform" = unknown ]; then
    os=$(uname -s 2>/dev/null || echo Linux)
    arch=$(uname -m 2>/dev/null || echo x86_64)
    case $os in Darwin) os=macos ;; *) os=linux ;; esac
    case $arch in aarch64|arm64) arch=sbsa-armv8 ;; *) arch=x64 ;; esac
    platform="$os-$arch"
fi
echo "Platform: $platform"

# CLI: NSYS_PATH when set, else the target tree for that platform, then PATH
nsys=${NSYS_PATH:-}
if [ -z "$nsys" ]; then
    nsys="$root/target-$platform/nsys"
    if [ ! -f "$nsys" ]; then nsys=$(command -v nsys 2>/dev/null || true); fi
fi
if [ -z "$nsys" ] || [ ! -f "$nsys" ]; then
    echo "ERROR: Could not resolve the Nsys CLI path on this platform."
    exit 1
fi
# Resolve a symlinked Nsys so the Python beside the real binary is found
nsys=$(readlink -f "$nsys" 2>/dev/null || echo "$nsys")
dir=$(cd "$(dirname "$nsys")" && pwd -P)
echo "Nsys CLI: \"$dir/$(basename "$nsys")\""

py="$dir/python/bin/python3"
if [ ! -f "$py" ]; then py="$dir/python/bin/python"; fi
if [ ! -f "$py" ]; then
    echo "ERROR: Could not find the bundled Nsys Python interpreter."
    exit 1
fi
echo "Nsys Python interpreter: \"$py\""

# No bundled Python in test environment.  Skip.
if [ -n "${NSYS_SKILL_UNIT_TEST:-}" ]; then exit 0; fi

# Report any packaged report dependencies missing from the bundled Python
if ! missing=$("$py" "$here/_core/check_report_dependencies.py" 2>/dev/null); then
    echo "ERROR: Failed to validate bundled Nsys Python dependencies."
    exit 1
fi
if [ -n "$missing" ]; then
    echo "ERROR: Bundled Nsys Python is missing dependencies: $missing."
    exit 1
fi

# Leave the resolved path where the packaged Python tools pick it up
cache=${NSYS_TMPDIR:-${TMPDIR:-/tmp}}/nvidia/nsight_systems/nsys-skill-cache
if mkdir -p "$cache" 2>/dev/null; then
    printf '%s\n' "$dir/$(basename "$nsys")" > "$cache/NSYS_PATH"
fi