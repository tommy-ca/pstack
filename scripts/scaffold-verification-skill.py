#!/usr/bin/env python3
"""Deterministic scaffolding and validation of portable verification skills.

Supports all 6 agent harnesses: Grok Build, Codex, OMP, OpenCode, Antigravity, Droid.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import List

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from portability_schema import DEFAULT_SKILLS_DIRS
from skill_frontmatter import SKILL_NAME_RE, read_scalar, split_frontmatter, validate_skill_name

REQUIRED_SECTIONS = [
    "Launch",
    "Doctor",
    "Drive",
    "Proof bar",
    "Evidence",
    "Cleanup",
]


# Detection order matters: a workspace can carry several host markers, so
# more specific hosts are probed first. Droid's `.factory` marker is last
# because the directory also appears in non-skill Droid setups.
HOST_DETECT_ORDER = ("antigravity", "codex", "omp", "opencode", "grok", "droid")


def detect_host(workspace: pathlib.Path) -> str:
    """Auto-detect active harness from workspace markers."""
    for host in HOST_DETECT_ORDER:
        skills_rel = DEFAULT_SKILLS_DIRS.get(host)
        if skills_rel and (workspace / skills_rel).exists():
            return host
        # Check parent folder marker like .agents, .codex, etc.
        marker = skills_rel.split("/")[0] if skills_rel else f".{host}"
        if (workspace / marker).exists():
            return host
    return "grok"


def get_skill_dir(workspace: pathlib.Path, host: str, app: str) -> pathlib.Path:
    validate_app_name(app, allow_pstack=True)
    skills_rel = DEFAULT_SKILLS_DIRS.get(host, f".{host}/skills")
    return workspace / skills_rel / f"verify-{app}"


def validate_app_name(app: str, *, allow_pstack: bool = False) -> None:
    if not SKILL_NAME_RE.fullmatch(app):
        raise ValueError("Application name must be lowercase kebab-case")
    if app == "pstack" and not allow_pstack:
        raise ValueError("Application name 'pstack' is reserved for the plugin doctor")


def generate_skill_content(app: str, host: str) -> str:
    return f"""---
name: verify-{app}
description: "Use when verifying, reproducing, or proving behavior for {app} on {host}."
disable-model-invocation: true
---

# Verify {app}

Draft requiring tailoring with concrete app commands and a shipped driver.
Structural validation does not assess runtime proof.

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
    validate_app_name(app)
    outputs = {
        "SKILL.md": generate_skill_content(app, host),
        "features/README.md": generate_features_readme(app),
        "features/core.md": generate_feature_content(app),
    }
    if any(path.is_symlink() for path in (target_dir, *target_dir.parents)):
        raise FileExistsError(f"Refusing symlink target or ancestor: {target_dir}")
    if target_dir.exists():
        if not target_dir.is_dir() or any(target_dir.iterdir()):
            raise FileExistsError(f"Refusing nonempty or non-directory target: {target_dir}")
    else:
        target_dir.mkdir(parents=True)
    (target_dir / "features").mkdir()
    for relative, content in outputs.items():
        with (target_dir / relative).open("x", encoding="utf-8") as output:
            output.write(content)


def map_references(section: str) -> List[str]:
    references = []
    for line in section.splitlines():
        if not re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line):
            continue
        references.extend(re.findall(r"\[[^\]]*\]\(([^)]+)\)", line))
        without_links = re.sub(r"\[[^\]]*\]\([^)]+\)", "", line)
        references.extend(re.findall(r"`([^`]*\.md)`", without_links))
    return references


def check_feature_map(features_dir: pathlib.Path) -> List[str]:
    errors = []
    if features_dir.is_symlink() or not features_dir.is_dir():
        return [f"Missing regular features/ directory in {features_dir.parent}"]
    readme = features_dir / "README.md"
    if readme.is_symlink() or not readme.is_file():
        return ["Missing regular features/README.md"]

    text = readme.read_text(encoding="utf-8")
    parts = re.split(r"^##\s+([^\n]+)\s*$", text, flags=re.MULTILINE)
    sections = {heading.strip(): body for heading, body in zip(parts[1::2], parts[2::2])}
    if len(sections) != len(parts[1::2]):
        errors.append("features/README.md has duplicate sections")
    if "Full sweep" not in sections:
        errors.append("features/README.md missing '## Full sweep' section")
    sweep = map_references(sections.get("Full sweep", ""))
    index = map_references(sections.get("Features", ""))
    if not sweep and not index:
        errors.append("features/README.md requires a nonempty ordered Full sweep or Features list")
    if not sweep and index and not sections.get("Full sweep", "").strip():
        errors.append("Full sweep requires ordered references or prose directing the Features order")

    feature_files = {}
    for path in sorted(features_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        if path.is_symlink() or not path.is_file():
            errors.append(f"Feature must be a regular sibling markdown file: {path.name}")
        else:
            feature_files[path.name] = path
    if not feature_files:
        errors.append("features/ must contain at least one feature markdown file")

    normalized_lists = []
    for label, references in (("Full sweep", sweep), ("Features", index)):
        normalized = []
        for reference in references:
            path = pathlib.PurePosixPath(reference)
            if path.is_absolute() or len(path.parts) != 1 or path.suffix != ".md" or path.name == "README.md":
                errors.append(f"{label} reference must stay inside features/ as a sibling: {reference}")
                continue
            name = path.name
            if name in normalized:
                errors.append(f"Duplicate {label} reference: {name}")
            normalized.append(name)
            if name not in feature_files:
                errors.append(f"Missing regular feature for {label} reference: {reference}")
        normalized_lists.append(normalized)
    ordered = normalized_lists[0] if sweep else normalized_lists[1]
    for name in sorted(feature_files.keys() - set(ordered)):
        errors.append(f"Unlisted feature in Full sweep: {name}")
    if sweep and index and set(normalized_lists[0]) != set(normalized_lists[1]):
        errors.append("Full sweep and Features references disagree")

    for name, path in feature_files.items():
        headings = re.findall(r"^##\s+([^\n]+?)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE)
        if (
            len(headings) != 4
            or headings[:2] != ["Sub-features", "How to get to it (user POV)"]
            or not re.fullmatch(r"Driving it with\s+\S.*", headings[2])
            or headings[3] != "Gotchas"
        ):
            errors.append(f"{name} requires the four feature sections in order, including 'Driving it with <harness>'")
    return errors


def check_skill(target_dir: pathlib.Path) -> List[str]:
    errors: List[str] = []
    if target_dir.is_symlink() or not target_dir.is_dir():
        return [f"Directory does not exist: {target_dir}"]

    skill_md = target_dir / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        errors.append(f"Missing SKILL.md in {target_dir}")
    else:
        text = skill_md.read_text(encoding="utf-8")
        body = ""
        try:
            header, body = split_frontmatter(text)
            native_parent = target_dir.absolute().parent.as_posix().endswith(
                tuple("/" + rel for rel in DEFAULT_SKILLS_DIRS.values())
            )
            expected = target_dir.name if native_parent else None
            name = validate_skill_name(read_scalar(header, "name"), expected)
            if not name.startswith("verify-") or not SKILL_NAME_RE.fullmatch(name[7:]):
                raise ValueError("frontmatter name must be verify-<app>")
            if not read_scalar(header, "description"):
                raise ValueError("frontmatter requires a nonempty description")
            if read_scalar(header, "disable-model-invocation") != "true":
                raise ValueError("frontmatter requires 'disable-model-invocation: true'")
        except ValueError as exc:
            errors.append(f"SKILL.md {exc}")
        for sec in REQUIRED_SECTIONS:
            pattern = rf"^##\s+{re.escape(sec)}\b"
            if not re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
                errors.append(f"SKILL.md missing required section '## {sec}'")

    errors.extend(check_feature_map(target_dir / "features"))

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

    if args.app is not None:
        try:
            validate_app_name(args.app, allow_pstack=not args.write)
        except ValueError as exc:
            parser.error(str(exc))

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
        try:
            scaffold_skill(target, args.app, host)
        except (ValueError, FileExistsError) as exc:
            parser.error(str(exc))
        print(f"Draft scaffold for '{args.app}' on {host} at {target}; requires tailoring and runtime proof.")
        return 0

    if args.check:
        if args.target_dir:
            target = args.target_dir
        elif args.app:
            target = get_skill_dir(workspace, host, args.app)
        else:
            print("Error: --target-dir or --app required with --check", file=sys.stderr)
            return 2

        try:
            errors = check_skill(target)
        except (ValueError, FileExistsError) as exc:
            parser.error(str(exc))
        if errors:
            print(f"FAIL: Verification skill at {target} has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: Structural validation of verification skill at {target}; runtime proof unassessed.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
