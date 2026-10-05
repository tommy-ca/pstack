#!/usr/bin/env python3
"""Sync and reconcile canonical pstack package to the live Antigravity plugin installation.

Implements Build the Lever + Prove It Works:
    Canonical pstack repo -> ~/.gemini/config/plugins/pstack/
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "pstack"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util

PROJECT_PACKAGE_SCRIPT = ROOT / "scripts" / "project-package.py"
_loader = importlib.util.spec_from_file_location("project_package", PROJECT_PACKAGE_SCRIPT)
assert _loader is not None and _loader.loader is not None
_pp_mod = importlib.util.module_from_spec(_loader)
sys.modules["project_package"] = _pp_mod
_loader.loader.exec_module(_pp_mod)

generate_antigravity_manifest = _pp_mod.generate_antigravity_manifest
generate_antigravity_models = _pp_mod.generate_antigravity_models
load_package_descriptor = _pp_mod.load_package_descriptor


def audit_live_plugin() -> dict[str, str]:
    report = {}
    if not LIVE_PLUGIN_DIR.is_dir():
        report["status"] = "missing"
        return report

    manifest_file = LIVE_PLUGIN_DIR / "plugin.json"
    if manifest_file.is_file():
        try:
            m = json.loads(manifest_file.read_text(encoding="utf-8"))
            report["version"] = m.get("version", "unknown")
            report["name"] = m.get("name", "unknown")
        except Exception:
            report["version"] = "corrupt"
    else:
        report["version"] = "missing"

    models_file = LIVE_PLUGIN_DIR / "models.json"
    if models_file.is_file():
        try:
            mod = json.loads(models_file.read_text(encoding="utf-8"))
            report["default_model"] = mod.get("singleRoleDefault", "unknown")
        except Exception:
            report["default_model"] = "corrupt"
    else:
        report["default_model"] = "missing"

    hooks_file = LIVE_PLUGIN_DIR / "hooks" / "hooks.json"
    if hooks_file.is_file():
        text = hooks_file.read_text(encoding="utf-8")
        report["has_claude_roots"] = "true" if "CLAUDE_PLUGIN_ROOT" in text else "false"
    else:
        report["has_claude_roots"] = "none"

    skills_dir = LIVE_PLUGIN_DIR / "skills"
    if skills_dir.is_dir():
        report["skills_count"] = str(len(list(skills_dir.iterdir())))
    else:
        report["skills_count"] = "0"

    return report


def sync_live_plugin(dry_run: bool = False) -> None:
    desc, _ = load_package_descriptor()
    print(f"Syncing canonical pstack ({desc.version}) -> {LIVE_PLUGIN_DIR}")

    if not LIVE_PLUGIN_DIR.exists():
        if not dry_run:
            LIVE_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    # 1. plugin.json
    manifest = generate_antigravity_manifest(desc)
    manifest_dest = LIVE_PLUGIN_DIR / "plugin.json"
    print(f"Writing {manifest_dest}")
    if not dry_run:
        manifest_dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # 2. models.json
    models = generate_antigravity_models(desc)
    models_dest = LIVE_PLUGIN_DIR / "models.json"
    print(f"Writing {models_dest}")
    if not dry_run:
        models_dest.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

    # 3. rules/AGENTS.md
    rules_dir = LIVE_PLUGIN_DIR / "rules"
    rules_dest = rules_dir / "AGENTS.md"
    session_start_context = LIVE_PLUGIN_DIR / "hooks" / "session-start-context.md"
    rules_content = """# pstack instructions for Antigravity

When working with pstack:
- Prefer fewer, higher-quality changes.
- Follow poteto-mode: go deep first, plan before coding, verify with levereable proofs.
- Use native subagents (`invoke_subagent`) for parallel operations (Arena, Swarm, Interrogate).
- Respect isolated workspaces (`Workspace: branch`) when modifying code in parallel.
"""
    if session_start_context.is_file():
        rules_content = session_start_context.read_text(encoding="utf-8")

    print(f"Writing {rules_dest}")
    if not dry_run:
        rules_dir.mkdir(parents=True, exist_ok=True)
        rules_dest.write_text(rules_content, encoding="utf-8")

    # Clean up stale hooks that relied on CLAUDE_PLUGIN_ROOT
    hooks_file = LIVE_PLUGIN_DIR / "hooks" / "hooks.json"
    if hooks_file.is_file():
        print(f"Removing stale {hooks_file}")
        if not dry_run:
            hooks_file.unlink()

    # 4. Sync skills from ROOT/skills
    src_skills = ROOT / "skills"
    dest_skills = LIVE_PLUGIN_DIR / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)

    for item in src_skills.iterdir():
        if item.is_dir():
            target = dest_skills / item.name
            print(f"Syncing skill {item.name} -> {target}")
            if not dry_run:
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)

    print("Live Antigravity plugin synchronization complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="Audit live plugin without modifying")
    parser.add_argument("--sync", action="store_true", help="Synchronize live plugin from repository")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for sync")
    args = parser.parse_args()

    if args.audit or not args.sync:
        report = audit_live_plugin()
        print("Live Antigravity Plugin Audit:")
        for k, v in report.items():
            print(f"  {k}: {v}")

    if args.sync:
        sync_live_plugin(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
