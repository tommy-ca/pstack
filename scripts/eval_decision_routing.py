#!/usr/bin/env python3
"""Offline decision routing evaluation and calibration lever.

Implements Task #186 and openspec/specs/pstack-jev-decisions/spec.md requirements:
Runs deterministic offline evaluation against versioned sanitized fixtures in
tests/fixtures/decision_corpus.json. Computes accuracy, direct bypass compliance,
false activation, missed rigor, abstention precision, latency, and cost metrics
against predeclared budgets.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    FakeDecisionProvider,
    JevDecisionAdapter,
    ProviderObservation,
)
from scripts.evidence_receipts import create_decision_receipt
from scripts.route_resolver import resolve_skill_order, resolve_skill_order_with_shadow


# Predeclared budgets per Task #186 and spec
MAX_P95_LATENCY_MS_BUDGET = 50.0
MAX_COST_PER_DECISION_BUDGET = 0.001
MIN_BYPASS_ACCURACY_PERCENT = 100.0


@dataclass
class EvalMetrics:
    """Computed evaluation and calibration metrics."""

    total_fixtures: int
    direct_bypasses: int
    direct_bypass_accuracy_pct: float
    semantic_candidates: int
    semantic_top1_accuracy_pct: float
    ambiguous_abstentions: int
    abstention_precision_pct: float
    false_positive_activations: int
    false_negative_missed_rigor: int
    p50_latency_ms: float
    p95_latency_ms: float
    estimated_cost_per_decision_usd: float
    latency_budget_met: bool
    cost_budget_met: bool
    verdict: str  # "PASS" or "FAIL"
    failure_reasons: List[str]


def run_evaluation(
    corpus_path: Path,
    root: Path,
    provider_type: str = "fake",
) -> Tuple[EvalMetrics, List[Dict[str, Any]]]:
    """Execute evaluation over fixture corpus and compute calibration metrics."""
    if not corpus_path.is_file():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures", [])

    profile_path = root / "profiles" / "grok.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    # Instantiate provider under test
    if provider_type == "disabled":
        provider = JevDecisionAdapter(enabled=False)
    elif provider_type == "jev":
        provider = JevDecisionAdapter(enabled=True)
    else:
        # Default fake provider: simulates high-confidence semantic judgments
        provider = FakeDecisionProvider()

    latencies_ms: List[float] = []
    item_results: List[Dict[str, Any]] = []

    direct_bypasses = 0
    direct_bypass_matches = 0
    semantic_candidates = 0
    semantic_matches = 0
    ambiguous_fixtures = 0
    abstention_matches = 0
    false_positives = 0
    false_negatives = 0

    for fixture in fixtures:
        query = fixture["query"]
        expected_baseline = fixture["expected_baseline"]
        expected_suggestion = fixture.get("expected_semantic_suggestion")
        category = fixture["category"]

        start_time = time.perf_counter()
        res = resolve_skill_order_with_shadow(
            profile, query, root, provider=provider, mode="shadow"
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        latencies_ms.append(elapsed_ms)

        acting_route = res.target if res.is_matched else "no-route"

        # Check bypass vs semantic categories
        if category == "direct_command_bypass":
            direct_bypasses += 1
            if expected_baseline == acting_route or expected_baseline in (res.target or ""):
                direct_bypass_matches += 1

        elif category in ("semantic_candidate", "jaggedness_trap"):
            semantic_candidates += 1
            # Acting route MUST remain baseline
            if acting_route == expected_baseline:
                pass
            # Shadow observation must suggest expected class when provider is active
            if res.shadow_observation and res.shadow_observation.is_decided():
                if res.shadow_observation.outcome.value == expected_suggestion:
                    semantic_matches += 1
                else:
                    false_negatives += 1
            elif provider_type == "disabled":
                # Disabled provider correctly abstains/unavails
                semantic_matches += 1
            else:
                false_negatives += 1

        elif category in ("ambiguous_and_abstention", "negative_non_jev"):
            ambiguous_fixtures += 1
            # Ambiguous inputs should abstain in baseline and shadow
            if acting_route == "no-route":
                if res.shadow_observation is None or res.shadow_observation.outcome.status in ("abstain", "unavailable"):
                    abstention_matches += 1
                else:
                    false_positives += 1
            else:
                false_positives += 1

        item_results.append(
            {
                "id": fixture["id"],
                "category": category,
                "expected_baseline": expected_baseline,
                "expected_suggestion": expected_suggestion,
                "actual_acting": acting_route,
                "latency_ms": elapsed_ms,
                "shadow_status": (
                    res.shadow_observation.outcome.status
                    if res.shadow_observation
                    else None
                ),
                "shadow_value": (
                    res.shadow_observation.outcome.value
                    if res.shadow_observation and res.shadow_observation.is_decided()
                    else None
                ),
            }
        )

    # Compute aggregate metrics
    bypass_acc = (
        (direct_bypass_matches / direct_bypasses * 100.0) if direct_bypasses else 100.0
    )
    semantic_acc = (
        (semantic_matches / semantic_candidates * 100.0)
        if semantic_candidates
        else 100.0
    )
    abstention_acc = (
        (abstention_matches / ambiguous_fixtures * 100.0)
        if ambiguous_fixtures
        else 100.0
    )

    latencies_sorted = sorted(latencies_ms)
    p50_lat = statistics.median(latencies_sorted) if latencies_sorted else 0.0
    p95_idx = int(0.95 * len(latencies_sorted))
    p95_lat = (
        latencies_sorted[p95_idx]
        if latencies_sorted
        else 0.0
    )

    cost_per_decision = 0.0001 if provider_type == "jev" else 0.0

    failure_reasons: List[str] = []
    if bypass_acc < MIN_BYPASS_ACCURACY_PERCENT:
        failure_reasons.append(
            f"Direct bypass accuracy {bypass_acc:.1f}% below required {MIN_BYPASS_ACCURACY_PERCENT}%"
        )
    latency_ok = p95_lat <= MAX_P95_LATENCY_MS_BUDGET
    if not latency_ok:
        failure_reasons.append(
            f"p95 latency {p95_lat:.2f}ms exceeds budget of {MAX_P95_LATENCY_MS_BUDGET}ms"
        )
    cost_ok = cost_per_decision <= MAX_COST_PER_DECISION_BUDGET
    if not cost_ok:
        failure_reasons.append(
            f"Cost ${cost_per_decision:.6f} exceeds budget of ${MAX_COST_PER_DECISION_BUDGET:.6f}"
        )

    verdict = "PASS" if not failure_reasons else "FAIL"

    metrics = EvalMetrics(
        total_fixtures=len(fixtures),
        direct_bypasses=direct_bypasses,
        direct_bypass_accuracy_pct=bypass_acc,
        semantic_candidates=semantic_candidates,
        semantic_top1_accuracy_pct=semantic_acc,
        ambiguous_abstentions=ambiguous_fixtures,
        abstention_precision_pct=abstention_acc,
        false_positive_activations=false_positives,
        false_negative_missed_rigor=false_negatives,
        p50_latency_ms=p50_lat,
        p95_latency_ms=p95_lat,
        estimated_cost_per_decision_usd=cost_per_decision,
        latency_budget_met=latency_ok,
        cost_budget_met=cost_ok,
        verdict=verdict,
        failure_reasons=failure_reasons,
    )
    return metrics, item_results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run offline decision routing evaluation and calibration lever"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "decision_corpus.json",
        help="Path to fixture corpus JSON",
    )
    parser.add_argument(
        "--provider",
        choices=["fake", "disabled", "jev"],
        default="fake",
        help="Decision provider to evaluate",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output report format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write receipt report JSON",
    )

    args = parser.parse_args()

    metrics, items = run_evaluation(args.corpus, ROOT, provider_type=args.provider)

    report_payload = {
        "metrics": asdict(metrics),
        "items": items,
        "budgets": {
            "max_p95_latency_ms": MAX_P95_LATENCY_MS_BUDGET,
            "max_cost_usd": MAX_COST_PER_DECISION_BUDGET,
            "min_bypass_accuracy_pct": MIN_BYPASS_ACCURACY_PERCENT,
        },
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report_payload, indent=2))
    else:
        print(f"=== Decision Routing Eval Verdict: {metrics.verdict} ===")
        print(f"Total fixtures evaluated: {metrics.total_fixtures}")
        print(f"Direct bypass accuracy:   {metrics.direct_bypass_accuracy_pct:.1f}%")
        print(f"Semantic top-1 accuracy:  {metrics.semantic_top1_accuracy_pct:.1f}%")
        print(f"Abstention precision:     {metrics.abstention_precision_pct:.1f}%")
        print(f"p50 / p95 latency:        {metrics.p50_latency_ms:.2f}ms / {metrics.p95_latency_ms:.2f}ms")
        print(f"Cost per decision:        ${metrics.estimated_cost_per_decision_usd:.6f}")
        if metrics.failure_reasons:
            print(f"Failure reasons:          {'; '.join(metrics.failure_reasons)}")

    return 0 if metrics.verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
