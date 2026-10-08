#!/usr/bin/env python3
"""Tests for offline decision routing evaluation and calibration lever."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_decision_routing import (
    MAX_COST_PER_DECISION_BUDGET,
    MAX_P95_LATENCY_MS_BUDGET,
    MIN_BYPASS_ACCURACY_PERCENT,
    run_evaluation,
)


class TestEvalDecisionRouting:
    """Tests verifying the offline evaluation lever and budget enforcement."""

    def test_run_evaluation_passes_with_fake_provider(self) -> None:
        corpus = ROOT / "tests" / "fixtures" / "decision_corpus.json"
        metrics, items = run_evaluation(corpus, ROOT, provider_type="fake")

        assert metrics.verdict == "PASS"
        assert metrics.total_fixtures > 0
        assert metrics.direct_bypass_accuracy_pct == 100.0
        assert metrics.semantic_top1_accuracy_pct >= 80.0
        assert metrics.abstention_precision_pct == 100.0
        assert metrics.latency_budget_met is True
        assert metrics.cost_budget_met is True
        assert len(items) == metrics.total_fixtures

    def test_run_evaluation_with_disabled_provider_preserves_bypasses(self) -> None:
        corpus = ROOT / "tests" / "fixtures" / "decision_corpus.json"
        metrics, items = run_evaluation(corpus, ROOT, provider_type="disabled")

        assert metrics.direct_bypass_accuracy_pct == 100.0
        assert metrics.abstention_precision_pct == 100.0
        assert metrics.latency_budget_met is True
        assert metrics.verdict == "PASS"

    def test_missing_corpus_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            run_evaluation(Path("/nonexistent/corpus.json"), ROOT)
