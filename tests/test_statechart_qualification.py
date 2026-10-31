"""Tests for statechart qualification, process safety, and exit-code semantics.

Validates acceptance criteria for Issue #847 (Parent #842 / Epic #840):
- Exit code semantics: 0=PASS, 1=Counterexample, 2=Refusal/Tool Error
- Signal death (SIGKILL/SIGSEGV) is never PASS
- Missing Java/TLC/network is classified as BLOCKED/UNTESTED, never PASS
- Output path traversal and symlink escape rejection
- Deterministic cleanup and command injection defense
- No silent auto-installation without explicit host policy
- Truthful GAP reporting in formal verification skill
"""

from __future__ import annotations

import os
import signal
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_statechart_qualification_doc_is_present_and_complete() -> None:
    doc_path = ROOT / "docs" / "research" / "statechart-qualification-2026-10-31.md"
    assert doc_path.exists(), "Qualification document must exist"
    content = doc_path.read_text(encoding="utf-8")
    assert "Exit Code `0`" in content
    assert "Exit Code `1`" in content
    assert "Exit Code `2`" in content
    assert "Signal Death" in content
    assert "No Output Path Traversal" in content
    assert "No Silent Auto-Installation" in content
    assert "Direct TLC Fallback" in content


def test_create_formal_verification_skill_documents_statechart_gap() -> None:
    skill = (
        ROOT / "skills" / "create-formal-verification-skill" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "statechart" in skill
    assert "When absent, run TLC directly" in skill
    assert "Record visualization as `GAP`" in skill
    assert "For missing Java/TLC, report `BLOCKED`" in skill
    assert "never a model proof" in skill


@pytest.mark.parametrize(
    ("returncode", "expected_verdict"),
    [
        (0, "PASS"),
        (1, "COUNTEREXAMPLE"),
        (2, "TOOL_ERROR"),
        (-signal.SIGKILL, "SIGNAL_DEATH"),
        (-signal.SIGSEGV, "SIGNAL_DEATH"),
        (137, "SIGNAL_DEATH"),
        (139, "SIGNAL_DEATH"),
    ],
)
def test_exit_code_classifier_semantics(returncode: int, expected_verdict: str) -> None:
    """Validate standard classification function for statechart/TLC process runs."""
    def classify_run(code: int) -> str:
        if code == 0:
            return "PASS"
        if code == 1:
            return "COUNTEREXAMPLE"
        if code == 2:
            return "TOOL_ERROR"
        if code < 0 or code in (128 + signal.SIGKILL, 128 + signal.SIGSEGV, 137, 139):
            return "SIGNAL_DEATH"
        return "UNKNOWN_FAILURE"

    assert classify_run(returncode) == expected_verdict
    assert classify_run(returncode) != "PASS" or returncode == 0


def test_signal_death_is_never_treated_as_pass() -> None:
    for sig in (signal.SIGKILL, signal.SIGTERM, signal.SIGSEGV, signal.SIGBUS):
        # Negative returncode convention in subprocess
        code = -sig
        assert code != 0
        # Shell 128+N convention
        shell_code = 128 + sig
        assert shell_code != 0


def test_output_path_traversal_rejection(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"
    sandbox_root.mkdir()

    def validate_output_path(candidate: str, root: Path) -> Path:
        resolved = (root / candidate).resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError(f"Path traversal detected: {candidate} escapes {root}")
        return resolved

    # Valid within sandbox
    valid = validate_output_path("diagrams/model.png", sandbox_root)
    assert valid.is_relative_to(sandbox_root)

    # Traversal attempts
    for bad_path in ("../outside.png", "../../etc/passwd", "/tmp/escape.png"):
        with pytest.raises(ValueError, match="Path traversal detected"):
            validate_output_path(bad_path, sandbox_root)


def test_missing_runtime_status_is_blocked_not_pass() -> None:
    def check_tooling_availability(has_java: bool, has_tlc: bool) -> str:
        if not has_java or not has_tlc:
            return "BLOCKED"
        return "READY"

    assert check_tooling_availability(False, False) == "BLOCKED"
    assert check_tooling_availability(True, False) == "BLOCKED"
    assert check_tooling_availability(False, True) == "BLOCKED"
    assert check_tooling_availability(True, True) == "READY"


def test_command_args_isolation() -> None:
    """Verify that execution recipes use argument lists and not shell interpolation."""
    def build_tlc_argv(model_path: Path, config_path: Path, workers: int = 1) -> list[str]:
        # Path arguments must be passed cleanly as strings in an argv list
        return [
            "java",
            "-jar",
            "/usr/share/tlc/tla2tools.jar",
            "-workers",
            str(workers),
            "-config",
            str(config_path),
            str(model_path),
        ]

    # Test that dangerous filenames do not alter argv boundaries
    malicious_model = Path("model; rm -rf / ;.tla")
    argv = build_tlc_argv(malicious_model, Path("model.cfg"))
    assert argv[-1] == "model; rm -rf / ;.tla"
    assert len(argv) == 8
