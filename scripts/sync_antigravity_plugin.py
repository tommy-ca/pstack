#!/usr/bin/env python3
"""Sync and reconcile canonical pstack package to the live Antigravity plugin installation.

Reconciles canonical pstack repo into the live Antigravity plugin installation.
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

# Source paths whose content sync_live_plugin publishes into the live plugin.
SYNCED_PATHS = ("skills", "agents", "pstack.package.json")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
)

import scripts.package_projection as _pp_mod
from scripts.package_projection import (
    generate_antigravity_commands,
    generate_antigravity_manifest,
    generate_antigravity_models,
    load_package_descriptor,
    project_all,
)


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

    # Check commands (native agy packages ship commands as skills; check only when commands dir exists)
    commands_dir = LIVE_PLUGIN_DIR / "commands"
    if commands_dir.is_dir():
        expected_cmds = generate_antigravity_commands(desc)
        dest_cmds = {f.name: f.read_bytes() for f in commands_dir.glob("*.toml") if f.is_file()}
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

    # Check profiles
    from scripts.setup_pstack import resolve_profiles_dir
    src_profiles_dir = resolve_profiles_dir(ROOT)
    dest_profiles_dir = LIVE_PLUGIN_DIR / "profiles"
    if dest_profiles_dir.is_dir():
        src_profiles = {p.name: p.read_bytes() for p in src_profiles_dir.glob("*.json")}
        dest_profiles = {p.name: p.read_bytes() for p in dest_profiles_dir.glob("*.json")}
        if not check_files(src_profiles, dest_profiles, "profiles"):
            all_ok = False

    if all_ok:
        print("PASS: Live Antigravity plugin is fully synchronized with canonical repo.")
    return all_ok


def _git(source: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # --no-optional-locks: the guard must never write the source repo's index or locks.
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(source), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def source_tree_guard(source: Path | None = None) -> str:
    """Return "" when the source tree is safe to publish, else the refusal message."""
    source = ROOT if source is None else source

    if _git(source, "rev-parse", "--git-dir").returncode != 0:
        return (
            f"Refusing to sync: {source} is not a git repository, so pstack cannot tell "
            "whether the published content is committed. Pass --force to sync anyway."
        )

    status = _git(source, "status", "--porcelain", "-uall", "--", *SYNCED_PATHS)
    if status.returncode != 0:
        return (
            f"Refusing to sync: git status failed in {source}: {status.stderr.strip()}\n"
            "Pass --force to sync anyway."
        )
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    if dirty:
        listed = "\n".join(f"  {line}" for line in dirty)
        return (
            f"Refusing to sync: {source} has uncommitted changes in published paths:\n"
            f"{listed}\n"
            "Commit or stash them, or pass --force to publish them anyway."
        )

    git_dir = _git(source, "rev-parse", "--git-dir").stdout.strip()
    common_dir = _git(source, "rev-parse", "--git-common-dir").stdout.strip()
    if (source / git_dir).resolve() != (source / common_dir).resolve():
        primary = next(
            (
                line.removeprefix("worktree ").strip()
                for line in _git(source, "worktree", "list", "--porcelain").stdout.splitlines()
                if line.startswith("worktree ")
            ),
            "unknown",
        )
        return (
            f"Refusing to sync: {source} is a linked git worktree, not the primary checkout "
            f"({primary}). Publish from the primary checkout, or pass --force to publish "
            "this worktree anyway."
        )

    return ""


def _log_sync_plan(desc: Any, dest_dir: Path) -> None:
    manifest_dest = dest_dir / "plugin.json"
    print(f"Writing {manifest_dest}")
    models_dest = dest_dir / "models.json"
    print(f"Writing {models_dest}")
    rules_dest = dest_dir / "rules" / "AGENTS.md"
    print(f"Writing {rules_dest}")

    hooks_file = dest_dir / "hooks" / "hooks.json"
    if hooks_file.is_file():
        print(f"Removing stale {hooks_file}")

    for stray in [".codex-plugin", ".claude-plugin"]:
        stray_path = dest_dir / stray
        if stray_path.exists():
            print(f"Removing foreign legacy directory {stray_path}")

    src_skills = ROOT / "skills"
    dest_skills = dest_dir / "skills"
    src_skill_names = skill_names(src_skills)
    for item_name in sorted(src_skill_names):
        print(f"Syncing skill {item_name} -> {dest_skills / item_name}")
    for name in sorted(skill_names(dest_skills) - src_skill_names):
        print(f"Removing deleted skill {name}")

    src_agents = ROOT / "agents"
    dest_agents = dest_dir / "agents"
    src_agent_files = {f.name for f in src_agents.glob("*.md") if f.is_file()}
    for fname in sorted(src_agent_files):
        print(f"Syncing agent {fname} -> {dest_agents / fname}")
    if dest_agents.is_dir():
        for existing_f in dest_agents.glob("*.md"):
            if existing_f.is_file() and existing_f.name not in src_agent_files:
                print(f"Removing deleted agent {existing_f.name}")

    expected_cmds = generate_antigravity_commands(desc)
    dest_cmds = dest_dir / "commands"
    for fname, _ in sorted(expected_cmds.items()):
        print(f"Syncing command {fname} -> {dest_cmds / fname}")
    if dest_cmds.is_dir():
        for existing_cmd in dest_cmds.glob("*.toml"):
            if existing_cmd.is_file() and existing_cmd.name not in expected_cmds:
                print(f"Removing deleted command {existing_cmd.name}")


def sync_live_plugin(dry_run: bool = False, force: bool = False) -> bool:
    refusal = "" if force else source_tree_guard()
    if refusal:
        print(refusal, file=sys.stderr)
        return False

    desc, _ = load_package_descriptor()
    print(f"Syncing canonical pstack ({desc.version}) -> {LIVE_PLUGIN_DIR}")

    _log_sync_plan(desc, LIVE_PLUGIN_DIR)

    if dry_run:
        return True

    from scripts.package_lifecycle import install_plugin
    project_all(desc, ["antigravity"])
    install_plugin("antigravity", target_dir=LIVE_PLUGIN_DIR, source_root=ROOT, force=force)

    # Reconcile removed skills and removed files inside managed skills
    src_skills = ROOT / "skills"
    dest_skills = LIVE_PLUGIN_DIR / "skills"
    if dest_skills.is_dir():
        src_skill_names = skill_names(src_skills)
        for name in sorted(skill_names(dest_skills) - src_skill_names):
            shutil.rmtree(dest_skills / name)
        for sname in sorted(src_skill_names):
            target = dest_skills / sname
            if target.is_dir():
                expected_files = set(skill_files(src_skills / sname).keys())
                actual_files = set(skill_files(target).keys())
                for extra_rel in sorted(actual_files - expected_files):
                    extra_p = target / extra_rel
                    if extra_p.is_file() or extra_p.is_symlink():
                        extra_p.unlink()

    if shutil.which("agy"):
        print("\nValidating with Antigravity CLI:")
        subprocess.run(["agy", "plugin", "validate", str(LIVE_PLUGIN_DIR)], check=False)

    print("Live Antigravity plugin synchronization complete.")
    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="Audit live plugin without modifying")
    parser.add_argument("--sync", action="store_true", help="Synchronize live plugin from repository")
    parser.add_argument("--check", action="store_true", help="Check synchronization and exit with code")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for sync")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sync even when the source tree has uncommitted changes or is a linked worktree",
    )
    args = parser.parse_args(argv)

    if args.check:
        ok = check_live_sync()
        sys.exit(0 if ok else 1)

    if args.audit or not args.sync:
        report = audit_live_plugin()
        print("Live Antigravity Plugin Audit:")
        for k, v in report.items():
            print(f"  {k}: {v}")

    if args.sync:
        if not sync_live_plugin(dry_run=args.dry_run, force=args.force):
            sys.exit(2)


if __name__ == "__main__":
    main()
