#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_core"))

from bootstrap_core import (  # noqa: E402
    default_cache_dir,
    default_recipe_output_dir,
    ensure_core,
    skill_pack_root,
)

ensure_core()

from nsys_agent_tools.agent_gateway import main as gateway_main  # noqa: E402


def main() -> int:
    return gateway_main(
        prog="scripts/nsys_skill_cli.py",
        default_skill_pack=skill_pack_root(),
        cache_dir=default_cache_dir(),
        recipe_output_dir=default_recipe_output_dir(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
