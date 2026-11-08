"""OpenSpec change resolution and validation (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import subprocess
import sys
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


def validate_all_openspec_specs(cwd: str | None = None) -> int:
    probed = subprocess.run(
        ["openspec", "validate", "--all"],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd if cwd is not None else _repo_root(),
    )
    sys.stdout.write(probed.stdout)
    sys.stderr.write(probed.stderr)
    return probed.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("-h", "--help") for arg in args):
        print("Usage: python3 scripts/openspec_change.py [--status] [--json] [--all] [--change CHANGE] [CHANGE]", file=sys.stdout)
        return 0
    if "--all" in args:
        args.remove("--all")
        return validate_all_openspec_specs()
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

