#!/usr/bin/env python3
"""Antigravity command and auxiliary projection.

Transforms canonical command definitions in package descriptor into Antigravity
command TOML manifests under .antigravity-plugin/commands/ and validates synchronization.
Decomposed from package_projection.py per Single Responsibility Principle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import PackageDescriptor, ValidationError


def _safe_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def generate_antigravity_commands(desc: PackageDescriptor) -> Dict[str, str]:
    """Generate TOML command manifest contents for Antigravity plugin."""
    cmds: Dict[str, str] = {}
    for cmd in desc.commands:
        name = cmd["name"]
        d = cmd["description"]
        p = cmd["prompt"]
        cmds[f"{name}.toml"] = f'description = "{d}"\nprompt = "{p}"\n'
    return cmds


def project_antigravity_commands(desc: PackageDescriptor, cmds_dir: Path) -> int:
    """Project generated TOML command manifests into target directory."""
    cmds_dir.mkdir(parents=True, exist_ok=True)
    commands = generate_antigravity_commands(desc)
    for fname, toml_str in commands.items():
        (cmds_dir / fname).write_text(toml_str, encoding="utf-8")
    return len(commands)


def check_antigravity_commands(desc: PackageDescriptor, cmds_dir: Path) -> bool:
    """Validate that all projected Antigravity command files match expectations."""
    expected_cmds = generate_antigravity_commands(desc)
    if not cmds_dir.is_dir() and expected_cmds:
        print(f"MISSING: antigravity commands directory not found at {_safe_rel(cmds_dir)}")
        return False
    if not expected_cmds:
        return True

    cmds_ok = True
    for fname, expected_content in expected_cmds.items():
        target_file = cmds_dir / fname
        if not target_file.is_file():
            print(f"MISSING: antigravity command not found at {_safe_rel(target_file)}")
            cmds_ok = False
        elif target_file.read_text(encoding="utf-8") != expected_content:
            print(f"DRIFT: antigravity command at {_safe_rel(target_file)} does not match expected")
            cmds_ok = False

    if cmds_ok:
        print(f"PASS: {len(expected_cmds)} antigravity commands at {_safe_rel(cmds_dir)} in sync")
    return cmds_ok


def project_antigravity_auxiliary(
    desc: PackageDescriptor,
    models_file: Path,
    models_data: Dict[str, Any],
) -> None:
    """Project models catalog and command manifests for Antigravity harness."""
    models_file.parent.mkdir(parents=True, exist_ok=True)
    models_file.write_text(json.dumps(models_data, indent=2) + "\n", encoding="utf-8")
    print(f"Projected antigravity models -> {_safe_rel(models_file)}")

    cmds_dir = models_file.parent / "commands"
    count = project_antigravity_commands(desc, cmds_dir)
    print(f"Projected {count} antigravity commands -> {_safe_rel(cmds_dir)}")


def check_antigravity_auxiliary(
    desc: PackageDescriptor,
    models_file: Path,
    expected_models: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check that Antigravity model catalog and command files are in sync."""
    all_ok = True
    if expected_models is None:
        all_ok = False
    elif not models_file.is_file():
        print(f"MISSING: antigravity models not found at {_safe_rel(models_file)}")
        all_ok = False
    else:
        try:
            actual_models = json.loads(models_file.read_text(encoding="utf-8"))
            if actual_models != expected_models:
                print(f"DRIFT: antigravity models at {_safe_rel(models_file)} does not match expected")
                all_ok = False
            else:
                print(f"PASS: antigravity models at {_safe_rel(models_file)} in sync")
        except Exception as e:
            print(f"ERROR: {_safe_rel(models_file)} failed to parse: {e}")
            all_ok = False

    cmds_dir = models_file.parent / "commands"
    if not check_antigravity_commands(desc, cmds_dir):
        all_ok = False

    return all_ok
