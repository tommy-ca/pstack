#!/usr/bin/env python3
"""Deterministic scaffolding and validation of portable verification skills.

Supports all 5 agent harnesses: Grok Build, Codex, OMP, OpenCode, Antigravity.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from portability_schema import DEFAULT_SKILLS_DIRS, HOSTS

REQUIRED_SECTIONS = [
    "Launch",
    "Doctor",
    "Drive",
    "Proof bar",
    "Evidence",
    "Cleanup",
]


def detect_host(workspace: pathlib.Path) -> str:
    """Auto-detect active harness from workspace markers."""
    for host in ("antigravity", "codex", "omp", "opencode", "grok"):
        skills_rel = DEFAULT_SKILLS_DIRS.get(host)
        if skills_rel and (workspace / skills_rel).exists():
            return host
        # Check parent folder marker like .agents, .codex, etc.
        marker = skills_rel.split("/")[0] if skills_rel else f".{host}"
        if (workspace / marker).exists():
            return host
    return "grok"


def get_skill_dir(workspace: pathlib.Path, host: str, app: str) -> pathlib.Path:
    skills_rel = DEFAULT_SKILLS_DIRS.get(host, f".{host}/skills")
    return workspace / skills_rel / f"verify-{app}"


def generate_skill_content(app: str, host: str) -> str:
    return f"""---
name: verify-{app}
description: "Use when verifying, reproducing, or proving behavior for {app} on {host}."
disable-model-invocation: true
---

# Verify {app}

Scripted harness to drive, test, and prove behavior for {app}.

## Launch

Start local instance in an isolated environment. Verify process readiness before driving.

## Doctor

Read-only health check. Confirm binary, dependencies, and environment are valid before driving.

## Drive

Drive user paths through programmatic commands or test runner. Prefer stable handles.

## Proof bar

Verify production path plus observable side effects. Exercise happy, error, and boundary states.

## Evidence

Capture test outputs, exit codes, transcripts, and artifacts. Verify they survive teardown.

## Cleanup

Tear down any processes or temporary instances spawned during verification.
"""


def generate_features_readme(app: str) -> str:
    return f"""# Feature Map for {app}

## Full sweep

Order of verification sweep across features:
1. `core.md`

## Features

- [`core.md`](core.md): Core application behavior.
"""


def generate_feature_content(app: str) -> str:
    return f"""# Core Feature: {app}

## Sub-features
- Initial startup
- Primary command execution

## How to get to it (user POV)
Invoke `{app}` with required arguments.

## Driving it with harness
Execute verification recipe and assert exit code 0.

## Gotchas
Ensure working directory and dependencies are initialized.
"""


def scaffold_skill(target_dir: pathlib.Path, app: str, host: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    features_dir = target_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    skill_md = target_dir / "SKILL.md"
    skill_md.write_text(generate_skill_content(app, host), encoding="utf-8")

    readme_md = features_dir / "README.md"
    readme_md.write_text(generate_features_readme(app), encoding="utf-8")

    core_md = features_dir / "core.md"
    core_md.write_text(generate_feature_content(app), encoding="utf-8")


def check_skill(target_dir: pathlib.Path) -> List[str]:
    errors: List[str] = []
    if not target_dir.is_dir():
        return [f"Directory does not exist: {target_dir}"]

    skill_md = target_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"Missing SKILL.md in {target_dir}")
    else:
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append("SKILL.md missing YAML frontmatter opening '---'")
        if "disable-model-invocation: true" not in text:
            errors.append("SKILL.md missing 'disable-model-invocation: true'")
        for sec in REQUIRED_SECTIONS:
            pattern = rf"^##\s+{re.escape(sec)}\b"
            if not re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                errors.append(f"SKILL.md missing required section '## {sec}'")

    features_dir = target_dir / "features"
    if not features_dir.is_dir():
        errors.append(f"Missing features/ directory in {target_dir}")
    else:
        readme = features_dir / "README.md"
        if not readme.is_file():
            errors.append(f"Missing features/README.md in {target_dir}")
        else:
            rtext = readme.read_text(encoding="utf-8")
            if "## Full sweep" not in rtext:
                errors.append("features/README.md missing '## Full sweep' section")

        feature_files = [f for f in features_dir.glob("*.md") if f.name != "README.md"]
        if not feature_files:
            errors.append("features/ must contain at least one feature markdown file")

    return errors


def list_verification_skills(workspace: pathlib.Path) -> List[pathlib.Path]:
    results: List[pathlib.Path] = []
    for host, rel in DEFAULT_SKILLS_DIRS.items():
        base = workspace / rel
        if base.is_dir():
            for d in base.glob("verify-*"):
                if d.is_dir() and (d / "SKILL.md").is_file():
                    results.append(d)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold or check portable verification skills.")
    parser.add_argument("--host", choices=list(DEFAULT_SKILLS_DIRS.keys()), help="Target agent harness")
    parser.add_argument("--app", help="Application name for verify-<app>")
    parser.add_argument("--target-dir", type=pathlib.Path, help="Explicit target directory for skill")
    parser.add_argument("--workspace", type=pathlib.Path, default=pathlib.Path.cwd(), help="Workspace root")
    parser.add_argument("--write", action="store_true", help="Scaffold verification skill files")
    parser.add_argument("--check", action="store_true", help="Validate existing verification skill")
    parser.add_argument("--list", action="store_true", help="Discover verification skills across harnesses")

    args = parser.parse_args()

    workspace = args.workspace.resolve()

    if args.list:
        skills = list_verification_skills(workspace)
        print(f"Found {len(skills)} verification skill(s):")
        for s in skills:
            rel = s.relative_to(workspace) if s.is_relative_to(workspace) else s
            print(f"  {rel}")
        return 0

    host = args.host or detect_host(workspace)

    if args.write:
        if not args.app:
            print("Error: --app required when scaffolding with --write", file=sys.stderr)
            return 2
        target = args.target_dir or get_skill_dir(workspace, host, args.app)
        scaffold_skill(target, args.app, host)
        print(f"Scaffolded verification skill for '{args.app}' on {host} at {target}")
        return 0

    if args.check:
        if args.target_dir:
            target = args.target_dir
        elif args.app:
            target = get_skill_dir(workspace, host, args.app)
        else:
            print("Error: --target-dir or --app required with --check", file=sys.stderr)
            return 2

        errors = check_skill(target)
        if errors:
            print(f"FAIL: Verification skill at {target} has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: Verification skill at {target} is valid.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
