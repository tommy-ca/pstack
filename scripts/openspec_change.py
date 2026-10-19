"""OpenSpec change resolution and validation (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any, Callable, List, Optional, Tuple

ChangeResolution = Tuple[str, Optional[str], List[str]]


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
        for entry in changes:
            if not isinstance(entry, dict):
                return None
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return None
            parsed.append(name)
        return parsed
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
    active_resolver: Callable[[], list[str] | None] = _active_openspec_changes,
) -> ChangeResolution:
    if change is not None:
        return "explicit", change, []
    active = active_resolver()
    if active is None:
        return "lookup-failed", None, []
    if active == []:
        return "none", None, []
    if len(active) == 1:
        return "active", active[0], []
    return "ambiguous", None, active


def validate_openspec_change(
    change: str | None,
    *,
    active_resolver: Callable[[], list[str] | None] = _active_openspec_changes,
) -> int:
    state, name, names = resolve_openspec_change(change, active_resolver=active_resolver)
    if state in ("explicit", "active"):
        assert name is not None
        return _validate_named_change(name)
    if state == "none":
        return 0
    if state == "lookup-failed":
        print("ERROR: `openspec list --json` lookup failed; cannot determine active changes.", file=sys.stderr)
        print("Resolve the openspec CLI failure, then rerun.", file=sys.stderr)
        return 1
    print(f"ERROR: {len(names)} active openspec changes; pass one explicitly via --change.", file=sys.stderr)
    for entry in names:
        print(f"  - {entry}", file=sys.stderr)
    return 1
