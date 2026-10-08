#!/usr/bin/env python3
"""Tests for blinded behavioral evaluation runner."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_blinded_pstack import run_blinded_eval


class TestBlindedEval:
    """Tests verifying blinded cross-comparison execution and invariants."""

    def test_run_blinded_eval_passes(self) -> None:
        corpus = ROOT / "tests" / "fixtures" / "decision_corpus.json"
        result = run_blinded_eval(corpus, ROOT)

        assert result.verdict == "PASS"
        assert result.total_fixtures == 12
        assert result.direct_bypass_pass_rate_pct == 100.0
        assert result.abstention_pass_rate_pct == 100.0
        assert result.delta_score >= 0.0
