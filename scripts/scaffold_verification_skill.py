#!/usr/bin/env python3
"""Deterministic scaffolding and validation of portable verification skills.

Supports all 6 agent harnesses: Grok Build, Codex, OMP, OpenCode, Antigravity, Droid.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
# `portability_schema` imports the host identity seam through the `scripts`
# package, so the repository root has to be importable too when this CLI is run
# as a plain script (#446).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import DEFAULT_SKILLS_DIRS
from scripts.host_identity import require_builtin_host_keys
from scripts.setup_pstack import resolve_profiles_dir
from scripts.verification_skill_templates import (
    generate_driver_script,
    generate_feature_content,
    generate_features_readme,
    generate_skill_content,
)
from skill_frontmatter import SKILL_NAME_RE, read_scalar, split_frontmatter, validate_skill_name

REQUIRED_SECTIONS = [
    "Launch",
    "Doctor",
    "Drive",
    "Proof bar",
    "Evidence",
    "Cleanup",
    "Helpers",
]


# Detection order matters: a workspace can carry several host markers, so
# more specific hosts are probed first. Droid's `.factory` marker is last
# because the directory also appears in non-skill Droid setups.
HOST_DETECT_ORDER = ("antigravity", "codex", "omp", "opencode", "grok", "droid")

# The order above is a detection preference, but its key set is the identity set:
# a built-in added to `BUILTIN_HOSTS` and to `DEFAULT_SKILLS_DIRS` and missed here
# is never detected and silently falls through to the `"grok"` default (#446).
require_builtin_host_keys(HOST_DETECT_ORDER, "HOST_DETECT_ORDER")

CANDIDATE_HOSTS = ("pi",)


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
    for host in CANDIDATE_HOSTS:
        marker = f".{host}"
        if (workspace / marker).exists() or (workspace / marker / "skills").exists():
            return host
    return "grok"


def get_skill_dir(workspace: pathlib.Path, host: str, app: str, *, formal: bool = False) -> pathlib.Path:
    validate_app_name(app, allow_pstack=True)
    skills_rel = DEFAULT_SKILLS_DIRS.get(host, f".{host}/skills")
    effective_app = f"{app}-formal" if formal and not app.endswith("-formal") else app
    return workspace / skills_rel / f"verify-{effective_app}"


def validate_app_name(app: str, *, allow_pstack: bool = False) -> None:
    if not SKILL_NAME_RE.fullmatch(app):
        raise ValueError("Application name must be lowercase kebab-case")
    if app == "pstack" and not allow_pstack:
        raise ValueError("Application name 'pstack' is reserved for the plugin doctor")


def scaffold_skill(
    target_dir: pathlib.Path,
    app: str,
    host: str,
    *,
    formal: bool = False,
) -> None:
    validate_app_name(app)
    effective_app = f"{app}-formal" if formal and not app.endswith("-formal") else app
    feature_file = "features/formal-model.md" if formal else "features/core.md"
    outputs = {
        "SKILL.md": generate_skill_content(effective_app, host, formal=formal),
        "features/README.md": generate_features_readme(effective_app, formal=formal),
        feature_file: generate_feature_content(effective_app, formal=formal),
        "scripts/driver.sh": generate_driver_script(effective_app, formal=formal),
    }
    if any(path.is_symlink() for path in (target_dir, *target_dir.parents)):
        raise FileExistsError(f"Refusing symlink target or ancestor: {target_dir}")
    if target_dir.exists():
        if not target_dir.is_dir() or any(target_dir.iterdir()):
            raise FileExistsError(f"Refusing nonempty or non-directory target: {target_dir}")
    else:
        target_dir.mkdir(parents=True)
    (target_dir / "features").mkdir()
    (target_dir / "scripts").mkdir()
    for relative, content in outputs.items():
        out_path = target_dir / relative
        with out_path.open("x", encoding="utf-8") as output:
            output.write(content)
        if relative.endswith(".sh"):
            out_path.chmod(0o755)


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


def get_candidate_skills_dirs(workspace: pathlib.Path) -> List[str]:
    """Discover candidate skills directories declared in workspace profiles/*.json."""
    candidate_dirs: List[str] = []
    profiles_dir = resolve_profiles_dir(workspace)
    if profiles_dir.is_dir() and not profiles_dir.is_symlink():
        for path in sorted(profiles_dir.glob("*.json")):
            if path.is_file() and not path.is_symlink():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        skills_rel = data.get("skills_dir")
                        if (
                            isinstance(skills_rel, str)
                            and skills_rel
                            and skills_rel not in DEFAULT_SKILLS_DIRS.values()
                            and skills_rel not in candidate_dirs
                        ):
                            candidate_dirs.append(skills_rel)
                except (OSError, json.JSONDecodeError):
                    continue
    return candidate_dirs


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
            candidate_dirs = get_candidate_skills_dirs(target_dir.parents[2]) if len(target_dir.parents) >= 3 else []
            known_parents = tuple("/" + rel for rel in (*DEFAULT_SKILLS_DIRS.values(), *candidate_dirs))
            native_parent = target_dir.absolute().parent.as_posix().endswith(known_parents)
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

        if len(body.encode("utf-8")) > 24000:
            errors.append(
                f"SKILL.md body exceeds Antigravity 24000-byte limit ({len(body.encode('utf-8'))} bytes)"
            )

    errors.extend(check_feature_map(target_dir / "features"))

    driver_script = target_dir / "scripts" / "driver.sh"
    if not driver_script.exists():
        errors.append(f"Missing driver.sh in {target_dir / 'scripts'}")
    elif driver_script.is_symlink():
        errors.append(f"driver.sh must not be a symlink: {driver_script}")
    elif not os.access(driver_script, os.X_OK):
        errors.append(f"driver.sh is not executable: {driver_script}")
    else:
        driver_text = driver_script.read_text(encoding="utf-8")
        if "PYTHON_EXEC" in driver_text and "uv run python" not in driver_text:
            errors.append(f"driver.sh must resolve uv run python for reproducible execution: {driver_script}")
        if "BUN_EXEC" in driver_text and "bun" not in driver_text:
            errors.append(f"driver.sh must default BUN_EXEC to bun for reproducible execution: {driver_script}")

    return errors


def list_verification_skills(
    workspace: pathlib.Path,
    *,
    all_dirs: bool = False,
    include_candidates: bool = True,
) -> List[pathlib.Path]:
    results: List[pathlib.Path] = []
    seen: set[pathlib.Path] = set()

    for host, rel in DEFAULT_SKILLS_DIRS.items():
        base = workspace / rel
        if base.is_dir():
            for d in sorted(base.glob("verify-*")):
                if d.is_dir() and (all_dirs or (d / "SKILL.md").is_file()):
                    if d not in seen:
                        results.append(d)
                        seen.add(d)

    if include_candidates:
        for rel in get_candidate_skills_dirs(workspace):
            base = workspace / rel
            if base.is_dir():
                for d in sorted(base.glob("verify-*")):
                    if d.is_dir() and (all_dirs or (d / "SKILL.md").is_file()):
                        if d not in seen:
                            results.append(d)
                            seen.add(d)

    return results


def audit_verification_skills_data(workspace: pathlib.Path) -> Dict[str, Any]:
    skills = list_verification_skills(workspace, all_dirs=True)
    results: List[Dict[str, Any]] = []
    has_failures = False
    passed_count = 0
    failed_count = 0
    for skill in skills:
        rel = skill.relative_to(workspace).as_posix() if skill.is_relative_to(workspace) else str(skill)
        errors = check_skill(skill)
        if errors:
            has_failures = True
            failed_count += 1
            results.append({"path": rel, "status": "FAIL", "errors": errors})
        else:
            passed_count += 1
            results.append({"path": rel, "status": "PASS", "errors": []})
    return {
        "exit_code": 1 if has_failures else 0,
        "total_skills": len(skills),
        "passed": passed_count,
        "failed": failed_count,
        "skills": results,
    }


def audit_verification_skills(workspace: pathlib.Path) -> Tuple[int, List[str]]:
    data = audit_verification_skills_data(workspace)
    if not data["skills"]:
        return 0, ["No verification skills found to audit."]
    results: List[str] = []
    for item in data["skills"]:
        results.append(f"{item['status']}: {item['path']}")
        for err in item["errors"]:
            results.append(f"  - {err}")
    return data["exit_code"], results


def audit_openspec_status(workspace: pathlib.Path) -> Dict[str, Any]:
    """Audit OpenSpec active changes and living specifications for verification readiness."""
    openspec_dir = workspace / "openspec"
    if not openspec_dir.is_dir():
        return {
            "exit_code": 1,
            "status": "FAIL",
            "errors": [f"openspec directory missing: {openspec_dir}"],
            "active_changes": [],
            "living_specs": [],
        }

    errors: List[str] = []
    active_changes: List[str] = []
    changes_dir = openspec_dir / "changes"
    if changes_dir.is_dir():
        for change in sorted(changes_dir.iterdir()):
            if not change.is_dir() or change.name == "archive":
                continue
            active_changes.append(change.name)
            for req in ("proposal.md", "tasks.md", ".openspec.yaml"):
                if not (change / req).is_file():
                    errors.append(f"Change '{change.name}' missing {req}")

    living_specs: List[str] = []
    specs_dir = openspec_dir / "specs"
    if specs_dir.is_dir():
        for spec in sorted(specs_dir.iterdir()):
            if not spec.is_dir():
                continue
            living_specs.append(spec.name)
            if not (spec / "spec.md").is_file():
                errors.append(f"Living spec '{spec.name}' missing spec.md")

    return {
        "exit_code": 1 if errors else 0,
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "active_changes": active_changes,
        "living_specs": living_specs,
    }


def drive_verification_skill(
    target_dir: pathlib.Path,
    *,
    command: Optional[str] = None,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """Execute verification driver script for a single skill."""
    rel = str(target_dir)
    driver_script = target_dir / "scripts" / "driver.sh"
    if not driver_script.is_file() or not os.access(driver_script, os.X_OK):
        return {
            "path": rel,
            "status": "FAIL",
            "command": command or "default",
            "exit_code": 127,
            "duration_s": 0.0,
            "stdout": "",
            "stderr": f"Driver script missing or not executable: {driver_script}",
        }

    t0 = time.time()
    try:
        if command:
            proc = subprocess.run(
                ["bash", str(driver_script), command],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            dur = time.time() - t0
            if proc.returncode == 0:
                status = "PASS"
            elif command == "cleanup" and proc.returncode == 2 and "BLOCKED" in proc.stderr:
                status = "BLOCKED"
            else:
                status = "FAIL"
            return {
                "path": rel,
                "status": status,
                "command": command,
                "exit_code": proc.returncode,
                "duration_s": round(dur, 3),
                "stdout": proc.stdout.strip()[:300],
                "stderr": proc.stderr.strip()[:300],
            }

        primary = "doctor" if target_dir.name == "verify-decision-contract" else "drive"
        p_launch = subprocess.run(
            ["bash", str(driver_script), "launch"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if p_launch.returncode != 0:
            dur = time.time() - t0
            return {
                "path": rel,
                "status": "FAIL",
                "command": "launch",
                "exit_code": p_launch.returncode,
                "duration_s": round(dur, 3),
                "stdout": p_launch.stdout.strip()[:300],
                "stderr": p_launch.stderr.strip()[:300],
            }

        p_primary = subprocess.run(
            ["bash", str(driver_script), primary],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        subprocess.run(
            ["bash", str(driver_script), "cleanup"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        dur = time.time() - t0
        status = "PASS" if p_primary.returncode == 0 else "FAIL"
        return {
            "path": rel,
            "status": status,
            "command": f"launch && {primary}",
            "exit_code": p_primary.returncode,
            "duration_s": round(dur, 3),
            "stdout": p_primary.stdout.strip()[:300],
            "stderr": p_primary.stderr.strip()[:300],
        }
    except subprocess.TimeoutExpired as exc:
        dur = time.time() - t0
        return {
            "path": rel,
            "status": "FAIL",
            "command": command or "auto",
            "exit_code": 124,
            "duration_s": round(dur, 3),
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s: {exc}",
        }


def drive_all_verification_skills(
    workspace: pathlib.Path,
    *,
    command: Optional[str] = None,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """Execute drivers across all discovered verification skills."""
    skills = list_verification_skills(workspace, all_dirs=True)
    results: List[Dict[str, Any]] = []
    passed_count = 0
    blocked_count = 0
    failed_count = 0
    for skill in skills:
        res = drive_verification_skill(skill, command=command, timeout=timeout)
        rel = skill.relative_to(workspace).as_posix() if skill.is_relative_to(workspace) else str(skill)
        res["path"] = rel
        if res["status"] == "PASS":
            passed_count += 1
        elif res["status"] == "BLOCKED":
            blocked_count += 1
        else:
            failed_count += 1
        results.append(res)
    return {
        "exit_code": 1 if failed_count > 0 else 0,
        "total_skills": len(skills),
        "passed": passed_count,
        "blocked": blocked_count,
        "failed": failed_count,
        "skills": results,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold or check portable verification skills.")
    parser.add_argument(
        "--host",
        choices=list(DEFAULT_SKILLS_DIRS.keys()) + list(CANDIDATE_HOSTS),
        help="Target agent harness",
    )
    parser.add_argument("--app", help="Application name for verify-<app>")
    parser.add_argument("--formal", action="store_true", help="Scaffold formal verification skill (model checker, provers, bounded falsifiers)")
    parser.add_argument("--target-dir", type=pathlib.Path, help="Explicit target directory for skill")
    parser.add_argument("--workspace", type=pathlib.Path, default=pathlib.Path.cwd(), help="Workspace root")
    parser.add_argument("--write", action="store_true", help="Scaffold verification skill files")
    parser.add_argument("--check", action="store_true", help="Validate existing verification skill")
    parser.add_argument("--list", action="store_true", help="Discover verification skills across harnesses")
    parser.add_argument("--audit", action="store_true", help="Audit all verification skills across all 6 harnesses")
    parser.add_argument("--check-openspec", action="store_true", help="Audit OpenSpec active changes and living specifications")
    parser.add_argument("--drive-all", action="store_true", help="Execute launch and drive/doctor across all verification skills")
    parser.add_argument("--doctor-all", action="store_true", help="Execute doctor across all verification skills")
    parser.add_argument("--cleanup-all", action="store_true", help="Execute cleanup across all verification skills")
    parser.add_argument("--drive", action="store_true", help="Execute driver for a single verification skill specified by --target-dir or --app")
    parser.add_argument("--command", choices=["doctor", "launch", "drive", "cleanup", "all"], default=None, help="Explicit driver verb to execute")
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-command timeout in seconds (default: 60.0)")
    parser.add_argument("--json", action="store_true", help="Output audit, list, or check results as JSON")

    args = parser.parse_args(argv)

    if args.app is not None:
        try:
            validate_app_name(args.app, allow_pstack=not args.write)
        except ValueError as exc:
            parser.error(str(exc))

    workspace = args.workspace.resolve()

    if args.audit:
        if args.json:
            data = audit_verification_skills_data(workspace)
            print(json.dumps(data, indent=2))
            return data["exit_code"]
        code, lines = audit_verification_skills(workspace)
        for line in lines:
            print(line)
        return code

    if args.check_openspec:
        data = audit_openspec_status(workspace)
        if args.json:
            print(json.dumps(data, indent=2))
            return data["exit_code"]
        if data["exit_code"] != 0:
            print("FAIL: OpenSpec audit found errors:")
            for err in data["errors"]:
                print(f"  - {err}")
            return data["exit_code"]
        print(f"PASS: OpenSpec audit verified {len(data['active_changes'])} active change(s) and {len(data['living_specs'])} living spec(s).")
        return 0

    if args.drive_all:
        data = drive_all_verification_skills(workspace, command=args.command, timeout=args.timeout)
        if args.json:
            print(json.dumps(data, indent=2))
            return data["exit_code"]
        for item in data["skills"]:
            print(f"[{item['status']}] {item['path']} ({item.get('command')}) {item.get('duration_s', 0):.2f}s")
        return data["exit_code"]

    if args.doctor_all:
        data = drive_all_verification_skills(workspace, command="doctor", timeout=args.timeout)
        if args.json:
            print(json.dumps(data, indent=2))
            return data["exit_code"]
        for item in data["skills"]:
            print(f"[{item['status']}] {item['path']} ({item.get('command')}) {item.get('duration_s', 0):.2f}s")
        return data["exit_code"]

    if args.cleanup_all:
        data = drive_all_verification_skills(workspace, command="cleanup", timeout=args.timeout)
        if args.json:
            print(json.dumps(data, indent=2))
            return data["exit_code"]
        for item in data["skills"]:
            print(f"[{item['status']}] {item['path']} ({item.get('command')}) {item.get('duration_s', 0):.2f}s")
        return data["exit_code"]

    if args.list:
        skills = list_verification_skills(workspace)
        if args.json:
            rel_skills = [
                (s.relative_to(workspace).as_posix() if s.is_relative_to(workspace) else str(s))
                for s in skills
            ]
            print(json.dumps({"count": len(skills), "skills": rel_skills}, indent=2))
            return 0
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
        target = args.target_dir or get_skill_dir(workspace, host, args.app, formal=args.formal)
        try:
            scaffold_skill(target, args.app, host, formal=args.formal)
        except (ValueError, FileExistsError) as exc:
            parser.error(str(exc))
        kind = "formal " if args.formal else ""
        print(f"Draft {kind}scaffold for '{args.app}' on {host} at {target}; requires tailoring and runtime proof.")
        return 0

    if args.check:
        if args.target_dir:
            target = args.target_dir
        elif args.app:
            target = get_skill_dir(workspace, host, args.app, formal=args.formal)
        else:
            print("Error: --target-dir or --app required with --check", file=sys.stderr)
            return 2

        try:
            errors = check_skill(target)
        except (ValueError, FileExistsError) as exc:
            parser.error(str(exc))
        if args.json:
            status = "FAIL" if errors else "PASS"
            res = {
                "path": str(target),
                "status": status,
                "errors": errors,
            }
            print(json.dumps(res, indent=2))
            return 1 if errors else 0
        if errors:
            print(f"FAIL: Verification skill at {target} has errors:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: Structural validation of verification skill at {target}; runtime proof unassessed.")
        return 0

    if args.drive:
        if args.target_dir:
            target = args.target_dir
        elif args.app:
            target = get_skill_dir(workspace, host, args.app, formal=args.formal)
        else:
            print("Error: --target-dir or --app required with --drive", file=sys.stderr)
            return 2

        res = drive_verification_skill(target, command=args.command, timeout=args.timeout)
        if args.json:
            print(json.dumps(res, indent=2))
            return res["exit_code"]
        print(f"[{res['status']}] {res['path']} ({res.get('command')}) {res.get('duration_s', 0):.2f}s")
        if res["exit_code"] != 0 and res.get("stderr"):
            print(f"Error: {res['stderr']}", file=sys.stderr)
        return res["exit_code"]

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
