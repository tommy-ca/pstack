#!/usr/bin/env python3
"""Frozen baseline corpus tests for the DSH E01-E07 / N01-N07 archetypes (#310).

The corpus is a *measurement*, not a gate on the candidate: a positive case whose
required evidence is not yet present in pstack is recorded UNTESTED (a baseline
gap), never FAIL and never a false PASS. Negatives must never activate, and every
probe's injected control must separate from the real input, so a green negative
is shown to be non-vacuous rather than tautological.
"""

import sys
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_blinded_pstack import (
    DSH_CORPUS_DIR,
    run_dsh_blinded_eval,
)


@pytest.fixture(scope="module")
def result():
    return run_dsh_blinded_eval(DSH_CORPUS_DIR, ROOT)


class TestDshBaselineCorpus:
    def test_corpus_shape(self, result) -> None:
        assert result.corpus_version == "1.0.0-dsh-baseline"
        assert result.phase == "baseline"
        assert result.model_route is None
        assert result.provider == "deterministic-offline"
        assert result.total_cases == 14
        assert result.positives == 7
        assert result.negatives == 7
        assert {c.id for c in result.cases} == {
            *(f"E0{i}" for i in range(1, 8)),
            *(f"N0{i}" for i in range(1, 8)),
        }

    def test_run_is_deterministic(self, result) -> None:
        def stable(payload: dict) -> dict:
            # Wall clock is measured, not deterministic; every counter must be.
            payload.pop("total_context_ms", None)
            for case in payload["cases"]:
                case.pop("context_ms", None)
            return payload

        again = run_dsh_blinded_eval(DSH_CORPUS_DIR, ROOT)
        assert stable(asdict(again)) == stable(asdict(result))

    def test_negative_controls_do_not_trigger(self, result) -> None:
        assert result.false_activations == 0
        assert result.unsafe_effects == 0
        for case in result.cases:
            if case.kind == "negative":
                assert case.status == "PASS", case.id
                assert case.forbidden_activated == []

    def test_every_control_is_sensitive(self, result) -> None:
        assert result.controls_total > 0
        assert result.controls_sensitive == result.controls_total
        for case in result.cases:
            assert case.insensitive_controls == [], case.id

    def test_no_false_pass(self, result) -> None:
        for case in result.cases:
            if case.status == "PASS":
                assert case.missed_required == []
                assert case.forbidden_activated == []
        assert result.false_passes == 0

    def test_baseline_gaps_are_untested_not_failed(self, result) -> None:
        untested = [c for c in result.cases if c.status == "UNTESTED"]
        assert all(c.kind == "positive" for c in untested)
        assert all(c.missed_required for c in untested)
        assert len(untested) == result.missed_required
        assert result.verdict in ("PASS", "UNTESTED")

    def test_context_work_is_recorded_within_budget(self, result) -> None:
        cap = result.budgets["max_context_ops_per_case"]
        assert result.total_context_ops > 0
        assert result.total_context_bytes > 0
        for case in result.cases:
            assert case.context_ops > 0, case.id
            assert case.context_ops <= cap, case.id

    def test_labels_are_blinded(self, result) -> None:
        labels = [c.blind_label for c in result.cases]
        assert len(set(labels)) == len(labels)
        for case in result.cases:
            assert case.blind_label.startswith("candidate-")
            assert case.id.lower() not in case.blind_label.lower()
