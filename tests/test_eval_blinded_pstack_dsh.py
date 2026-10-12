#!/usr/bin/env python3
"""Frozen baseline corpus tests for the DSH E01-E07 / N01-N07 archetypes (#310).

The corpus is a *measurement*, not a gate on the candidate: a positive case whose
required evidence is not yet present in pstack is recorded UNTESTED (a baseline
gap), never FAIL and never a false PASS. Negatives must never activate, and every
probe's injected control must separate from the real input, so a green negative
is shown to be non-vacuous rather than tautological.

**Revision bound.** These cases were frozen and measured at pstack revision
`52333df` - the revision recorded in `scoring_table.json`, which is not reachable from
`main` because the branch was re-based on merge. A re-measurement at that revision is
therefore impossible, and the tree has moved since (P13 landed the consumer-reachability
contract E05 probes). The runner handles that mechanically: `phase="baseline"` reports the
frozen record and names every case the evaluated tree no longer reproduces in the case's
`drift` notes and in `result.provenance["drift_cases"]`, so staleness is reported as drift
rather than as a failed baseline. This module stays the historical record check, not the
live gate - the live measurement is `tests/test_eval_blinded_pstack_dsh_candidate.py`,
which re-runs the same frozen cases with the re-derived controls and records them in
`scoring_table_candidate.json`. The frozen JSON is never edited by either phase.
"""

import sys
from dataclasses import asdict
import json
from pathlib import Path
import shutil

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

    def test_a_moved_tree_is_reported_as_drift_not_as_a_failed_baseline(self, result) -> None:
        provenance = result.provenance
        assert provenance["drifted"] == (
            provenance["frozen_record"]["pinned_revision"] != provenance["evaluated_revision"]
        )
        # The record is reported as measured, so its own revision is what the run names.
        assert result.pstack_revision == provenance["frozen_record"]["pinned_revision"]
        assert provenance["drifted"] is True, "main has moved past the pinned baseline revision"

    def test_the_drifted_case_names_its_divergence(self, result) -> None:
        recorded = json.loads(
            (DSH_CORPUS_DIR / "scoring_table.json").read_text(encoding="utf-8")
        )
        by_id = {case["id"]: case for case in recorded["cases"]}
        drifted = {case.id: case for case in result.cases if case.drift}
        assert set(drifted) == set(result.provenance["drift_cases"])
        for case_id, case in drifted.items():
            assert case.status == by_id[case_id]["status"], case_id
            assert case.status != "FAIL", (case_id, case.drift)
            assert case_id in case.drift[0]

    def test_a_record_that_does_not_reproduce_at_its_own_revision_fails(self, result, tmp_path) -> None:
        corpus_dir = tmp_path / "eval_corpus_dsh"
        corpus_dir.mkdir()
        for name in ("cases.json", "scoring_table.json"):
            shutil.copyfile(DSH_CORPUS_DIR / name, corpus_dir / name)
        table_path = corpus_dir / "scoring_table.json"
        record = json.loads(table_path.read_text(encoding="utf-8"))
        # Same revision as the evaluated tree: any disagreement is a defect, not drift.
        record["pstack_revision"] = result.provenance["evaluated_revision"]
        for drift_id in ("E05", "E04"):
            case = next(case for case in record["cases"] if case["id"] == drift_id)
            case["status"] = "PASS"
        table_path.write_text(json.dumps(record), encoding="utf-8")
        rerun = run_dsh_blinded_eval(corpus_dir, ROOT)
        assert rerun.provenance["drifted"] is False
        assert rerun.provenance["drift_cases"] == ["E05", "E04"]
        assert rerun.verdict == "FAIL"
