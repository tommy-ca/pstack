#!/usr/bin/env python3
"""Sync and reconcile canonical pstack package to the live Antigravity plugin installation.

Implements Build the Lever + Prove It Works + Zero Drift:
    Canonical pstack repo -> ~/.gemini/config/plugins/pstack/
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "pstack"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util

from scripts.portability_schema import (
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
)

PROJECT_PACKAGE_SCRIPT = ROOT / "scripts" / "project-package.py"
_loader = importlib.util.spec_from_file_location("project_package", PROJECT_PACKAGE_SCRIPT)
assert _loader is not None and _loader.loader is not None
_pp_mod = importlib.util.module_from_spec(_loader)
sys.modules["project_package"] = _pp_mod
_loader.loader.exec_module(_pp_mod)

generate_antigravity_manifest = _pp_mod.generate_antigravity_manifest
generate_antigravity_models = _pp_mod.generate_antigravity_models
generate_antigravity_commands = _pp_mod.generate_antigravity_commands
load_package_descriptor = _pp_mod.load_package_descriptor
project_all = _pp_mod.project_all


def skill_names(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {
        item.name for item in directory.iterdir()
        if item.is_dir() and item.name not in SKILLS_HASH_IGNORED_DIRS
    }


def skill_files(directory: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    if not directory.is_dir():
        return files

    base_resolved = directory.resolve()
    # (current_dir, tuple_of_resolved_ancestors)
    stack = [(directory, (base_resolved,))]
    while stack:
        current_dir, ancestors = stack.pop()
        try:
            entries = sorted(current_dir.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        subdirs = []
        for entry in entries:
            if entry.name in SKILLS_HASH_IGNORED_DIRS:
                continue
            if entry.is_symlink():
                try:
                    resolved = entry.resolve()
                except OSError:
                    continue
                if not resolved.is_relative_to(base_resolved):
                    continue
                if resolved.is_dir():
                    if resolved in ancestors:
                        continue
                    subdirs.append((entry, ancestors + (resolved,)))
                elif resolved.is_file():
                    if entry.suffix not in SKILLS_HASH_IGNORED_SUFFIXES:
                        try:
                            files[str(entry.relative_to(directory))] = resolved.read_bytes()
                        except OSError:
                            continue
            elif entry.is_dir():
                try:
                    resolved = entry.resolve()
                except OSError:
                    continue
                if not resolved.is_relative_to(base_resolved) or resolved in ancestors:
                    continue
                subdirs.append((entry, ancestors + (resolved,)))
            elif entry.is_file():
                if entry.suffix not in SKILLS_HASH_IGNORED_SUFFIXES:
                    try:
                        files[str(entry.relative_to(directory))] = entry.read_bytes()
                    except OSError:
                        continue
        for subdir, next_ancestors in reversed(subdirs):
            stack.append((subdir, next_ancestors))
    return files


def check_files(expected: dict[str, bytes], actual: dict[str, bytes], label: str) -> bool:
    missing = expected.keys() - actual.keys()
    extra = actual.keys() - expected.keys()
    drifted = {name for name in expected.keys() & actual.keys() if expected[name] != actual[name]}
    for status, names in [("Missing", missing), ("Extra", extra), ("Drifted", drifted)]:
        if names:
            print(f"FAIL: {status} {label} in live plugin: {sorted(names)}")
    return not (missing or extra or drifted)


def audit_live_plugin() -> dict[str, str]:
    report: dict[str, str] = {}
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

    skills_dir = LIVE_PLUGIN_DIR / "skills"
    if skills_dir.is_dir():
        report["skills_count"] = str(len([d for d in skills_dir.iterdir() if d.is_dir()]))
    else:
        report["skills_count"] = "0"

    agents_dir = LIVE_PLUGIN_DIR / "agents"
    if agents_dir.is_dir():
        report["agents_count"] = str(len(list(agents_dir.glob("*.md"))))
    else:
        report["agents_count"] = "0"

    commands_dir = LIVE_PLUGIN_DIR / "commands"
    if commands_dir.is_dir():
        report["commands_count"] = str(len(list(commands_dir.glob("*.toml"))))
    else:
        report["commands_count"] = "0"

    foreign = [d for d in [".codex-plugin", ".claude-plugin"] if (LIVE_PLUGIN_DIR / d).exists()]
    report["foreign_directories"] = ", ".join(foreign) if foreign else "none"

    if shutil.which("agy"):
        proc = subprocess.run(
            ["agy", "plugin", "validate", str(LIVE_PLUGIN_DIR)],
            capture_output=True,
            text=True,
            check=False,
        )
        report["agy_validate"] = "PASS" if proc.returncode == 0 else "FAIL"

    return report


def check_live_sync() -> bool:
    desc, _ = load_package_descriptor()
    if not LIVE_PLUGIN_DIR.is_dir():
        print(f"FAIL: Live plugin directory does not exist: {LIVE_PLUGIN_DIR}")
        return False

    all_ok = True

    # Check plugin.json
    manifest_dest = LIVE_PLUGIN_DIR / "plugin.json"
    if not manifest_dest.is_file():
        print("FAIL: plugin.json missing from live plugin")
        all_ok = False
    else:
        expected = generate_antigravity_manifest(desc)
        try:
            actual = json.loads(manifest_dest.read_text(encoding="utf-8"))
            if actual != expected:
                print("FAIL: plugin.json has drifted from canonical descriptor")
                all_ok = False
        except Exception as e:
            print(f"FAIL: plugin.json corrupt: {e}")
            all_ok = False

    # Check models.json
    models_dest = LIVE_PLUGIN_DIR / "models.json"
    if not models_dest.is_file():
        print("FAIL: models.json missing from live plugin")
        all_ok = False
    else:
        expected_models = generate_antigravity_models(desc)
        try:
            actual_models = json.loads(models_dest.read_text(encoding="utf-8"))
            if actual_models != expected_models:
                print("FAIL: models.json has drifted from expected")
                all_ok = False
        except Exception as e:
            print(f"FAIL: models.json corrupt: {e}")
            all_ok = False

    # Check skills
    src_skills = skill_names(ROOT / "skills")
    dest_skills = skill_names(LIVE_PLUGIN_DIR / "skills")
    missing_skills = src_skills - dest_skills
    extra_skills = dest_skills - src_skills
    if missing_skills:
        print(f"FAIL: Missing skills in live plugin: {sorted(missing_skills)}")
        all_ok = False
    if extra_skills:
        print(f"FAIL: Extra untracked skills in live plugin: {sorted(extra_skills)}")
        all_ok = False
    for name in sorted(src_skills & dest_skills):
        if not check_files(
            skill_files(ROOT / "skills" / name),
            skill_files(LIVE_PLUGIN_DIR / "skills" / name),
            f"files for skill {name}",
        ):
            all_ok = False

    # Check agents
    src_agents = {f.name: f.read_bytes() for f in (ROOT / "agents").glob("*.md") if f.is_file()}
    dest_agents = {f.name: f.read_bytes() for f in (LIVE_PLUGIN_DIR / "agents").glob("*.md") if f.is_file()}
    if not check_files(src_agents, dest_agents, "agents"):
        all_ok = False

    # Check commands
    expected_cmds = generate_antigravity_commands(desc)
    dest_cmds = {f.name: f.read_bytes() for f in (LIVE_PLUGIN_DIR / "commands").glob("*.toml") if f.is_file()}
    if not check_files(
        {name: content.encode("utf-8") for name, content in expected_cmds.items()},
        dest_cmds,
        "commands",
    ):
        all_ok = False

    # Check foreign directories
    for stray in [".codex-plugin", ".claude-plugin"]:
        if (LIVE_PLUGIN_DIR / stray).exists():
            print(f"FAIL: Foreign legacy directory present in live plugin: {stray}")
            all_ok = False

    if all_ok:
        print("PASS: Live Antigravity plugin is fully synchronized with canonical repo.")
    return all_ok


def sync_live_plugin(dry_run: bool = False) -> None:
    desc, _ = load_package_descriptor()
    print(f"Syncing canonical pstack ({desc.version}) -> {LIVE_PLUGIN_DIR}")

    if not LIVE_PLUGIN_DIR.exists():
        if not dry_run:
            LIVE_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Project local repo manifests first
    if not dry_run:
        project_all(desc, ["antigravity"])

    # 2. plugin.json
    manifest = generate_antigravity_manifest(desc)
    manifest_dest = LIVE_PLUGIN_DIR / "plugin.json"
    print(f"Writing {manifest_dest}")
    if not dry_run:
        manifest_dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # 3. models.json
    models = generate_antigravity_models(desc)
    models_dest = LIVE_PLUGIN_DIR / "models.json"
    print(f"Writing {models_dest}")
    if not dry_run:
        models_dest.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

    # 4. rules/AGENTS.md
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

    # Clean up foreign / legacy directories
    for stray in [".codex-plugin", ".claude-plugin"]:
        stray_path = LIVE_PLUGIN_DIR / stray
        if stray_path.exists():
            print(f"Removing foreign legacy directory {stray_path}")
            if not dry_run:
                shutil.rmtree(stray_path)

    # 5. Sync skills from ROOT/skills
    src_skills = ROOT / "skills"
    dest_skills = LIVE_PLUGIN_DIR / "skills"
    if not dry_run:
        dest_skills.mkdir(parents=True, exist_ok=True)

    src_skill_names = skill_names(src_skills)
    for item_name in sorted(src_skill_names):
        item = src_skills / item_name
        target = dest_skills / item_name
        print(f"Syncing skill {item_name} -> {target}")
        if not dry_run:
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            for rel_path, content in skill_files(item).items():
                dest_file = target / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_bytes(content)

    # Clean up any removed skills
    for name in sorted(skill_names(dest_skills) - src_skill_names):
        print(f"Removing deleted skill {name}")
        if not dry_run:
            shutil.rmtree(dest_skills / name)

    # 6. Sync agents from ROOT/agents
    src_agents = ROOT / "agents"
    dest_agents = LIVE_PLUGIN_DIR / "agents"
    if not dry_run:
        dest_agents.mkdir(parents=True, exist_ok=True)

    src_agent_files = {f.name for f in src_agents.glob("*.md") if f.is_file()}
    for fname in sorted(src_agent_files):
        src_file = src_agents / fname
        target_file = dest_agents / fname
        print(f"Syncing agent {fname} -> {target_file}")
        if not dry_run:
            shutil.copy2(src_file, target_file)

    for existing_f in dest_agents.glob("*.md"):
        if existing_f.is_file() and existing_f.name not in src_agent_files:
            print(f"Removing deleted agent {existing_f.name}")
            if not dry_run:
                existing_f.unlink()

    expected_cmds = generate_antigravity_commands(desc)
    dest_cmds = LIVE_PLUGIN_DIR / "commands"
    if not dry_run:
        dest_cmds.mkdir(parents=True, exist_ok=True)

    for fname, content in sorted(expected_cmds.items()):
        target_cmd = dest_cmds / fname
        print(f"Syncing command {fname} -> {target_cmd}")
        if not dry_run:
            target_cmd.write_text(content, encoding="utf-8")

    for existing_cmd in dest_cmds.glob("*.toml"):
        if existing_cmd.is_file() and existing_cmd.name not in expected_cmds:
            print(f"Removing deleted command {existing_cmd.name}")
            if not dry_run:
                existing_cmd.unlink()

    # 8. Run agy plugin validate verification
    if not dry_run and shutil.which("agy"):
        print("\nValidating with Antigravity CLI:")
        subprocess.run(["agy", "plugin", "validate", str(LIVE_PLUGIN_DIR)], check=False)

    print("Live Antigravity plugin synchronization complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="Audit live plugin without modifying")
    parser.add_argument("--sync", action="store_true", help="Synchronize live plugin from repository")
    parser.add_argument("--check", action="store_true", help="Check synchronization and exit with code")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for sync")
    args = parser.parse_args()

    if args.check:
        ok = check_live_sync()
        sys.exit(0 if ok else 1)

    if args.audit or not args.sync:
        report = audit_live_plugin()
        print("Live Antigravity Plugin Audit:")
        for k, v in report.items():
            print(f"  {k}: {v}")

    if args.sync:
        sync_live_plugin(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
