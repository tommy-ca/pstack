"""Executable tests proving matcher truth values and Test Behavior principle correctness (#204)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

ROOT = Path(__file__).resolve().parents[1]
PRINCIPLE_FILE = ROOT / "skills" / "principle-test-behavior-not-implementation" / "SKILL.md"


def test_principle_documents_canonical_exception_474() -> None:
    text = PRINCIPLE_FILE.read_text(encoding="utf-8")
    assert "cursor/plugins #474" in text
    assert "Weak assertions that fail on `undefined`" in text
    assert "Non-discriminating checks" in text


def test_weak_matchers_do_fail_on_undefined_or_none() -> None:
    """Prove that toBeDefined and toBeTruthy do NOT pass when a stub returns undefined/None.

    This proves that claiming these matchers 'still pass when every imported function returns undefined'
    is factually false (cursor/plugins #474).
    """
    def stub() -> None:
        return None

    res = stub()

    # In Python equivalent of toBeTruthy:
    with pytest.raises(AssertionError):
        assert bool(res) is True, "Expected truthy but got None/undefined"

    # In Python equivalent of toBeDefined:
    with pytest.raises(AssertionError):
        assert res is not None, "Expected defined but got None/undefined"


def test_vacuous_assertion_passes_without_observing_behavior() -> None:
    """Prove truly vacuous assertion shapes that pass despite missing behavior."""
    def stub() -> None:
        return None

    # Shape 1: No assertion - execution only passes
    stub()

    # Shape 2: Absence check alone passes on missing behavior
    mock = MagicMock()
    # No interaction with mock
    mock.assert_not_called()

    # Shape 3: Self-referential assertion passes trivially
    val = stub()
    assert val == val
