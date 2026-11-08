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
    inspect_intent_driven_change,
    main,
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


def test_intent_driven_status_active_and_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, list[str]] = {}

    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "status ok", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["active-unit"])

    assert inspect_intent_driven_change() == 0
    assert seen.get("argv", []) == ["openspec", "status", "--change", "active-unit"]

    assert inspect_intent_driven_change("explicit-unit", as_json=True) == 0
    assert seen.get("argv", []) == [
        "openspec",
        "status",
        "--change",
        "explicit-unit",
        "--json",
    ]


def test_intent_driven_status_none_branches(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: [])

    assert inspect_intent_driven_change(as_json=False) == 0
    captured = capsys.readouterr()
    assert "No active OpenSpec changes." in captured.out

    assert inspect_intent_driven_change(as_json=True) == 0
    captured_json = capsys.readouterr()
    parsed = json.loads(captured_json.out)
    assert parsed["status"] == "none"
    assert parsed["changes"] == []


def test_intent_driven_status_error_branches(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: None)
    assert inspect_intent_driven_change() == 1
    err = capsys.readouterr().err
    assert "lookup failed" in err

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["c1", "c2"])
    assert inspect_intent_driven_change() == 1
    err2 = capsys.readouterr().err
    assert "2 active openspec changes" in err2


def test_intent_driven_status_main_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: dict[str, list[str]] = {}

    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "{}", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["active-flow"])

    assert main(["--status"]) == 0
    assert seen.get("argv", []) == ["openspec", "status", "--change", "active-flow"]

    assert main(["--status", "--json"]) == 0
    assert seen.get("argv", []) == [
        "openspec",
        "status",
        "--change",
        "active-flow",
        "--json",
    ]

    assert main(["--status", "named-flow"]) == 0
    assert seen.get("argv", []) == ["openspec", "status", "--change", "named-flow"]

    assert main(["--status", "--change", "explicit-flow", "--json"]) == 0
    assert seen.get("argv", []) == [
        "openspec",
        "status",
        "--change",
        "explicit-flow",
        "--json",
    ]

    assert main(["--help"]) == 0
    captured = capsys.readouterr()
    assert "Usage" in captured.out



def _make_intent_change(root: Path, name: str, *, skip_specs: bool = False) -> Path:
    directory = root / "openspec" / "changes" / name
    directory.mkdir(parents=True)
    (directory / ".openspec.yaml").write_text(
        "schema: intent-driven\n" + ("skip_specs: true\n" if skip_specs else ""),
        encoding="utf-8",
    )
    for artifact in ("proposal.md", "design.md", "adr.md", "tasks.md"):
        (directory / artifact).write_text("# " + artifact + "\n", encoding="utf-8")
    if not skip_specs:
        spec = directory / "specs" / "capability" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("## ADDED Requirements\n", encoding="utf-8")
    (directory / "tasks.md").write_text("- [ ] 1.1 Implement\n", encoding="utf-8")
    return directory


def test_intent_status_is_filesystem_only_and_preserves_task_progress(tmp_path: Path) -> None:
    from scripts.openspec_change import inspect_intent_chain

    directory = _make_intent_change(tmp_path, "2026-11-08-change")
    entry = inspect_intent_chain(directory.name, root=tmp_path)
    assert entry["planning_chain_ready"]
    assert entry["tasks"] == {"total": 1, "done": 0, "status": "in-progress"}
    assert entry["evidence"].startswith("filesystem-only")
    assert entry["next_stage"] is None

    (directory / "adr.md").unlink()
    incomplete = inspect_intent_chain(directory.name, root=tmp_path)
    assert incomplete["missing"] == ["adr"]
    assert incomplete["next_stage"] == "adr"
    assert not incomplete["planning_chain_ready"]


def test_intent_status_docs_only_exception_and_invalid_names(tmp_path: Path) -> None:
    from scripts.openspec_change import inspect_intent_chain

    directory = _make_intent_change(tmp_path, "docs-only", skip_specs=True)
    status = inspect_intent_chain("docs-only", root=tmp_path)
    assert status["specs_exempt"] and status["planning_chain_ready"]
    (directory / ".openspec.yaml").write_text("schema: other\n", encoding="utf-8")
    wrong_schema = inspect_intent_chain("docs-only", root=tmp_path)
    assert ".openspec.yaml:schema=intent-driven" in wrong_schema["missing"]
    assert "specs" in wrong_schema["missing"]
    with pytest.raises(ValueError):
        inspect_intent_chain("../outside", root=tmp_path)
    with pytest.raises(FileNotFoundError):
        inspect_intent_chain("not-found", root=tmp_path)


def test_intent_status_rejects_symlink_artifacts(tmp_path: Path) -> None:
    from scripts.openspec_change import inspect_intent_chain

    first = _make_intent_change(tmp_path, "candidate")
    second = _make_intent_change(tmp_path, "other")
    (first / "adr.md").unlink()
    (first / "adr.md").symlink_to(second / "adr.md")
    entry = inspect_intent_chain("candidate", root=tmp_path)
    assert "adr" in entry["missing"]


def test_intent_status_json_lists_active_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.openspec_change import print_intent_artifacts

    _make_intent_change(tmp_path, "alpha")
    _make_intent_change(tmp_path, "beta")
    (tmp_path / "openspec" / "changes" / "archive").mkdir()
    assert print_intent_artifacts(root=tmp_path, as_json=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stage_order"] == ["proposal", "specs", "design", "adr", "tasks"]
    assert [c["name"] for c in payload["changes"]] == ["alpha", "beta"]
    assert payload["summary"]["planning_ready"] == 2
    assert payload["inspection_level"].startswith("filesystem-only")


def test_intent_verify_requires_real_cli_and_all_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.openspec_change import verify_all_intent_changes

    directory = _make_intent_change(tmp_path, "demo")
    (directory / "design.md").unlink()
    assert verify_all_intent_changes(root=tmp_path) == 2
    assert "missing design" in capsys.readouterr().err
    (directory / "design.md").write_text("# Design\n", encoding="utf-8")

    def unavailable(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("openspec not installed")

    monkeypatch.setattr(subprocess, "run", unavailable)
    assert verify_all_intent_changes(root=tmp_path) == 2
    assert "CLI unavailable" in capsys.readouterr().err


def test_intent_verify_calls_schema_then_strict_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.openspec_change import verify_all_intent_changes

    _make_intent_change(tmp_path, "beta")
    _make_intent_change(tmp_path, "alpha")
    seen: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert verify_all_intent_changes(root=tmp_path) == 0
    assert seen == [
        ["openspec", "schema", "validate", "intent-driven"],
        ["openspec", "validate", "alpha", "--type", "change", "--strict"],
        ["openspec", "validate", "beta", "--type", "change", "--strict"],
    ]
    assert "PASS: schema and 2 active" in capsys.readouterr().out


def test_intent_status_cli_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    invoked: dict[str, object] = {}
    monkeypatch.setattr(oc, "print_intent_artifacts", lambda **kw: invoked.update(kw) or 0)
    assert oc.main(["--artifacts", "--json", "--change", "example"]) == 0
    assert invoked == {"change": "example", "as_json": True}
    monkeypatch.setattr(oc, "verify_all_intent_changes", lambda **kw: 2)
    assert oc.main(["verify-all", "--change", "example"]) == 2
