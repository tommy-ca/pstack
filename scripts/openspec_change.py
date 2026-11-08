"""OpenSpec change resolution and validation (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, List, Literal, Optional, Tuple

ChangeState = Literal["explicit", "active", "none", "lookup-failed", "ambiguous"]


@dataclass(frozen=True)
class ChangeResolution:
    state: ChangeState
    name: Optional[str] = None
    names: List[str] = field(default_factory=list)

    @property
    def candidates(self) -> List[str]:
        return self.names

    def __iter__(self) -> Iterator[Any]:
        yield self.state
        yield self.name
        yield self.names

    def __getitem__(self, index: int | slice) -> Any:
        return (self.state, self.name, self.names)[index]


def _active_openspec_changes(cwd: Optional[str] = None) -> list[str] | None:
    try:
        listed = subprocess.run(
            ["openspec", "list", "--json"], capture_output=True, text=True, check=False,
            cwd=cwd if cwd is not None else _repo_root(),
        )
        if listed.returncode != 0:
            return None
        import json as _json

        payload = _json.loads(listed.stdout or "{}")
        changes = payload.get("changes") if isinstance(payload, dict) else payload
        if not isinstance(changes, list):
            return None
        in_progress: list[str] = []
        for entry in changes:
            if not isinstance(entry, dict):
                return None
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return None
            if entry.get("status") != "complete":
                in_progress.append(name)
        return in_progress
    except Exception:
        return None


def _repo_root() -> str:
    from pathlib import Path as _Path
    return str(_Path(__file__).resolve().parents[1])


def _validate_named_change(change: str, cwd: Optional[str] = None) -> int:
    probed = subprocess.run(
        ["openspec", "validate", change, "--type", "change", "--strict"],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd if cwd is not None else _repo_root(),
    )
    sys.stdout.write(probed.stdout)
    sys.stderr.write(probed.stderr)
    return probed.returncode


def resolve_openspec_change(
    change: str | None,
    *,
    active_resolver: Optional[Callable[[], list[str] | None]] = None,
) -> ChangeResolution:
    if change is not None:
        return ChangeResolution(state="explicit", name=change, names=[])
    resolver = active_resolver if active_resolver is not None else _active_openspec_changes
    active = resolver()
    if active is None:
        return ChangeResolution(state="lookup-failed", name=None, names=[])
    if active == []:
        return ChangeResolution(state="none", name=None, names=[])
    if len(active) == 1:
        return ChangeResolution(state="active", name=active[0], names=[])
    return ChangeResolution(state="ambiguous", name=None, names=list(active))


def validate_openspec_change(
    change: str | None,
    *,
    active_resolver: Optional[Callable[[], list[str] | None]] = None,
) -> int:
    resolution = resolve_openspec_change(change, active_resolver=active_resolver)
    if resolution.state in ("explicit", "active"):
        assert resolution.name is not None
        return _validate_named_change(resolution.name)
    if resolution.state == "none":
        return 0
    if resolution.state == "lookup-failed":
        print("ERROR: `openspec list --json` lookup failed; cannot determine active changes.", file=sys.stderr)
        print("Resolve the openspec CLI failure, then rerun.", file=sys.stderr)
        return 1
    print(f"ERROR: {len(resolution.names)} active openspec changes; pass one explicitly via --change.", file=sys.stderr)
    for entry in resolution.names:
        print(f"  - {entry}", file=sys.stderr)
    return 1


def inspect_intent_driven_change(
    change: str | None = None,
    *,
    as_json: bool = False,
    active_resolver: Optional[Callable[[], list[str] | None]] = None,
    cwd: str | None = None,
) -> int:
    resolution = resolve_openspec_change(change, active_resolver=active_resolver)
    if resolution.state in ("explicit", "active"):
        assert resolution.name is not None
        cmd = ["openspec", "status", "--change", resolution.name]
        if as_json:
            cmd.append("--json")
        probed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd if cwd is not None else _repo_root(),
        )
        sys.stdout.write(probed.stdout)
        sys.stderr.write(probed.stderr)
        return probed.returncode
    if resolution.state == "none":
        if as_json:
            import json as _json

            print(_json.dumps({"status": "none", "changes": []}))
        else:
            print("No active OpenSpec changes.")
        return 0
    if resolution.state == "lookup-failed":
        print("ERROR: `openspec list --json` lookup failed; cannot determine active changes.", file=sys.stderr)
        print("Resolve the openspec CLI failure, then rerun.", file=sys.stderr)
        return 1
    print(f"ERROR: {len(resolution.names)} active openspec changes; pass one explicitly via --change.", file=sys.stderr)
    for entry in resolution.names:
        print(f"  - {entry}", file=sys.stderr)
    return 1


# This inspector reports *repository artifact presence*, not OpenSpec CLI validity,
# applied behavior, or archival eligibility. Native OpenSpec validation is separate.
INTENT_STAGES = ("proposal", "specs", "design", "adr", "tasks")


def _intent_manifest_fields(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        return {}
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in ("schema", "skip_specs"):
            fields[key.strip()] = value.strip().strip("\"'").lower()
    return fields


def inspect_intent_chain(
    change: str, *, root: Path | None = None,
) -> dict[str, Any]:
    """Inspect the five intent artifacts without depending on a host or OpenSpec CLI."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", change) or change == "archive":
        raise ValueError("change name must be a simple kebab-case directory")
    repo = root if root is not None else Path(_repo_root())
    changes = repo / "openspec" / "changes"
    directory = changes / change
    if directory.is_symlink() or not directory.is_dir():
        raise FileNotFoundError(f"active OpenSpec change not found: {change}")

    manifest = _intent_manifest_fields(directory / ".openspec.yaml")
    schema_ok = manifest.get("schema") == "intent-driven"
    skip_specs = manifest.get("skip_specs") == "true"

    def regular_file(path: Path) -> bool:
        return path.is_file() and not path.is_symlink()

    specs = directory / "specs"
    specs_found = (
        specs.is_dir()
        and not specs.is_symlink()
        and any(
            regular_file(p) and not any(a.is_symlink() for a in p.parents if a != directory)
            for p in specs.rglob("spec.md")
        )
    )
    artifacts = {
        "proposal": regular_file(directory / "proposal.md"),
        "specs": bool(specs_found or skip_specs),
        "design": regular_file(directory / "design.md"),
        "adr": regular_file(directory / "adr.md"),
        "tasks": regular_file(directory / "tasks.md"),
    }
    missing = [stage for stage in INTENT_STAGES if not artifacts[stage]]
    if not schema_ok:
        missing.insert(0, ".openspec.yaml:schema=intent-driven")
    tasks_text = (directory / "tasks.md").read_text(encoding="utf-8") if artifacts["tasks"] else ""
    task_marks = re.findall(r"(?m)^- \[([ xX])\]\s+", tasks_text)
    task_status = (
        "untracked" if not task_marks
        else "complete" if all(mark.lower() == "x" for mark in task_marks)
        else "in-progress"
    )
    return {
        "name": change,
        "schema": manifest.get("schema"),
        "skip_specs": skip_specs,
        "artifacts": artifacts,
        "specs_exempt": skip_specs and not specs_found,
        "missing": missing,
        "next_stage": next((stage for stage in INTENT_STAGES if not artifacts[stage]), None),
        "planning_chain_ready": not missing,
        "tasks": {"total": len(task_marks), "done": sum(m.lower() == "x" for m in task_marks), "status": task_status},
        "evidence": "filesystem-only; OpenSpec CLI and execution unverified",
    }


def inspect_intent_chains(
    *, root: Path | None = None, change: str | None = None,
) -> list[dict[str, Any]]:
    repo = root if root is not None else Path(_repo_root())
    folder = repo / "openspec" / "changes"
    if not folder.is_dir():
        raise FileNotFoundError("openspec/changes directory missing")
    if change is not None:
        return [inspect_intent_chain(change, root=repo)]
    return [
        inspect_intent_chain(p.name, root=repo)
        for p in sorted(folder.iterdir())
        if p.is_dir() and not p.is_symlink() and p.name not in ("archive", ".archive")
    ]


def print_intent_artifacts(
    *, root: Path | None = None, change: str | None = None, as_json: bool = False,
) -> int:
    try:
        changes = inspect_intent_chains(root=root, change=change)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    payload = {
        "schema": "intent-driven",
        "stage_order": list(INTENT_STAGES),
        "inspection_level": "filesystem-only; not OpenSpec validation",
        "summary": {
            "total": len(changes),
            "planning_ready": sum(bool(x["planning_chain_ready"]) for x in changes),
            "incomplete": sum(not x["planning_chain_ready"] for x in changes),
        },
        "changes": changes,
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for entry in changes:
            label = "ARTIFACTS_PRESENT" if entry["planning_chain_ready"] else "INCOMPLETE"
            missing = ", ".join(entry["missing"]) if entry["missing"] else "none"
            print(f'{entry["name"]}: {label}; missing: {missing}; tasks: {entry["tasks"]["status"]}')
        print("NOTE: filesystem inspection only; run OpenSpec CLI validation separately.")
    return 0


def verify_all_intent_changes(
    *, root: Path | None = None, change: str | None = None,
) -> int:
    """Strict verification, deliberately BLOCKED if CLI or artifact chain is missing."""
    repo = root if root is not None else Path(_repo_root())
    try:
        changes = inspect_intent_chains(root=repo, change=change)
    except (ValueError, FileNotFoundError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    unready = [x for x in changes if not x["planning_chain_ready"]]
    if unready:
        for entry in unready:
            print(f'BLOCKED: {entry["name"]}: missing {", ".join(entry["missing"])}', file=sys.stderr)
        return 2
    try:
        commands = [["openspec", "schema", "validate", "intent-driven"]]
        commands.extend(
            ["openspec", "validate", x["name"], "--type", "change", "--strict"]
            for x in changes
        )
        for command in commands:
            result = subprocess.run(
                command, cwd=str(repo), capture_output=True, text=True, check=False,
            )
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
            if result.returncode != 0:
                print(f"FAIL: OpenSpec command exited {result.returncode}: {' '.join(command)}", file=sys.stderr)
                return 1
    except OSError as exc:
        print(f"BLOCKED: OpenSpec CLI unavailable: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: schema and {len(changes)} active change(s) strictly validated with OpenSpec CLI.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and (args[0] == "verify-all" or "--artifacts" in args):
        strict = args[0] == "verify-all"
        parser = argparse.ArgumentParser(
            prog="openspec_change.py verify-all" if strict else "openspec_change.py --artifacts"
        )
        parser.add_argument("--change", metavar="NAME")
        if not strict:
            parser.add_argument("--artifacts", action="store_true")
            parser.add_argument("--json", action="store_true")
        try:
            selected = parser.parse_args(args[1:] if strict else args)
        except SystemExit as exc:
            return int(exc.code)
        if strict:
            return verify_all_intent_changes(change=selected.change)
        return print_intent_artifacts(change=selected.change, as_json=selected.json)
    if any(arg in ("-h", "--help") for arg in args):
        print("Usage: python3 scripts/openspec_change.py [--status] [--json] [--change CHANGE] [CHANGE] | --artifacts [--json] [--change NAME] | verify-all [--change NAME]", file=sys.stdout)
        return 0
    status_mode = "--status" in args
    if status_mode:
        args.remove("--status")
    as_json = "--json" in args
    if as_json:
        args.remove("--json")

    change: str | None = None
    if "--change" in args:
        idx = args.index("--change")
        if idx + 1 < len(args):
            change = args[idx + 1]
            del args[idx : idx + 2]
        else:
            args.remove("--change")
    elif args and args[0] == "validate":
        args.pop(0)
        if args:
            change = args.pop(0)
    elif args:
        change = args.pop(0)

    if status_mode or as_json:
        return inspect_intent_driven_change(change, as_json=as_json)
    return validate_openspec_change(change)


if __name__ == "__main__":
    sys.exit(main())

