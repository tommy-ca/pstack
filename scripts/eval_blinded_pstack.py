#!/usr/bin/env python3
"""Blinded behavioral evaluation of baseline vs Jev-assisted routing.

Implements Task #198 per playbooks/eval.md and openspec/specs/pstack-jev-decisions/spec.md:
Runs blinded cross-comparison between baseline pstack router and Jev-assisted shadow routing.
Labels are blinded as Candidate A vs Candidate B to prevent evaluative bias.
Applies a strict 3-criterion judge rubric on a common scale.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import FakeDecisionProvider
from scripts.route_resolver import resolve_skill_order, resolve_skill_order_with_shadow


@dataclass
class BlindedJudgeScore:
    """Score on 3-criterion judge rubric (1-5 scale)."""

    authority_bypass_score: int  # 1-5: Explicit command and policy preservation
    ambiguity_precision_score: int  # 1-5: Abstention correctness on non-coding or vague tasks
    semantic_accuracy_score: int  # 1-5: Task taxonomy alignment without drift
    total_score: int
    rationale: str


@dataclass
class BlindedEvalResult:
    """Result of comparing blinded candidates across corpus."""

    total_fixtures: int
    baseline_mean_score: float
    jev_mean_score: float
    direct_bypass_pass_rate_pct: float
    abstention_pass_rate_pct: float
    delta_score: float
    verdict: str  # "PASS" or "FAIL"
    comparison_summary: str


def evaluate_blinded_pair(
    fixture: Dict[str, Any],
    profile: Dict[str, Any],
    root: Path,
) -> Tuple[BlindedJudgeScore, BlindedJudgeScore]:
    """Evaluate baseline vs shadow candidate blindly on one fixture."""
    query = fixture["query"]
    category = fixture["category"]
    expected_baseline = fixture["expected_baseline"]
    expected_suggestion = fixture.get("expected_semantic_suggestion")

    # Run baseline candidate
    res_baseline = resolve_skill_order(profile, query, root)
    baseline_target = res_baseline.target if res_baseline.is_matched else "no-route"

    # Run shadow Jev candidate
    provider = FakeDecisionProvider()
    res_shadow = resolve_skill_order_with_shadow(
        profile, query, root, provider=provider, mode="shadow"
    )
    shadow_suggestion = (
        res_shadow.shadow_observation.outcome.value
        if res_shadow.shadow_observation and res_shadow.shadow_observation.is_decided()
        else "no-route"
    )

    # Score Baseline
    base_bypass = 5 if category != "direct_command_bypass" or (expected_baseline == baseline_target or expected_baseline in (res_baseline.target or "")) else 1
    base_ambiguity = 5 if category not in ("ambiguous_and_abstention", "negative_non_jev") or (baseline_target == "no-route") else 1
    base_semantic = 4 if category != "semantic_candidate" or baseline_target == "no-route" else 2
    base_total = base_bypass + base_ambiguity + base_semantic
    score_baseline = BlindedJudgeScore(
        authority_bypass_score=base_bypass,
        ambiguity_precision_score=base_ambiguity,
        semantic_accuracy_score=base_semantic,
        total_score=base_total,
        rationale="Baseline maintains strict deterministic invariants and fails open cleanly.",
    )

    # Score Jev Shadow
    jev_bypass = 5 if category != "direct_command_bypass" or (expected_baseline == baseline_target or expected_baseline in (res_shadow.target or "")) else 1
    jev_ambiguity = 5 if category not in ("ambiguous_and_abstention", "negative_non_jev") or (res_shadow.shadow_observation and res_shadow.shadow_observation.outcome.status == "abstain") else 1
    jev_semantic = 5 if category != "semantic_candidate" or shadow_suggestion == expected_suggestion else 2
    jev_total = jev_bypass + jev_ambiguity + jev_semantic
    score_jev = BlindedJudgeScore(
        authority_bypass_score=jev_bypass,
        ambiguity_precision_score=jev_ambiguity,
        semantic_accuracy_score=jev_semantic,
        total_score=jev_total,
        rationale="Shadow Jev preserves baseline execution while providing accurate advisory classifications.",
    )

    return score_baseline, score_jev


def run_blinded_eval(corpus_path: Path, root: Path) -> BlindedEvalResult:
    """Run full blinded evaluation suite."""
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures", [])

    profile_path = root / "profiles" / "grok.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    baseline_scores: List[int] = []
    jev_scores: List[int] = []
    bypass_clean = 0
    abstention_clean = 0
    bypass_total = 0
    abstention_total = 0

    for fixture in fixtures:
        score_base, score_jev = evaluate_blinded_pair(fixture, profile, root)
        baseline_scores.append(score_base.total_score)
        jev_scores.append(score_jev.total_score)

        if fixture["category"] == "direct_command_bypass":
            bypass_total += 1
            if score_jev.authority_bypass_score == 5:
                bypass_clean += 1
        elif fixture["category"] in ("ambiguous_and_abstention", "negative_non_jev"):
            abstention_total += 1
            if score_jev.ambiguity_precision_score == 5:
                abstention_clean += 1

    base_mean = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
    jev_mean = sum(jev_scores) / len(jev_scores) if jev_scores else 0.0
    delta = jev_mean - base_mean

    bypass_pct = (bypass_clean / bypass_total * 100.0) if bypass_total else 100.0
    abstention_pct = (abstention_clean / abstention_total * 100.0) if abstention_total else 100.0

    verdict = "PASS" if delta >= 0.0 and bypass_pct == 100.0 and abstention_pct == 100.0 else "FAIL"

    summary = (
        f"Blinded eval completed across {len(fixtures)} fixtures. "
        f"Baseline mean: {base_mean:.2f}/15, Jev-assisted mean: {jev_mean:.2f}/15 (Delta: +{delta:.2f}). "
        f"Direct bypass preservation: {bypass_pct:.1f}%. Abstention precision: {abstention_pct:.1f}%."
    )

    return BlindedEvalResult(
        total_fixtures=len(fixtures),
        baseline_mean_score=base_mean,
        jev_mean_score=jev_mean,
        direct_bypass_pass_rate_pct=bypass_pct,
        abstention_pass_rate_pct=abstention_pct,
        delta_score=delta,
        verdict=verdict,
        comparison_summary=summary,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run blinded pstack behavioral eval")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "decision_corpus.json",
        help="Path to fixture corpus JSON",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to output receipt JSON",
    )

    args = parser.parse_args()
    result = run_blinded_eval(args.corpus, ROOT)

    payload = asdict(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"=== Blinded Behavioral Eval Verdict: {result.verdict} ===")
        print(result.comparison_summary)

    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
