#!/usr/bin/env python3
"""Native package lifecycle driver for pstack across supported harnesses.

Implements Build the Lever + Model the Domain + Make Operations Idempotent:
Provides real lifecycle management (install, verify, update, uninstall, prove)
separating package deployment from validation and ensuring clean residue.

Usage:
    python3 scripts/package_lifecycle.py install [--host <host>] [--target-dir <dir>]
    python3 scripts/package_lifecycle.py verify [--host <host>] [--target-dir <dir>]
    python3 scripts/package_lifecycle.py update [--host <host>] [--target-dir <dir>]
    python3 scripts/package_lifecycle.py uninstall [--host <host>] [--target-dir <dir>]
    python3 scripts/package_lifecycle.py prove [--host <host>] [--target-dir <dir>]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.host_identity import BUILTIN_HOSTS, require_builtin_host_keys  # noqa: E402
from scripts.portability_schema import (  # noqa: E402
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
)
from scripts.setup_pstack import resolve_profiles_dir

from scripts.package_projection import (
    check_all as check_all_projected,
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
    load_package_descriptor,
)

SUPPORTED_HOSTS = BUILTIN_HOSTS

HOST_PLUGIN_REL_PATHS = {
    "grok": Path(".grok/plugins/pstack"),
    "codex": Path(".codex/plugins/pstack"),
    "omp": Path(".omp/plugins/pstack"),
    "opencode": Path(".opencode/plugins/pstack"),
    "antigravity": Path(".gemini/config/plugins/pstack"),
    "droid": Path(".factory/plugins/pstack"),
}
require_builtin_host_keys(HOST_PLUGIN_REL_PATHS, "HOST_PLUGIN_REL_PATHS")


def get_plugin_dir(host: str, target_base: Optional[Path] = None) -> Path:
    rel = HOST_PLUGIN_REL_PATHS[host]
    if target_base is not None:
        return target_base / rel
    return Path.home() / rel


class ForeignSourceError(RuntimeError):
    """Raised when a write would clobber a deploy tree pstack does not own."""


# The one record of the retired Grok-specific release label (#699). A tree that
# still carries it is not silently accepted and not reported as a generic
# mismatch: the check names the retirement and the upgrade command that
# converges it. Entries are permanent history; never delete one.
RETIRED_VERSIONS = {
    "0.15.29-grokbuild.0": "the Grok-specific release label; the package identity is now host-neutral",
}


def _traverses_symlink(path: Path) -> bool:
    """True when `path` or any of its ancestors is a symlink.

    A symlinked leaf is obvious; a symlinked ancestor (e.g. `~/.grok` bound to
    another harness home) is the same hazard one level up: the path names a tree
    pstack never created, so deleting "managed files" inside it hits foreign
    content.

    Deliberately walks to the filesystem root, so a platform alias (macOS
    `/var` -> `/private/var`) also reads as foreign. That costs a refusal on
    such hosts, never a delete, and pstack's CI and deploy hosts are Linux.
    """
    return any(candidate.is_symlink() for candidate in (path, *path.parents))


def is_owned_deploy_target(live_dir: Path) -> bool:
    """True only for installed copies pstack itself deployed.

    pstack installs real directories at `HOST_PLUGIN_REL_PATHS`. A symlinked
    (leaf or ancestor) or marketplace-bind install is a foreign-source variant
    (the Claude variant's `pstack-claude` symlinked tree, e.g. `~/.agents/skills`
    -> the pstack-claude checkout, or `~/.claude/plugins/cache/pstack-claude`).
    Those carry a different source tree, so a freshness comparison against this
    repo would false-fail — and a delete would hit content pstack does not own.
    They are excluded instead.
    """
    if _traverses_symlink(live_dir):
        return False
    if "marketplaces" in live_dir.parts:
        return False
    return not any("pstack-claude" in part for part in live_dir.parts)


def _tree_files(base: Path) -> Dict[str, bytes]:
    """Files under a skills/agents tree, using the canonical skills-hash policy.

    Mirrors `SKILLS_HASH_IGNORED_DIRS`/`_SUFFIXES` (plus dot-prefixed paths) so
    `node_modules`, `__pycache__`, and bytecode never count as drift.
    """
    files: Dict[str, bytes] = {}
    if not base.is_dir():
        return files
    for path in base.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(base)
        if any(part.startswith(".") or part in SKILLS_HASH_IGNORED_DIRS for part in rel.parts):
            continue
        if path.suffix in SKILLS_HASH_IGNORED_SUFFIXES:
            continue
        files[rel.as_posix()] = path.read_bytes()
    return files


def freshness_errors(plugin_dir: Path) -> List[str]:
    """Compare the repo-owned skills/agents trees against an installed copy.

    Only trees pstack actually copies are compared, so hosts that project
    without agents (codex, opencode) or into `droids/` (droid) don't get a
    spurious "missing agents" verdict.
    """
    errors: List[str] = []
    for subtree in ("skills", "agents"):
        src = ROOT / subtree
        live = plugin_dir / subtree
        if not src.is_dir() or (subtree == "agents" and not live.is_dir()):
            continue
        expected = _tree_files(src)
        actual = _tree_files(live)
        drifted = sorted(
            name for name in expected.keys() & actual.keys() if expected[name] != actual[name]
        )
        for label, names in (
            ("missing", sorted(expected.keys() - actual.keys())),
            ("extra", sorted(actual.keys() - expected.keys())),
            ("drifted", drifted),
        ):
            if names:
                errors.append(
                    f"Stale installed copy at {plugin_dir}: {label} {subtree} {names}"
                )
    return errors


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

    import os
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


def install_plugin(
    host: str,
    target_base: Optional[Path] = None,
    force: bool = False,
    target_dir: Optional[Path] = None,
    source_root: Optional[Path] = None,
) -> Path:
    src_root = source_root or ROOT
    desc, _ = load_package_descriptor()
    standard_dir = get_plugin_dir(host, target_base)
    plugin_dir = target_dir if target_dir is not None else standard_dir
    if not force and not is_owned_deploy_target(plugin_dir):
        raise ForeignSourceError(f"refusing to install over a foreign-source install at {plugin_dir}")

    agy_bin = shutil.which("agy")
    is_standard_dir = (plugin_dir == standard_dir)
    if host == "antigravity" and agy_bin and is_standard_dir:
        from scripts.prove_antigravity_native_package import stage_antigravity_package
        import os, subprocess
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

            # Preserve pre-existing unmanaged user files before native agy plugin install
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

                # Restore preserved unmanaged user files
                for u_rel in unmanaged_paths:
                    src_u = backup_dir / u_rel
                    if src_u.is_file() or src_u.is_symlink():
                        dest_u = plugin_dir / u_rel
                        dest_u.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_u, dest_u, follow_symlinks=False)
        return plugin_dir

    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Clean up previously managed files that are no longer part of the package
    managed_record_file = plugin_dir / ".pstack-managed-files.json"
    if managed_record_file.is_file():
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
        # The pre-native projection wrote a generated plugin.json that OMP never
        # reads. Remove it only when it is that generated shape, so a tree
        # installed before the cutover does not keep a dead manifest forever and
        # a user-authored file is never touched.
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

        # Clean up stale hooks that relied on CLAUDE_PLUGIN_ROOT
        hooks_file = plugin_dir / "hooks" / "hooks.json"
        if hooks_file.is_file():
            hooks_file.unlink()

        # Clean up foreign / legacy directories
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

    # Record ownership manifest
    managed_set = compute_managed_files(host, desc)
    manifest_record = {
        "host": host,
        "version": desc.version,
        "managed_files": sorted(list(managed_set)),
    }
    (plugin_dir / ".pstack-managed-files.json").write_text(
        json.dumps(manifest_record, indent=2) + "\n", encoding="utf-8"
    )

    return plugin_dir


def verify_plugin(host: str, target_base: Optional[Path] = None) -> Tuple[bool, List[str]]:
    desc, _ = load_package_descriptor()
    errors: List[str] = []

    # If no target_base provided and running in repository context:
    if target_base is None:
        # Check projected manifests in repository
        ok = check_all_projected(desc, [host])
        if not ok:
            errors.append(f"Repository projected manifest check failed for {host}")

        # Installed-copy freshness for repo-owned deploy targets only (#404).
        # A foreign-source variant install is skipped by is_owned_deploy_target.
        live_dir = get_plugin_dir(host)
        if live_dir.is_dir() and is_owned_deploy_target(live_dir):
            live_ok, live_errs = verify_plugin_at_dir(host, live_dir, desc)
            if not live_ok:
                errors.extend(live_errs)
            errors.extend(freshness_errors(live_dir))
        return len(errors) == 0, errors

    plugin_dir = get_plugin_dir(host, target_base)
    return verify_plugin_at_dir(host, plugin_dir, desc)


def verify_plugin_at_dir(host: str, plugin_dir: Path, desc: Any) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not plugin_dir.is_dir():
        return False, [f"Plugin directory does not exist: {plugin_dir}"]

    # 1. Manifest verification
    if host == "droid":
        manifest_path = plugin_dir / ".factory-plugin" / "plugin.json"
        marketplace_path = plugin_dir / ".factory-plugin" / "marketplace.json"
        if not marketplace_path.is_file():
            errors.append(f"Missing marketplace file: {marketplace_path}")
        else:
            try:
                mk_data = json.loads(marketplace_path.read_text(encoding="utf-8"))
                if mk_data.get("plugins", [{}])[0].get("name") != desc.name:
                    errors.append(f"Droid marketplace plugin name mismatch: {mk_data.get('plugins')}")
            except Exception as e:
                errors.append(f"Marketplace file corrupt: {e}")
        droids_dir = plugin_dir / "droids"
        if not droids_dir.is_dir() or len(list(droids_dir.glob("*.md"))) == 0:
            errors.append(f"Missing or empty droids directory: {droids_dir}")
    else:
        manifest_name = "package.json" if host in ("opencode", "omp") else "plugin.json"
        manifest_path = plugin_dir / manifest_name
    if not manifest_path.is_file():
        errors.append(f"Missing manifest file: {manifest_path}")
    else:
        try:
            m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if host == "opencode":
                if m_data.get("id") != desc.id:
                    errors.append(f"OpenCode manifest id mismatch: {m_data.get('id')} != {desc.id}")
            else:
                if m_data.get("name") != desc.name:
                    errors.append(f"Manifest name mismatch: {m_data.get('name')} != {desc.name}")
                if host == "omp" and not isinstance(m_data.get("omp"), dict):
                    errors.append("OMP manifest is missing the package.json#omp key OMP enrolls packages with")
            installed = m_data.get("version")
            # A malformed manifest can carry a non-string here; only a string can
            # name a retired identity, and the dict lookup would raise on the rest.
            if isinstance(installed, str) and installed in RETIRED_VERSIONS:
                errors.append(
                    f"{host} carries retired version {installed} ({RETIRED_VERSIONS[installed]});"
                    f" run `package_lifecycle.py update --host {host}` to converge on {desc.version}"
                )
            elif installed != desc.version:
                errors.append(f"Manifest version mismatch: {installed} != {desc.version}")
        except Exception as e:
            errors.append(f"Manifest file corrupt: {e}")

    # 2. Skills & Router verification
    skills_dir = plugin_dir / "skills"
    router_file = skills_dir / "poteto-mode" / "SKILL.md"
    if not router_file.is_file():
        errors.append(f"Missing poteto-mode router skill at: {router_file}")

    canonical_skills = (
        "babysit",
        "deslop",
        "fix-ci",
        "fix-merge-conflicts",
        "get-pr-comments",
        "make-pr-easy-to-review",
        "thermo-nuclear-code-quality-review",
        "what-did-i-get-done",
    )
    for c_skill in canonical_skills:
        skill_md = skills_dir / c_skill / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"Missing canonical skill {c_skill} in {skills_dir}")

    # 3. Host-specific component verification
    if host in ("grok", "antigravity", "omp"):
        agents_dir = plugin_dir / "agents"
        if not agents_dir.is_dir() or len(list(agents_dir.glob("*.md"))) == 0:
            errors.append(f"Missing or empty agents directory: {agents_dir}")

    if host == "antigravity":
        models_file = plugin_dir / "models.json"
        if not models_file.is_file():
            errors.append(f"Missing models.json: {models_file}")
        else:
            try:
                mod_data = json.loads(models_file.read_text(encoding="utf-8"))
                if "singleRoleDefault" not in mod_data:
                    errors.append("models.json missing singleRoleDefault")
            except Exception as e:
                errors.append(f"Corrupt models.json: {e}")

        logo_file = plugin_dir / "assets" / "logo.svg"
        if not logo_file.is_file():
            errors.append(f"Missing logo file at: {logo_file}")

        cmds_dir = plugin_dir / "commands"
        if cmds_dir.is_dir() and len(list(cmds_dir.glob("*.toml"))) < len(desc.commands):
            errors.append(f"Missing or incomplete commands in: {cmds_dir}")

        profiles_dir = plugin_dir / "profiles"
        if not profiles_dir.is_dir() or len(list(profiles_dir.glob("*.json"))) < 9:
            errors.append(f"Missing or incomplete root profiles in: {profiles_dir}")

        setup_profiles = plugin_dir / "skills" / "setup-pstack" / "profiles"
        if not setup_profiles.is_dir() or len(list(setup_profiles.glob("*.json"))) < 9:
            errors.append(f"Missing or incomplete packaged profiles in: {setup_profiles}")

    return len(errors) == 0, errors


def update_plugin(host: str, target_base: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Idempotently re-install and verify convergence."""
    try:
        install_plugin(host, target_base)
    except ForeignSourceError as exc:
        return False, [f"Update refused for {host}: {exc}"]
    ok, errors = verify_plugin(host, target_base)
    if not ok:
        return False, [f"Update verification failed for {host}: {errors}"]

    # Second pass proves idempotent convergence
    install_plugin(host, target_base)
    ok2, errors2 = verify_plugin(host, target_base)
    if not ok2:
        return False, [f"Idempotent re-run verification failed for {host}: {errors2}"]

    return True, []


def uninstall_plugin(host: str, target_base: Optional[Path] = None, force: bool = False) -> Tuple[bool, List[str]]:
    """Uninstall plugin and verify clean residue state without destroying unmanaged content."""
    plugin_dir = get_plugin_dir(host, target_base)
    errors: List[str] = []

    if not plugin_dir.exists():
        return True, []

    if not is_owned_deploy_target(plugin_dir):
        return False, [f"refusing to uninstall a foreign-source install at {plugin_dir}"]

    desc, _ = load_package_descriptor()

    # Identify managed files from recorded manifest or derived defaults
    managed_file = plugin_dir / ".pstack-managed-files.json"
    managed_set: Set[str] = set()
    if managed_file.is_file():
        try:
            data = json.loads(managed_file.read_text(encoding="utf-8"))
            managed_set = set(data.get("managed_files", []))
        except Exception:
            pass
    if not managed_set:
        managed_set = compute_managed_files(host, desc)

    unmanaged_before = get_unmanaged_paths(plugin_dir, managed_set)

    agy_bin = shutil.which("agy")
    if host == "antigravity" and agy_bin and (force or not unmanaged_before):
        import os, subprocess
        cmd = [agy_bin, "plugin", "uninstall", "pstack"]
        env = dict(os.environ)
        if target_base is not None:
            env["HOME"] = str(target_base)
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0 and "not found" not in (proc.stderr + proc.stdout).lower():
            errors.append(f"agy plugin uninstall failed: {proc.stderr or proc.stdout}")
        if not unmanaged_before and not plugin_dir.exists():
            # Clean residue check: parent directory should not be corrupted
            if target_base is not None and not target_base.exists():
                errors.append(f"Uninstall corrupted target base directory: {target_base}")
            return len(errors) == 0, errors

    if force:
        shutil.rmtree(plugin_dir)
    else:
        # Delete ONLY managed files and symlinks
        for rel_str in sorted(managed_set, reverse=True):
            p = plugin_dir / rel_str
            if p.is_file() or p.is_symlink():
                try:
                    p.unlink()
                except OSError as e:
                    errors.append(f"Failed to remove managed file {p}: {e}")

        # Clean up empty directories from bottom up
        import os
        for root, dirs, files in os.walk(plugin_dir, topdown=False, followlinks=False):
            for d in dirs:
                d_path = Path(root) / d
                if not d_path.is_symlink() and d_path.is_dir():
                    try:
                        d_path.rmdir()
                    except OSError:
                        pass  # Directory not empty because contains unmanaged files

        # If plugin_dir is now empty, remove it
        try:
            plugin_dir.rmdir()
        except OSError:
            pass

    # Clean residue check: if there were NO unmanaged files, plugin directory must be gone
    if not unmanaged_before and plugin_dir.exists():
        errors.append(f"Plugin directory still exists after clean uninstall: {plugin_dir}")

    # If unmanaged files were present, ensure they are preserved!
    if unmanaged_before:
        for u_rel in unmanaged_before:
            u_path = plugin_dir / u_rel
            if not u_path.exists():
                errors.append(f"Unmanaged file was unexpectedly deleted during uninstall: {u_rel}")

    # Clean residue check: parent directory should not be corrupted
    parent = plugin_dir.parent
    if target_base is not None and not target_base.exists():
        errors.append(f"Uninstall corrupted target base directory: {target_base}")

    return len(errors) == 0, errors


def prove_lifecycle(host: str, target_base: Optional[Path] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """Execute full isolated lifecycle proof gauntlet:

    1. Prepare isolated workspace with user sentinel file
    2. Install -> verify
    3. Update -> verify idempotent convergence
    4. Uninstall -> verify clean residue & user sentinel preservation
    """
    cleanup_needed = False
    if target_base is None:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"pstack-lifecycle-{host}-")
        target_base = Path(temp_dir_obj.name)
        cleanup_needed = True
    else:
        target_base.mkdir(parents=True, exist_ok=True)

    scenarios: List[Dict[str, Any]] = []
    overall_pass = True

    try:
        # Step 0: User state preservation setup
        user_sentinel = target_base / f".{host}-user-sentinel.json"
        user_sentinel.write_text(json.dumps({"user_config": "custom_value", "host": host}), encoding="utf-8")

        # Step 1: Install
        t0 = time.perf_counter()
        installed_dir = get_plugin_dir(host, target_base)
        try:
            installed_dir = install_plugin(host, target_base)
            ok_verify, v_errs = verify_plugin_at_dir(host, installed_dir, load_package_descriptor()[0])
        except ForeignSourceError as exc:
            ok_verify, v_errs = False, [str(exc)]
        d_install = time.perf_counter() - t0
        scenarios.append({
            "step": "install",
            "verdict": "PASS" if ok_verify else "FAIL",
            "duration_s": d_install,
            "details": f"Installed {host} into {installed_dir} (verified={ok_verify}, errors={v_errs})",
        })
        if not ok_verify:
            overall_pass = False

        # Step 2: Update convergence
        t0 = time.perf_counter()
        ok_update, u_errs = update_plugin(host, target_base)
        d_update = time.perf_counter() - t0
        scenarios.append({
            "step": "update",
            "verdict": "PASS" if ok_update else "FAIL",
            "duration_s": d_update,
            "details": f"Idempotent convergence check for {host} (errors={u_errs})",
        })
        if not ok_update:
            overall_pass = False

        # Step 3: Uninstall & Clean residue
        t0 = time.perf_counter()
        ok_uninst, un_errs = uninstall_plugin(host, target_base)
        d_uninst = time.perf_counter() - t0
        sentinel_intact = user_sentinel.is_file() and json.loads(user_sentinel.read_text(encoding="utf-8")).get("user_config") == "custom_value"
        residue_pass = ok_uninst and sentinel_intact and not installed_dir.exists()
        scenarios.append({
            "step": "uninstall",
            "verdict": "PASS" if residue_pass else "FAIL",
            "duration_s": d_uninst,
            "details": f"Clean residue verified: plugin removed={not installed_dir.exists()}, user sentinel preserved={sentinel_intact}",
        })
        if not residue_pass:
            overall_pass = False

    finally:
        if cleanup_needed:
            try:
                temp_dir_obj.cleanup()
            except Exception:
                pass

    return overall_pass, scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "verify", "update", "uninstall", "prove"], help="Lifecycle action")
    parser.add_argument("--host", choices=list(SUPPORTED_HOSTS) + ["all"], default="all", help="Target harness")
    parser.add_argument("--target-dir", type=Path, default=None, help="Target home/workspace directory")
    args = parser.parse_args()

    hosts = list(SUPPORTED_HOSTS) if args.host == "all" else [args.host]
    all_ok = True

    for h in hosts:
        print(f"[{h}] Executing {args.action}...")
        if args.action == "install":
            try:
                p = install_plugin(h, args.target_dir)
            except ForeignSourceError as exc:
                print(f"[{h}] INSTALL REFUSED: {exc}")
                all_ok = False
                continue
            print(f"[{h}] Installed to {p}")
        elif args.action == "verify":
            ok, errs = verify_plugin(h, args.target_dir)
            if not ok:
                print(f"[{h}] VERIFY FAILED:\n  " + "\n  ".join(errs))
                all_ok = False
            else:
                print(f"[{h}] VERIFY PASS")
        elif args.action == "update":
            ok, errs = update_plugin(h, args.target_dir)
            if not ok:
                print(f"[{h}] UPDATE FAILED:\n  " + "\n  ".join(errs))
                all_ok = False
            else:
                print(f"[{h}] UPDATE PASS (converged)")
        elif args.action == "uninstall":
            ok, errs = uninstall_plugin(h, args.target_dir)
            if not ok:
                print(f"[{h}] UNINSTALL FAILED:\n  " + "\n  ".join(errs))
                all_ok = False
            else:
                print(f"[{h}] UNINSTALL PASS (clean residue)")
        elif args.action == "prove":
            ok, scenarios = prove_lifecycle(h, args.target_dir)
            for sc in scenarios:
                print(f"  [{sc['step']}] {sc['verdict']} ({sc['duration_s']:.3f}s) - {sc['details']}")
            if not ok:
                print(f"[{h}] PROVE FAILED")
                all_ok = False
            else:
                print(f"[{h}] PROVE PASS")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
