#!/usr/bin/env python3
"""Staging, asset generation, and file management for package installation.

Extracts installation staging, managed manifest records, host asset generation,
and safe filesystem operations from package_lifecycle.py.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from scripts.package_projection import (
    generate_antigravity_commands,
    generate_antigravity_manifest,
    generate_antigravity_models,
    generate_antigravity_rules,
    generate_codex_manifest,
    generate_droid_manifest,
    generate_droid_marketplace,
    generate_droid_roles,
    generate_grok_manifest,
    generate_omp_manifest,
    generate_opencode_manifest,
)
from scripts.portability_types import (
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
    STRAY_PLUGIN_DIRS,
)
from scripts.setup_pstack import resolve_profiles_dir


def find_agy_binary() -> str | None:
    bin_path = shutil.which("agy")
    if bin_path:
        return bin_path
    local_bin = Path.home() / ".local" / "bin" / "agy"
    if local_bin.is_file() and os.access(local_bin, os.X_OK):
        return str(local_bin)
    return None


def skill_names(directory: Path) -> set[str]:
    """Return all skill directory names in directory ignoring dot and excluded directories."""
    if not directory.is_dir():
        return set()
    return {
        item.name for item in directory.iterdir()
        if item.is_dir() and not item.name.startswith(".") and item.name not in SKILLS_HASH_IGNORED_DIRS
    }


def skill_files(directory: Path) -> dict[str, bytes]:
    """Return relative path to content mapping for all valid skill files in directory."""
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
            if entry.name.startswith(".") or entry.name in SKILLS_HASH_IGNORED_DIRS:
                continue
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
        for subdir, next_ancestors in reversed(subdirs):
            stack.append((subdir, next_ancestors))
    return files


def purge_stray_plugin_dirs(plugin_dir: Path) -> None:
    """Purge foreign legacy directories and retired hooks from the plugin directory."""
    for stray in STRAY_PLUGIN_DIRS:
        stray_path = plugin_dir / stray
        if stray_path.is_symlink():
            stray_path.unlink(missing_ok=True)
        elif stray_path.is_dir():
            shutil.rmtree(stray_path, ignore_errors=True)
        elif stray_path.is_file():
            stray_path.unlink(missing_ok=True)
    hooks_file = plugin_dir / "hooks" / "hooks.json"
    if hooks_file.is_file():
        hooks_file.unlink(missing_ok=True)
    hooks_dir = plugin_dir / "hooks"
    if hooks_dir.is_dir() and not any(hooks_dir.iterdir()):
        try:
            hooks_dir.rmdir()
        except OSError:
            pass


def copy_skills(
    dest_skills: Path, source_root: Path | None = None, clean_stale: bool = False
) -> list[str]:
    src_skills = (source_root or ROOT) / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)
    copied_rel = []
    src_names = skill_names(src_skills)
    if clean_stale and dest_skills.is_dir():
        for existing_d in dest_skills.iterdir():
            if existing_d.name not in src_names and not existing_d.name.startswith("."):
                if existing_d.is_symlink():
                    existing_d.unlink()
                elif existing_d.is_dir():
                    shutil.rmtree(existing_d)
    for sname in sorted(src_names):
        item = src_skills / sname
        target = dest_skills / sname
        target.mkdir(parents=True, exist_ok=True)
        expected_files = skill_files(item)
        for rel_path, content in expected_files.items():
            dest_file = target / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if dest_file.is_symlink():
                dest_file.unlink()
            dest_file.write_bytes(content)
            copied_rel.append(f"skills/{sname}/{rel_path}")
        if clean_stale:
            actual_files = skill_files(target)
            for extra_rel in sorted(actual_files.keys() - expected_files.keys()):
                extra_p = target / extra_rel
                if extra_p.is_file() or extra_p.is_symlink():
                    extra_p.unlink()
    return copied_rel


def copy_agents(
    dest_agents: Path, source_root: Path | None = None, clean_stale: bool = False
) -> list[str]:
    src_agents = (source_root or ROOT) / "agents"
    dest_agents.mkdir(parents=True, exist_ok=True)
    copied_rel = []
    src_agent_files = {f.name for f in src_agents.glob("*.md") if f.is_file() and not f.name.startswith(".")}
    for fname in sorted(src_agent_files):
        src_file = src_agents / fname
        dest_file = dest_agents / fname
        if dest_file.is_symlink():
            dest_file.unlink()
        shutil.copy2(src_file, dest_file)
        copied_rel.append(f"agents/{fname}")
    if clean_stale:
        for existing_f in dest_agents.glob("*.md"):
            if existing_f.is_file() and existing_f.name not in src_agent_files:
                existing_f.unlink()
    return copied_rel


def write_antigravity_assets(
    plugin_dir: Path,
    desc: Any,
    src_root: Path,
    include_skills: bool = False,
    clean_stale: bool = True,
) -> None:
    """Project all Antigravity plugin files (manifest, models, commands, rules, assets, agents, profiles)."""
    manifest = generate_antigravity_manifest(desc)
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    models = generate_antigravity_models(desc)
    (plugin_dir / "models.json").write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

    cmds_dir = plugin_dir / "commands"
    cmds_dir.mkdir(parents=True, exist_ok=True)
    expected_cmds = generate_antigravity_commands(desc)
    for fname, toml_str in expected_cmds.items():
        (cmds_dir / fname).write_text(toml_str, encoding="utf-8")
    if clean_stale:
        for existing_cmd in cmds_dir.glob("*.toml"):
            if existing_cmd.is_file() and existing_cmd.name not in expected_cmds:
                existing_cmd.unlink()

    rules_dir = plugin_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rules_dest = rules_dir / "AGENTS.md"
    rules_dest.write_text(generate_antigravity_rules(), encoding="utf-8")

    purge_stray_plugin_dirs(plugin_dir)

    assets_dir = plugin_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    logo_src = src_root / "assets" / "logo.svg"
    if logo_src.is_file():
        shutil.copy2(logo_src, assets_dir / "logo.svg")

    agents_dir = plugin_dir / "agents"
    copy_agents(agents_dir, source_root=src_root, clean_stale=clean_stale)

    profiles_dest = plugin_dir / "profiles"
    profiles_dest.mkdir(parents=True, exist_ok=True)
    src_profiles_dir = resolve_profiles_dir(src_root)
    src_profiles = {p.name for p in src_profiles_dir.glob("*.json")}
    if clean_stale:
        for existing_p in profiles_dest.glob("*.json"):
            if existing_p.name not in src_profiles:
                existing_p.unlink(missing_ok=True)
    for p in src_profiles_dir.glob("*.json"):
        shutil.copy2(p, profiles_dest / p.name)

    if include_skills:
        copy_skills(plugin_dir / "skills", source_root=src_root, clean_stale=clean_stale)


def stage_antigravity_package(dest_dir: Path, source_root: Path | None = None) -> Path:
    """Stage a clean, standalone Antigravity plugin package for validation and installation."""
    from scripts.package_projection import load_package_descriptor
    src_root = source_root if source_root is not None else ROOT
    desc, _ = load_package_descriptor()
    dest_dir.mkdir(parents=True, exist_ok=True)
    write_antigravity_assets(dest_dir, desc, src_root, include_skills=True, clean_stale=True)
    return dest_dir


def compute_managed_files(host: str, desc: Any, source_root: Path | None = None) -> set[str]:
    """Compute the set of relative paths owned by pstack inside the plugin directory."""
    managed: set[str] = set()
    src_root = source_root if source_root is not None else ROOT

    # Manifests
    if host in ("opencode", "omp"):
        managed.add("package.json")
    elif host == "droid":
        managed.add(".factory-plugin/plugin.json")
        managed.add(".factory-plugin/marketplace.json")
        for fname in generate_droid_roles().keys():
            managed.add(f"droids/{fname}")
    else:
        managed.add("plugin.json")

    # Host specific projections
    if host == "antigravity":
        managed.add("models.json")
        managed.add("rules/AGENTS.md")
        managed.add("assets/logo.svg")
        for fname in generate_antigravity_commands(desc).keys():
            managed.add(f"commands/{fname}")
        profiles_dir = resolve_profiles_dir(src_root)
        for p in profiles_dir.glob("*.json"):
            managed.add(f"profiles/{p.name}")

    if host in ("grok", "antigravity", "omp"):
        for a in (src_root / "agents").glob("*.md"):
            managed.add(f"agents/{a.name}")

    # Canonical skills
    src_skills = src_root / "skills"
    for s_file in src_skills.rglob("*"):
        if s_file.is_file():
            rel = s_file.relative_to(src_skills)
            if not any(part.startswith(".") or part in SKILLS_HASH_IGNORED_DIRS for part in rel.parts) and not any(rel.name.endswith(sfx) for sfx in SKILLS_HASH_IGNORED_SUFFIXES):
                managed.add(f"skills/{rel.as_posix()}")

    managed.add(".pstack-managed-files.json")
    return managed


def safe_scan_plugin_tree(plugin_dir: Path) -> list[str]:
    """Scan all files and symlinks inside plugin_dir without following symlinks into loops."""
    rel_paths: list[str] = []
    if not plugin_dir.exists():
        return rel_paths

    for root, dirs, files in os.walk(plugin_dir, followlinks=False):
        root_path = Path(root)
        for f in files:
            f_path = root_path / f
            rel = f_path.relative_to(plugin_dir).as_posix()
            rel_paths.append(rel)
        for d in dirs:
            d_path = root_path / d
            if d_path.is_symlink():
                rel = d_path.relative_to(plugin_dir).as_posix()
                rel_paths.append(rel)
    return rel_paths


def get_unmanaged_paths(plugin_dir: Path, managed_files: set[str]) -> list[str]:
    """Identify all unexpected or user-authored paths inside plugin_dir."""
    all_found = safe_scan_plugin_tree(plugin_dir)
    return [p for p in all_found if p not in managed_files]


def clean_stale_managed_files(
    plugin_dir: Path, host: str, desc: Any, source_root: Path | None = None
) -> None:
    """Clean up previously managed files that are no longer part of the package."""
    managed_record_file = plugin_dir / ".pstack-managed-files.json"
    if not managed_record_file.is_file():
        return
    try:
        prev_record = json.loads(managed_record_file.read_text(encoding="utf-8"))
        old_managed = set(prev_record.get("managed_files", []))
        new_managed = compute_managed_files(host, desc, source_root=source_root)
        for stale_rel in old_managed - new_managed:
            stale_p = plugin_dir / stale_rel
            if stale_p.is_file() or stale_p.is_symlink():
                stale_p.unlink()
            parent = stale_p.parent
            while parent != plugin_dir and parent.is_relative_to(plugin_dir):
                try:
                    parent.rmdir()
                    parent = parent.parent
                except OSError:
                    break
    except (json.JSONDecodeError, OSError):
        pass


def record_managed_manifest(
    plugin_dir: Path, host: str, desc: Any, source_root: Path | None = None
) -> set[str]:
    """Record the managed files manifest in the plugin directory."""
    managed_set = compute_managed_files(host, desc, source_root=source_root)
    manifest_record = {
        "host": host,
        "version": desc.version,
        "managed_files": sorted(list(managed_set)),
    }
    (plugin_dir / ".pstack-managed-files.json").write_text(
        json.dumps(manifest_record, indent=2) + "\n", encoding="utf-8"
    )
    return managed_set


def stage_antigravity_native_install(
    plugin_dir: Path,
    standard_dir: Path,
    host: str,
    desc: Any,
    src_root: Path,
    target_base: Path | None,
) -> bool:
    """Attempt native agy plugin install if agy binary is available and targeting standard dir.

    Returns True if native installation was performed, False otherwise.
    """
    clean_stale_managed_files(plugin_dir, host, desc, source_root=src_root)
    agy_bin = find_agy_binary()
    is_standard_dir = (plugin_dir == standard_dir)
    if not (host == "antigravity" and agy_bin and is_standard_dir):
        return False

    with tempfile.TemporaryDirectory(prefix="pstack-agy-stage-") as tmp_stage:
        stage_dir = Path(tmp_stage)
        stage_antigravity_package(stage_dir, source_root=src_root)
        managed_set = compute_managed_files(host, desc, source_root=src_root)
        manifest_record = {
            "host": host,
            "version": desc.version,
            "managed_files": sorted(list(managed_set)),
        }
        (stage_dir / ".pstack-managed-files.json").write_text(
            json.dumps(manifest_record, indent=2) + "\n", encoding="utf-8"
        )

        unmanaged_paths = []
        if plugin_dir.exists():
            raw_unmanaged = get_unmanaged_paths(plugin_dir, managed_set)
            unmanaged_paths = [
                p for p in raw_unmanaged
                if not any(p == d or p.startswith(f"{d}/") for d in STRAY_PLUGIN_DIRS)
            ]

        with tempfile.TemporaryDirectory(prefix="pstack-unmanaged-backup-") as backup_tmp:
            backup_dir = Path(backup_tmp)
            for u_rel in unmanaged_paths:
                src_u = plugin_dir / u_rel
                if src_u.is_file() or src_u.is_symlink():
                    dest_u = backup_dir / u_rel
                    dest_u.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_u, dest_u, follow_symlinks=False)

            try:
                cmd = [agy_bin, "plugin", "install", str(stage_dir)]
                env = dict(os.environ)
                if target_base is not None:
                    env["HOME"] = str(target_base)
                proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False, timeout=120)
                if proc.returncode != 0:
                    raise RuntimeError(f"agy plugin install failed ({proc.returncode}): {proc.stderr or proc.stdout}")
            finally:
                for u_rel in unmanaged_paths:
                    src_u = backup_dir / u_rel
                    if src_u.is_file() or src_u.is_symlink():
                        dest_u = plugin_dir / u_rel
                        dest_u.parent.mkdir(parents=True, exist_ok=True)
                        if dest_u.is_symlink() or dest_u.is_file():
                            dest_u.unlink(missing_ok=True)
                        shutil.copy2(src_u, dest_u, follow_symlinks=False)
                purge_stray_plugin_dirs(plugin_dir)

    return True


def write_host_plugin_assets(plugin_dir: Path, host: str, desc: Any, src_root: Path) -> None:
    """Generate and write host-specific manifests, commands, and assets."""
    skills_dir = plugin_dir / "skills"
    copy_skills(skills_dir, source_root=src_root)

    if host == "grok":
        manifest = generate_grok_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        agents_dir = plugin_dir / "agents"
        copy_agents(agents_dir, source_root=src_root)

    elif host == "codex":
        manifest = generate_codex_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    elif host == "omp":
        legacy = plugin_dir / "plugin.json"
        if legacy.is_file():
            try:
                legacy_data = json.loads(legacy.read_text(encoding="utf-8"))
            except Exception:
                legacy_data = {}
            if isinstance(legacy_data, dict) and {"skills_root", "entrypoint"} <= set(legacy_data):
                legacy.unlink()
        manifest = generate_omp_manifest(desc)
        (plugin_dir / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        agents_dir = plugin_dir / "agents"
        copy_agents(agents_dir, source_root=src_root)

    elif host == "opencode":
        manifest = generate_opencode_manifest(desc)
        (plugin_dir / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    elif host == "antigravity":
        write_antigravity_assets(plugin_dir, desc, src_root, include_skills=False, clean_stale=True)

    elif host == "droid":
        plugin_meta = plugin_dir / ".factory-plugin"
        plugin_meta.mkdir(parents=True, exist_ok=True)
        manifest = generate_droid_manifest(desc)
        (plugin_meta / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        marketplace = generate_droid_marketplace(desc)
        (plugin_meta / "marketplace.json").write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")
        roles = generate_droid_roles()
        droids_dir = plugin_dir / "droids"
        droids_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in roles.items():
            (droids_dir / fname).write_text(content, encoding="utf-8")


def remove_managed_files_and_empty_dirs(plugin_dir: Path, managed_set: set[str]) -> list[str]:
    """Remove all managed files and clean up resulting empty parent directories."""
    errors: list[str] = []
    for rel_str in sorted(managed_set, reverse=True):
        p = plugin_dir / rel_str
        if p.is_file() or p.is_symlink():
            try:
                p.unlink()
            except OSError as e:
                errors.append(f"Failed to remove managed file {p}: {e}")

    for root, dirs, _files in os.walk(plugin_dir, topdown=False, followlinks=False):
        for d in dirs:
            d_path = Path(root) / d
            if not d_path.is_symlink() and d_path.is_dir():
                try:
                    d_path.rmdir()
                except OSError:
                    pass

    try:
        plugin_dir.rmdir()
    except OSError:
        pass

    return errors
