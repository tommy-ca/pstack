#!/usr/bin/env python3
"""Candidate-phase corpus tests for the DSH E01-E07 / N01-N07 archetypes (#310).

`cases.json` and `scoring_table.json` are the frozen baseline record and stay byte-identical;
this suite asserts the *candidate* phase re-runs those same cases against the current tree
with the controls re-derived in `candidate_phase.json`. A positive archetype whose required
evidence is still absent is recorded UNTESTED - a named gap, never FAIL and never a false
PASS - and every control must separate on the candidate text, which is how a green candidate
is shown to be non-vacuous instead of merely unmatched.
"""

import hashlib
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_blinded_pstack import (
    CANDIDATE_PHASE_FILE,
    DSH_CORPUS_DIR,
    run_dsh_blinded_eval,
)

BASELINE_CORPUS = DSH_CORPUS_DIR / "cases.json"
BASELINE_TABLE = DSH_CORPUS_DIR / "scoring_table.json"
CANDIDATE_TABLE = DSH_CORPUS_DIR / "scoring_table_candidate.json"
FROZEN_CORPUS_SHA256 = "90285f0f28e9337c56380fbe932a2fa1796b212d9c43f5397ad0ce273a38ed45"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def result():
    return run_dsh_blinded_eval(DSH_CORPUS_DIR, ROOT, phase="candidate")


@pytest.fixture(scope="module")
def recorded() -> dict:
    return json.loads(CANDIDATE_TABLE.read_text(encoding="utf-8"))


def _corpus_copy(tmp_path: Path) -> Path:
    target = tmp_path / "eval_corpus_dsh"
    target.mkdir()
    for name in ("cases.json", "scoring_table.json", CANDIDATE_PHASE_FILE):
        shutil.copyfile(DSH_CORPUS_DIR / name, target / name)
    return target


class TestDshCandidatePhase:
    def test_corpus_shape(self, result) -> None:
        assert result.corpus_version == "1.0.0-dsh-candidate"
        assert result.phase == "candidate"
        assert result.model_route is None  # no model route is invoked offline
        assert result.provider == "deterministic-offline"
        assert result.total_cases == 14
        assert result.positives == 7
        assert result.negatives == 7
        assert {c.id for c in result.cases} == {
            *(f"E0{i}" for i in range(1, 8)),
            *(f"N0{i}" for i in range(1, 8)),
        }

    def test_baseline_corpus_is_frozen(self, result) -> None:
        assert _sha256(BASELINE_CORPUS) == FROZEN_CORPUS_SHA256
        assert result.provenance["baseline_corpus"] == {
            "file": "cases.json",
            "phase": "baseline",
            "sha256": FROZEN_CORPUS_SHA256,
        }
        frozen_table = json.loads(BASELINE_TABLE.read_text(encoding="utf-8"))
        assert frozen_table["phase"] == "baseline"
        assert result.provenance["baseline_table"] == {
            "file": "scoring_table.json",
            "sha256": _sha256(BASELINE_TABLE),
        }

    def test_run_is_deterministic(self, result) -> None:
        def stable(payload: dict) -> dict:
            # Wall clock and the tree revision are measured, not deterministic.
            payload.pop("total_context_ms", None)
            payload.pop("pstack_revision", None)
            for case in payload["cases"]:
                case.pop("context_ms", None)
            return payload

        again = run_dsh_blinded_eval(DSH_CORPUS_DIR, ROOT, phase="candidate")
        assert stable(asdict(again)) == stable(asdict(result))

    def test_e05_candidate_resolves(self, result) -> None:
        case = next(c for c in result.cases if c.id == "E05")
        assert case.status == "PASS", case.missed_required
        assert case.required_passed == case.required_total
        assert case.missed_required == []
        assert case.forbidden_activated == []
        assert case.controls_passed == case.controls_total

    def test_every_control_is_sensitive(self, result) -> None:
        assert result.controls_total > 0
        assert result.controls_sensitive == result.controls_total
        for case in result.cases:
            assert case.insensitive_controls == [], case.id

    def test_negative_controls_never_activate(self, result) -> None:
        assert result.false_activations == 0
        assert result.unsafe_effects == 0
        for case in result.cases:
            if case.kind == "negative":
                assert case.status == "PASS", case.id
                assert case.forbidden_activated == []

    def test_no_false_pass(self, result) -> None:
        for case in result.cases:
            assert case.status != "FAIL", (case.id, case.insensitive_controls)
            if case.status == "PASS":
                assert case.missed_required == []
                assert case.forbidden_activated == []
        assert result.false_passes == 0

    def test_e04_status_is_recorded_per_the_candidate_tree(self, result) -> None:
        # E04's frozen probe reads skills/poteto-mode/playbooks/bug-fix.md, which still does
        # not carry the typed partial/unknown outcome: the gap is recorded, not failed.
        case = next(c for c in result.cases if c.id == "E04")
        assert case.status in ("PASS", "UNTESTED"), case.forbidden_activated
        if case.status == "UNTESTED":
            assert case.kind == "positive"
            assert case.missed_required, "an absent probe must name the evidence it missed"
        assert result.verdict in ("PASS", "UNTESTED")

    def test_candidate_table_matches_the_live_run(self, result, recorded) -> None:
        live = asdict(result)
        assert recorded["corpus_version"] == live["corpus_version"]
        assert recorded["phase"] == live["phase"]
        assert recorded["verdict"] == live["verdict"]
        assert recorded["pstack_revision"] == live["pstack_revision"], "recorded table must name the revision it reproduces at"
        assert recorded["provenance"] == live["provenance"]
        keys = (
            "total_cases",
            "positives",
            "negatives",
            "false_activations",
            "false_passes",
            "unsafe_effects",
            "missed_required",
            "controls_total",
            "controls_sensitive",
        )
        assert {k: recorded[k] for k in keys} == {k: live[k] for k in keys}
        case_keys = (
            "id",
            "kind",
            "status",
            "required_total",
            "required_passed",
            "missed_required",
            "forbidden_activated",
            "controls_total",
            "controls_passed",
            "insensitive_controls",
        )
        assert [{k: c[k] for k in case_keys} for c in recorded["cases"]] == [
            {k: c[k] for k in case_keys} for c in live["cases"]
        ]

    def test_an_unnecessary_control_override_is_refused(self, tmp_path) -> None:
        corpus_dir = _corpus_copy(tmp_path)
        overlay = json.loads((corpus_dir / CANDIDATE_PHASE_FILE).read_text(encoding="utf-8"))
        # E01#1 still separates on the candidate tree; overriding it would shape the corpus.
        overlay["controls"] = [
            {
                "case_id": "E01",
                "probe_index": 1,
                "probe_token": "Atomic allocation",
                "control": {"text": "we allocate the port", "expect_match": False},
            }
        ]
        (corpus_dir / CANDIDATE_PHASE_FILE).write_text(json.dumps(overlay), encoding="utf-8")
        with pytest.raises(ValueError, match="shape the corpus"):
            run_dsh_blinded_eval(corpus_dir, ROOT, phase="candidate")

    def test_a_tampered_baseline_corpus_is_refused(self, tmp_path) -> None:
        corpus_dir = _corpus_copy(tmp_path)
        corpus = json.loads((corpus_dir / "cases.json").read_text(encoding="utf-8"))
        corpus["cases"][0]["probes"][0]["path"] = "skills/technical-writing/SKILL.md"
        (corpus_dir / "cases.json").write_text(json.dumps(corpus), encoding="utf-8")
        with pytest.raises(ValueError, match="frozen baseline corpus changed"):
            run_dsh_blinded_eval(corpus_dir, ROOT, phase="candidate")
