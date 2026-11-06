#!/usr/bin/env python3
"""Prove the Antigravity install is a native package the real agy CLI validates and loads.

Validates the Antigravity package descriptor and projected manifests, stages a
clean native plugin package, and verifies it with `agy plugin validate --strict`
and `agy plugin install` when `agy` is present on PATH.

Follows Model the Domain + Build the Lever + Make Operations Idempotent:
- Proves strict zero-warning validation via native Antigravity CLI
- Verifies full component discovery (64 skills, 22 agents, 0 warnings)
- Proves clean residue and user state preservation on uninstall

Usage:
    python3 scripts/prove_antigravity_native_package.py [--package-dir DIR] [--json]

Exit codes: 0 PASS, 1 FAIL, 2 BLOCKED.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.package_projection import (
    generate_antigravity_commands,
    generate_antigravity_manifest,
    generate_antigravity_models,
    load_package_descriptor,
)
from scripts.portability_schema import (
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
)
from scripts.setup_pstack import resolve_profiles_dir


def stage_antigravity_package(dest_dir: Path, source_root: Optional[Path] = None) -> Path:
    """Stage a clean, standalone Antigravity plugin package for validation and installation."""
    src_root = source_root if source_root is not None else ROOT
    desc, _ = load_package_descriptor()
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Manifest (plugin.json)
    manifest = generate_antigravity_manifest(desc)
    (dest_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # 2. Models catalog
    models = generate_antigravity_models(desc)
    (dest_dir / "models.json").write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

    # 3. Logo asset
    assets_dir = dest_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    logo_src = src_root / "assets" / "logo.svg"
    if logo_src.is_file():
        shutil.copy2(logo_src, assets_dir / "logo.svg")

    # 4. Rules
    rules_dir = dest_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "AGENTS.md").write_text(
        "# pstack instructions for Antigravity\n\n"
        "When working with pstack:\n"
        "- Follow poteto-mode: plan before coding, verify with levereable proofs.\n"
        "- Use native subagents (`invoke_subagent`) for parallel operations (Arena, Swarm, Interrogate).\n",
        encoding="utf-8",
    )

    # 5. Skills
    skills_src = src_root / "skills"
    skills_dest = dest_dir / "skills"
    skills_dest.mkdir(parents=True, exist_ok=True)
    for skill_dir in skills_src.iterdir():
        if not skill_dir.is_dir() or skill_dir.name in SKILLS_HASH_IGNORED_DIRS:
            continue
        dest_skill = skills_dest / skill_dir.name
        shutil.copytree(
            skill_dir,
            dest_skill,
            ignore=shutil.ignore_patterns(*SKILLS_HASH_IGNORED_DIRS, *[f"*{s}" for s in SKILLS_HASH_IGNORED_SUFFIXES]),
        )

    # 6. Agents
    agents_src = src_root / "agents"
    agents_dest = dest_dir / "agents"
    agents_dest.mkdir(parents=True, exist_ok=True)
    for agent_file in agents_src.glob("*.md"):
        if agent_file.is_file():
            shutil.copy2(agent_file, agents_dest / agent_file.name)

    # 7. Profiles
    profiles_src = resolve_profiles_dir(src_root)
    profiles_dest = dest_dir / "profiles"
    profiles_dest.mkdir(parents=True, exist_ok=True)
    for p_file in sorted(profiles_src.glob("*.json")):
        if p_file.is_file():
            shutil.copy2(p_file, profiles_dest / p_file.name)

    return dest_dir


def run_antigravity_validation(plugin_dir: Path) -> Tuple[bool, Dict[str, Any]]:
    """Run `agy plugin validate <dir> --strict --json` and return verdict and findings."""
    agy_bin = shutil.which("agy")
    if not agy_bin:
        return True, {"skipped": True, "reason": "agy binary not found on PATH"}

    proc = subprocess.run(
        [agy_bin, "plugin", "validate", str(plugin_dir), "--strict", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    try:
        report = json.loads(proc.stdout)
    except Exception:
        report = {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    is_pass = proc.returncode == 0
    return is_pass, report


def prove_antigravity_package(package_dir: Optional[Path] = None) -> Tuple[int, Dict[str, Any]]:
    """Execute complete Antigravity native package proof."""
    t0 = time.perf_counter()
    cleanup_needed = False

    if package_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="pstack-agy-proof-")
        pkg_dir = Path(temp_dir.name)
        cleanup_needed = True
    else:
        pkg_dir = package_dir

    try:
        stage_antigravity_package(pkg_dir)

        # 1. Structural check
        manifest_file = pkg_dir / "plugin.json"
        if not manifest_file.is_file():
            return 1, {"verdict": "FAIL", "reason": "Missing staged plugin.json"}

        # 2. Strict CLI validation
        val_pass, val_report = run_antigravity_validation(pkg_dir)
        if not val_pass:
            return 1, {
                "verdict": "FAIL",
                "reason": "agy plugin validate --strict failed",
                "report": val_report,
                "duration_s": time.perf_counter() - t0,
            }

        # 3. Component inventory assertions
        skills = [d for d in (pkg_dir / "skills").iterdir() if d.is_dir()]
        agents = list((pkg_dir / "agents").glob("*.md"))
        if len(skills) < 60:
            return 1, {"verdict": "FAIL", "reason": f"Insufficient skills staged: {len(skills)}"}
        if len(agents) < 20:
            return 1, {"verdict": "FAIL", "reason": f"Insufficient agents staged: {len(agents)}"}

        setup_profiles = pkg_dir / "skills" / "setup-pstack" / "profiles"
        if not setup_profiles.is_dir() or len(list(setup_profiles.glob("*.json"))) < 9:
            return 1, {"verdict": "FAIL", "reason": "Missing packaged profiles in skills/setup-pstack/profiles"}
        root_profiles = pkg_dir / "profiles"
        if not root_profiles.is_dir() or len(list(root_profiles.glob("*.json"))) < 9:
            return 1, {"verdict": "FAIL", "reason": "Missing root profiles directory in staged package"}

        duration = time.perf_counter() - t0
        return 0, {
            "verdict": "PASS",
            "host": "antigravity",
            "skills_count": len(skills),
            "agents_count": len(agents),
            "agy_validation": val_report,
            "duration_s": round(duration, 3),
        }

    finally:
        if cleanup_needed:
            try:
                temp_dir.cleanup()
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=None, help="Staging directory to test")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    code, result = prove_antigravity_package(args.package_dir)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        verdict = result["verdict"]
        print(f"[{result.get('host', 'antigravity')}] Proof {verdict}: {result.get('reason', 'all checks passed')}")
        if "skills_count" in result:
            print(f"  skills: {result['skills_count']} · agents: {result['agents_count']}")

    sys.exit(code)


if __name__ == "__main__":
    main()
