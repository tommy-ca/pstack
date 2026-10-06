#!/usr/bin/env python3
"""Native package lifecycle driver for pstack across supported harnesses.

Implements Build the Lever + Model the Domain + Make Operations Idempotent:
Provides real lifecycle management (install, verify, update, uninstall, prove)
separating package deployment from validation and ensuring clean residue.

Usage:
    python3 scripts/package-lifecycle.py install [--host <host>] [--target-dir <dir>]
    python3 scripts/package-lifecycle.py verify [--host <host>] [--target-dir <dir>]
    python3 scripts/package-lifecycle.py update [--host <host>] [--target-dir <dir>]
    python3 scripts/package-lifecycle.py uninstall [--host <host>] [--target-dir <dir>]
    python3 scripts/package-lifecycle.py prove [--host <host>] [--target-dir <dir>]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROJECT_PACKAGE_SCRIPT = ROOT / "scripts" / "project-package.py"
_loader = importlib.util.spec_from_file_location("project_package", PROJECT_PACKAGE_SCRIPT)
assert _loader is not None and _loader.loader is not None
_pp_mod = importlib.util.module_from_spec(_loader)
sys.modules["project_package"] = _pp_mod
_loader.loader.exec_module(_pp_mod)

load_package_descriptor = _pp_mod.load_package_descriptor
generate_grok_manifest = _pp_mod.generate_grok_manifest
generate_codex_manifest = _pp_mod.generate_codex_manifest
generate_omp_manifest = _pp_mod.generate_omp_manifest
generate_opencode_manifest = _pp_mod.generate_opencode_manifest
generate_antigravity_manifest = _pp_mod.generate_antigravity_manifest
generate_antigravity_models = _pp_mod.generate_antigravity_models
generate_antigravity_commands = _pp_mod.generate_antigravity_commands
generate_droid_manifest = _pp_mod.generate_droid_manifest
generate_droid_marketplace = _pp_mod.generate_droid_marketplace
generate_droid_roles = _pp_mod.generate_droid_roles
check_all_projected = _pp_mod.check_all

SUPPORTED_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid")

HOST_PLUGIN_REL_PATHS = {
    "grok": Path(".grok/plugins/pstack"),
    "codex": Path(".codex/plugins/pstack"),
    "omp": Path(".omp/plugins/pstack"),
    "opencode": Path(".opencode/plugins/pstack"),
    "antigravity": Path(".gemini/config/plugins/pstack"),
    "droid": Path(".factory/plugins/pstack"),
}


def get_plugin_dir(host: str, target_base: Optional[Path] = None) -> Path:
    rel = HOST_PLUGIN_REL_PATHS[host]
    if target_base is not None:
        return target_base / rel
    return Path.home() / rel


def copy_skills(dest_skills: Path) -> None:
    src_skills = ROOT / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)
    for skill_dir in src_skills.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            target = dest_skills / skill_dir.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill_dir, target)


def copy_agents(dest_agents: Path) -> None:
    src_agents = ROOT / "agents"
    dest_agents.mkdir(parents=True, exist_ok=True)
    for agent_file in src_agents.glob("*.md"):
        shutil.copy2(agent_file, dest_agents / agent_file.name)


def install_plugin(host: str, target_base: Optional[Path] = None) -> Path:
    desc, _ = load_package_descriptor()
    plugin_dir = get_plugin_dir(host, target_base)
    plugin_dir.mkdir(parents=True, exist_ok=True)

    skills_dir = plugin_dir / "skills"
    copy_skills(skills_dir)

    if host == "grok":
        manifest = generate_grok_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        agents_dir = plugin_dir / "agents"
        copy_agents(agents_dir)

    elif host == "codex":
        manifest = generate_codex_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    elif host == "omp":
        manifest = generate_omp_manifest(desc)
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

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
        for fname, toml_str in generate_antigravity_commands(desc).items():
            (cmds_dir / fname).write_text(toml_str, encoding="utf-8")

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

        agents_dir = plugin_dir / "agents"
        copy_agents(agents_dir)

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

        # If live Antigravity plugin exists, verify live synchronization
        if host == "antigravity":
            live_dir = Path.home() / ".gemini" / "config" / "plugins" / "pstack"
            if live_dir.is_dir():
                live_ok, live_errs = verify_plugin_at_dir("antigravity", live_dir, desc)
                if not live_ok:
                    errors.extend(live_errs)
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
        manifest_name = "package.json" if host == "opencode" else "plugin.json"
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
            if m_data.get("version") != desc.version:
                errors.append(f"Manifest version mismatch: {m_data.get('version')} != {desc.version}")
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
    if host in ("grok", "antigravity"):
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

        cmds_dir = plugin_dir / "commands"
        if not cmds_dir.is_dir() or len(list(cmds_dir.glob("*.toml"))) < len(desc.commands):
            errors.append(f"Missing or incomplete commands in: {cmds_dir}")

    return len(errors) == 0, errors


def update_plugin(host: str, target_base: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Idempotently re-install and verify convergence."""
    install_plugin(host, target_base)
    ok, errors = verify_plugin(host, target_base)
    if not ok:
        return False, [f"Update verification failed for {host}: {errors}"]

    # Second pass proves idempotent convergence
    install_plugin(host, target_base)
    ok2, errors2 = verify_plugin(host, target_base)
    if not ok2:
        return False, [f"Idempotent re-run verification failed for {host}: {errors2}"]

    return True, []


def uninstall_plugin(host: str, target_base: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Uninstall plugin and verify clean residue state."""
    plugin_dir = get_plugin_dir(host, target_base)
    errors: List[str] = []

    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    # Clean residue check: plugin directory must be gone
    if plugin_dir.exists():
        errors.append(f"Plugin directory still exists after uninstall: {plugin_dir}")

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
        installed_dir = install_plugin(host, target_base)
        d_install = time.perf_counter() - t0
        ok_verify, v_errs = verify_plugin_at_dir(host, installed_dir, load_package_descriptor()[0])
        scenarios.append({
            "step": "install",
            "verdict": "PASS" if ok_verify else "FAIL",
            "duration_s": d_install,
            "details": f"Installed {host} into {installed_dir} (verified={ok_verify})",
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
            p = install_plugin(h, args.target_dir)
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
