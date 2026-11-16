from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.agnix_guard as guard


def test_reviewed_policy_and_mise_pin() -> None:
    errors = guard.policy_errors(guard.ROOT)
    assert errors == []


def test_missing_or_malformed_receipts_never_pass() -> None:
    assert guard.receipt_errors("non-dict", 0) != []
    assert guard.receipt_errors(None, 0) != []

    missing_parts = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
    }
    assert guard.receipt_errors(missing_parts, 0) != []

    invalid_summary = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": -1, "warnings": 0, "info": 0},
        "diagnostics": [],
    }
    assert guard.receipt_errors(invalid_summary, 0) != []

    non_object_diagnostics = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 0, "info": 0},
        "diagnostics": ["not-a-dict"],
    }
    assert guard.receipt_errors(non_object_diagnostics, 0) != []


def test_bad_version_and_vacuous_coverage_rejected() -> None:
    wrong_version = {
        "version": "0.59.0",
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 0, "info": 0},
        "diagnostics": [],
    }
    errors = guard.receipt_errors(wrong_version, 0)
    assert any("version" in e for e in errors)

    under_min_files = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES - 1,
        "summary": {"errors": 0, "warnings": 0, "info": 0},
        "diagnostics": [],
    }
    errors = guard.receipt_errors(under_min_files, 0)
    assert any(f"fewer than {guard.MIN_FILES}" in e for e in errors)


def test_inconsistent_summary_and_diagnostics_rejected() -> None:
    contradictory_zero_summary = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 0, "info": 0},
        "diagnostics": [{"level": "warning", "rule": "AS-001"}],
    }
    errors = guard.receipt_errors(contradictory_zero_summary, 0)
    assert any("does not match diagnostics count" in e for e in errors)

    contradictory_missing_detail = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 2, "info": 0},
        "diagnostics": [{"level": "warning", "rule": "AS-001"}],
    }
    errors = guard.receipt_errors(contradictory_missing_detail, 0)
    assert any("does not match diagnostics count" in e for e in errors)


def test_error_and_failing_exit_are_rejected() -> None:
    error_receipt = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 1, "warnings": 0, "info": 0},
        "diagnostics": [{"level": "error", "rule": "AGY-001"}],
    }
    assert guard.receipt_errors(error_receipt, 0) != []

    clean_receipt = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 0, "info": 0},
        "diagnostics": [],
    }
    assert guard.receipt_errors(clean_receipt, 1) != []


def test_warnings_are_visible_but_not_yet_zero_budgeted() -> None:
    warning_receipt = {
        "version": guard.VERSION,
        "files_checked": guard.MIN_FILES,
        "summary": {"errors": 0, "warnings": 20, "info": 0},
        "diagnostics": [{"level": "warning", "rule": "AS-002"}] * 20,
    }
    assert guard.receipt_errors(warning_receipt, 0, warning_budget=31) == []
    assert guard.receipt_errors(warning_receipt, 0, warning_budget=10) != []


def test_bounded_real_code_verdict_and_failing_mutant() -> None:
    states, failures = guard.bounded_model()
    assert states == 288
    assert failures == []


def test_policy_rejects_blanket_exclusion_and_disabled_rules(tmp_path: pathlib.Path) -> None:
    agnix_toml = tmp_path / ".agnix.toml"
    mise_toml = tmp_path / "mise.toml"

    valid_agnix = (guard.ROOT / ".agnix.toml").read_text(encoding="utf-8")
    valid_mise = (guard.ROOT / "mise.toml").read_text(encoding="utf-8")

    agnix_toml.write_text(valid_agnix.replace('severity = "Warning"', 'severity = "Info"'), encoding="utf-8")
    mise_toml.write_text(valid_mise, encoding="utf-8")
    assert any("severity" in e for e in guard.policy_errors(tmp_path))

    agnix_toml.write_text(valid_agnix.replace('disabled_rules = []', 'disabled_rules = ["AS-001"]'), encoding="utf-8")
    assert any("disabled_rules" in e for e in guard.policy_errors(tmp_path))

    agnix_toml.write_text(valid_agnix + "\n[overrides]\nfoo = 'bar'\n", encoding="utf-8")
    assert any("overrides" in e for e in guard.policy_errors(tmp_path))


def test_binary_never_falls_back_to_node_modules() -> None:
    fake_node_modules = pathlib.Path("/tmp/node_modules/agnix")
    assert guard.resolve_binary(fake_node_modules) is None
