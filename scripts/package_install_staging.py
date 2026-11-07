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
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]

from scripts.setup_pstack import resolve_profiles_dir
from scripts.package_projection import (
    generate_antigravity_commands,
    generate_antigravity_manifest,
    generate_antigravity_models,
    generate_codex_manifest,
    generate_droid_manifest,
    generate_droid_marketplace,
    generate_droid_roles,
    generate_grok_manifest,
    generate_omp_manifest,
    generate_opencode_manifest,
)


def copy_skills(dest_skills: Path, source_root: Optional[Path] = None) -> List[str]:
    from scripts.sync_antigravity_plugin import skill_files, skill_names
    src_skills = (source_root or ROOT) / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)
    copied_rel = []
    src_names = skill_names(src_skills)
    for sname in sorted(src_names):
        item = src_skills / sname
        target = dest_skills / sname
        target.mkdir(parents=True, exist_ok=True)
        for rel_path, content in skill_files(item).items():
            dest_file = target / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(content)
            copied_rel.append(f"skills/{sname}/{rel_path}")
    return copied_rel


def copy_agents(dest_agents: Path, source_root: Optional[Path] = None) -> List[str]:
    src_agents = (source_root or ROOT) / "agents"
    dest_agents.mkdir(parents=True, exist_ok=True)
    copied_rel = []
    src_agent_files = {f.name for f in src_agents.glob("*.md") if f.is_file()}
    for fname in sorted(src_agent_files):
        shutil.copy2(src_agents / fname, dest_agents / fname)
        copied_rel.append(f"agents/{fname}")
    for existing_f in dest_agents.glob("*.md"):
        if existing_f.is_file() and existing_f.name not in src_agent_files:
            existing_f.unlink()
    return copied_rel


def compute_managed_files(host: str, desc: Any) -> Set[str]:
    """Compute the set of relative paths owned by pstack inside the plugin directory."""
    managed: Set[str] = set()

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
        profiles_dir = resolve_profiles_dir(ROOT)
        for p in profiles_dir.glob("*.json"):
            managed.add(f"profiles/{p.name}")

    if host in ("grok", "antigravity", "omp"):
        for a in (ROOT / "agents").glob("*.md"):
            managed.add(f"agents/{a.name}")

    # Canonical skills
    src_skills = ROOT / "skills"
    for s_file in src_skills.rglob("*"):
        if s_file.is_file():
            rel = s_file.relative_to(src_skills)
            if not any(part.startswith(".") for part in rel.parts):
                managed.add(f"skills/{rel.as_posix()}")

    managed.add(".pstack-managed-files.json")
    return managed


def safe_scan_plugin_tree(plugin_dir: Path) -> List[str]:
    """Scan all files and symlinks inside plugin_dir without following symlinks into loops."""
    rel_paths: List[str] = []
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


def get_unmanaged_paths(plugin_dir: Path, managed_files: Set[str]) -> List[str]:
    """Identify all unexpected or user-authored paths inside plugin_dir."""
    all_found = safe_scan_plugin_tree(plugin_dir)
    return [p for p in all_found if p not in managed_files]


def clean_stale_managed_files(plugin_dir: Path, host: str, desc: Any) -> None:
    """Clean up previously managed files that are no longer part of the package."""
    managed_record_file = plugin_dir / ".pstack-managed-files.json"
    if not managed_record_file.is_file():
        return
    try:
        prev_record = json.loads(managed_record_file.read_text(encoding="utf-8"))
        old_managed = set(prev_record.get("managed_files", []))
        new_managed = compute_managed_files(host, desc)
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
    except Exception:
        pass


def record_managed_manifest(plugin_dir: Path, host: str, desc: Any) -> Set[str]:
    """Record the managed files manifest in the plugin directory."""
    managed_set = compute_managed_files(host, desc)
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
    target_base: Optional[Path],
) -> bool:
    """Attempt native agy plugin install if agy binary is available and targeting standard dir.

    Returns True if native installation was performed, False otherwise.
    """
    agy_bin = shutil.which("agy")
    is_standard_dir = (plugin_dir == standard_dir)
    if not (host == "antigravity" and agy_bin and is_standard_dir):
        return False

    from scripts.prove_antigravity_native_package import stage_antigravity_package
    with tempfile.TemporaryDirectory(prefix="pstack-agy-stage-") as tmp_stage:
        stage_dir = Path(tmp_stage)
        stage_antigravity_package(stage_dir, source_root=src_root)
        managed_set = compute_managed_files(host, desc)
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
            unmanaged_paths = get_unmanaged_paths(plugin_dir, managed_set)

        with tempfile.TemporaryDirectory(prefix="pstack-unmanaged-backup-") as backup_tmp:
            backup_dir = Path(backup_tmp)
            for u_rel in unmanaged_paths:
                src_u = plugin_dir / u_rel
                if src_u.is_file() or src_u.is_symlink():
                    dest_u = backup_dir / u_rel
                    dest_u.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_u, dest_u, follow_symlinks=False)

            cmd = [agy_bin, "plugin", "install", str(stage_dir)]
            env = dict(os.environ)
            if target_base is not None:
                env["HOME"] = str(target_base)
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(f"agy plugin install failed ({proc.returncode}): {proc.stderr or proc.stdout}")

            for u_rel in unmanaged_paths:
                src_u = backup_dir / u_rel
                if src_u.is_file() or src_u.is_symlink():
                    dest_u = plugin_dir / u_rel
                    dest_u.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_u, dest_u, follow_symlinks=False)

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
        manifest = generate_antigravity_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        models = generate_antigravity_models(desc)
        (plugin_dir / "models.json").write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

        cmds_dir = plugin_dir / "commands"
        cmds_dir.mkdir(parents=True, exist_ok=True)
        expected_cmds = generate_antigravity_commands(desc)
        for fname, toml_str in expected_cmds.items():
            (cmds_dir / fname).write_text(toml_str, encoding="utf-8")
        for existing_cmd in cmds_dir.glob("*.toml"):
            if existing_cmd.is_file() and existing_cmd.name not in expected_cmds:
                existing_cmd.unlink()

        rules_dir = plugin_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rules_dest = rules_dir / "AGENTS.md"
        rules_dest.write_text(
            "# pstack instructions for Antigravity\n\n"
            "When working with pstack:\n"
            "- Prefer fewer, higher-quality changes.\n"
            "- Follow poteto-mode: go deep first, plan before coding, verify with levereable proofs.\n"
            "- Use native subagents (`invoke_subagent`) for parallel operations (Arena, Swarm, Interrogate).\n"
            "- Respect isolated workspaces (`Workspace: branch`) when modifying code in parallel.\n",
            encoding="utf-8",
        )

        hooks_file = plugin_dir / "hooks" / "hooks.json"
        if hooks_file.is_file():
            hooks_file.unlink()

        for stray in [".codex-plugin", ".claude-plugin"]:
            stray_path = plugin_dir / stray
            if stray_path.exists():
                shutil.rmtree(stray_path)

        assets_dir = plugin_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        logo_src = src_root / "assets" / "logo.svg"
        if logo_src.is_file():
            shutil.copy2(logo_src, assets_dir / "logo.svg")

        agents_dir = plugin_dir / "agents"
        copy_agents(agents_dir, source_root=src_root)

        profiles_dest = plugin_dir / "profiles"
        profiles_dest.mkdir(parents=True, exist_ok=True)
        for p in resolve_profiles_dir(src_root).glob("*.json"):
            shutil.copy2(p, profiles_dest / p.name)

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


def remove_managed_files_and_empty_dirs(plugin_dir: Path, managed_set: Set[str]) -> List[str]:
    """Remove all managed files and clean up resulting empty parent directories."""
    errors: List[str] = []
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
