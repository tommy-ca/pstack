#!/usr/bin/env python3
"""Project canonical pstack.package.json into harness-native plugin descriptors.

CLI entrypoint and facade re-exporting from scripts.package_projection.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.package_projection as _pkg_proj
from scripts.package_projection import *
from scripts.package_projection import _split_frontmatter, main

# Local bindings so monkeypatching in tests functions correctly
CLAUDE_PLUGIN_DIR = _pkg_proj.CLAUDE_PLUGIN_DIR
MODEL_ROLE_POLICY = _pkg_proj.MODEL_ROLE_POLICY


def check_claude_plugin(desc: PackageDescriptor, plugin_dir: Optional[Path] = None) -> bool:
    return _pkg_proj.check_claude_plugin(desc, plugin_dir=plugin_dir or CLAUDE_PLUGIN_DIR)


def check_model_role_plan(desc: PackageDescriptor, policy_path: Optional[Path] = None) -> bool:
    return _pkg_proj.check_model_role_plan(desc, policy_path=policy_path or MODEL_ROLE_POLICY)


def check_all(desc: PackageDescriptor, hosts: List[str] | None = None) -> bool:
    return _pkg_proj.check_all(
        desc, hosts=hosts, plugin_dir=CLAUDE_PLUGIN_DIR, policy_path=MODEL_ROLE_POLICY
    )


if __name__ == "__main__":
    main()
