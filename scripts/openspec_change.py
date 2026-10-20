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


def _active_openspec_changes() -> list[str] | None:
    try:
        listed = subprocess.run(
            ["openspec", "list", "--json"], capture_output=True, text=True, check=False
        )
        if listed.returncode != 0:
            return None
        import json as _json

        payload = _json.loads(listed.stdout or "{}")
        changes = payload.get("changes") if isinstance(payload, dict) else payload
        if not isinstance(changes, list):
            return None
        parsed: list[str] = []
        in_progress: list[str] = []
        for entry in changes:
            if not isinstance(entry, dict):
                return None
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return None
            parsed.append(name)
            if entry.get("status") != "complete":
                in_progress.append(name)
        return in_progress if in_progress else parsed
    except Exception:
        return None


def _validate_named_change(change: str) -> int:
    probed = subprocess.run(
        ["openspec", "validate", change, "--type", "change", "--strict"],
        capture_output=True,
        text=True,
        check=False,
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
