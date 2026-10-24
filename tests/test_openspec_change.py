#!/usr/bin/env python3
"""Tests for OpenSpec change resolution and schema validation (#761, #762).

Decomposed from test_verify_portable.py to isolate OpenSpec domain logic
and prevent test suite sprawl past 1k lines.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.openspec_change as oc
from scripts.openspec_change import (
    ChangeResolution,
    _active_openspec_changes,
    resolve_openspec_change,
    validate_openspec_change,
)


def test_validate_default_change_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["only-active"])
    seen: dict[str, list[str]] = {}

    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert validate_openspec_change(None) == 0
    assert seen.get("argv", [])[2] == "only-active"

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: [])
    assert validate_openspec_change(None) == 0

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: None)
    assert validate_openspec_change(None) == 1

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
    assert validate_openspec_change(None) == 1


def test_validate_explicit_default_name_validates_that_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "pstack-portability-contract"
    seen: dict[str, list[str]] = {}

    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert validate_openspec_change(name) == 0
    assert seen.get("argv", [])[2] == name


def test_resolution_states_are_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: None)
    assert resolve_openspec_change(None)[0] == "lookup-failed"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: [])
    assert resolve_openspec_change(None)[0] == "none"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["one"])
    assert resolve_openspec_change(None)[:2] == ("active", "one")
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
    state, name, names = resolve_openspec_change(None)
    assert (state, name, names) == ("ambiguous", None, ["a", "b"])
    assert resolve_openspec_change("explicit-name")[:2] == ("explicit", "explicit-name")


@pytest.mark.parametrize(
    "stdout",
    [
        '{"changes": ["junk"]}',
        '{"changes": [{}]}',
        '{"changes": [{"name": ""}]}',
        '{"changes": [{"name": 42}]}',
        '{"changes": "junk"}',
        "not json",
    ],
)
def test_active_changes_malformed_payload_is_lookup_failure(
    monkeypatch: pytest.MonkeyPatch, stdout: str
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout, ""),
    )
    assert _active_openspec_changes() is None
    assert validate_openspec_change(None) == 1


def test_active_changes_lookup_failure_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    def _rc1(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(a, 1, "", "boom")

    monkeypatch.setattr(subprocess, "run", _rc1)
    assert _active_openspec_changes() is None
    assert validate_openspec_change(None) == 1

    def _missing(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("no openspec binary")

    monkeypatch.setattr(subprocess, "run", _missing)
    assert _active_openspec_changes() is None
    assert validate_openspec_change(None) == 1


def test_active_changes_empty_list_parses_to_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps({"changes": [], "root": {}}), ""),
    )
    assert _active_openspec_changes() == []
    assert validate_openspec_change(None) == 0


def test_active_changes_all_complete_parses_to_none_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    completed_payload = {
        "changes": [
            {"name": "change-1", "status": "complete", "completedTasks": 5, "totalTasks": 5},
            {"name": "change-2", "status": "complete", "completedTasks": 3, "totalTasks": 3},
        ],
        "root": {},
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps(completed_payload), ""),
    )
    assert _active_openspec_changes() == []
    resolution = resolve_openspec_change(None)
    assert resolution.state == "none"
    assert resolution.name is None
    assert resolution.names == []
    assert validate_openspec_change(None) == 0


def test_active_changes_filters_out_completed_when_in_progress_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mixed_payload = {
        "changes": [
            {"name": "change-complete", "status": "complete"},
            {"name": "change-active", "status": "in-progress"},
        ],
        "root": {},
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps(mixed_payload), ""),
    )
    assert _active_openspec_changes() == ["change-active"]
    resolution = resolve_openspec_change(None)
    assert resolution.state == "active"
    assert resolution.name == "change-active"
    assert resolution.names == []


def test_change_resolution_frozen_dataclass_and_semantics() -> None:
    """ChangeResolution is a frozen dataclass with Literal states and tuple compatibility (#615)."""
    assert is_dataclass(ChangeResolution)

    res = resolve_openspec_change("explicit-change")
    assert isinstance(res, ChangeResolution)
    assert res.state == "explicit"
    assert res.name == "explicit-change"
    assert res.names == []
    assert res.candidates == []

    # Frozen immutability check
    with pytest.raises(FrozenInstanceError):
        res.state = "none"  # type: ignore[misc]

    # Tuple unpacking and indexing backwards compatibility
    state, name, names = res
    assert (state, name, names) == ("explicit", "explicit-change", [])
    assert res[0] == "explicit"
    assert res[1] == "explicit-change"
    assert res[:2] == ("explicit", "explicit-change")

    # Ambiguous resolution
    ambig = ChangeResolution(state="ambiguous", name=None, names=["ch1", "ch2"])
    assert ambig.state == "ambiguous"
    assert ambig.name is None
    assert ambig.candidates == ["ch1", "ch2"]
    assert ambig[2] == ["ch1", "ch2"]
