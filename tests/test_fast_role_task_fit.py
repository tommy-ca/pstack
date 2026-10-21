#!/usr/bin/env python3
"""Tests for fast-worker role task-fit, cognitive frontier protection, and catalog confinement.

Implements Issue #517 and Issue #670 per ADR-0022:
- Asserts cognitive frontier roles cannot be demoted to fast workers.
- Asserts catalog confinement under Contract #429 (no invented model slugs).
- Asserts refactoring < 100 LOC boundary and test coverage requirement.
- Asserts shadow mode behavior when calibrated evidence is missing.
- Asserts zero bloat to QStack (100% contained in pstack).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_fast_role_task_fit import (
    COGNITIVE_FRONTIER_ROLES,
    FAST_WORKER_ELIGIBLE_ROLES,
    HOLDOUT_CORPUS,
    HoldoutTask,
    evaluate_task_baseline,
    evaluate_task_deterministic,
    evaluate_task_semantic,
    load_host_model_catalog,
    run_benchmark,
)


@pytest.fixture
def antigravity_catalog() -> Dict[str, Any]:
    return load_host_model_catalog("antigravity", ROOT)


class TestFastRoleTaskFitInvariants:
    """Invariant enforcement tests for fast worker role-fit."""

    def test_cognitive_frontier_roles_cannot_be_demoted(
        self, antigravity_catalog: Dict[str, Any]
    ) -> None:
        """Cognitive frontier roles MUST remain in frontier/panel/strongest tier."""
        for role in COGNITIVE_FRONTIER_ROLES:
            task = HoldoutTask(
                id=f"test_demote_{role}",
                description=f"Attempted demotion test for {role}",
                domain="pstack-core",
                target_role=role,
                diff_loc=10,
                has_test_coverage=True,
                consequence_of_error="low",  # even on low consequence, role must not demote
                expected_baseline_tier="panel" if "panel" in role or "judge" in role or "runner" in role else "strongest",
                expected_optimal_tier="panel" if "panel" in role or "judge" in role or "runner" in role else "strongest",
            )

            # Test deterministic pipeline
            det_outcome = evaluate_task_deterministic(task, antigravity_catalog)
            assert not det_outcome.demotion_violation
            assert det_outcome.assigned_tier not in ("fast-worker", "fast-verifier")

            # Test semantic pipeline with hostile demotion suggestion
            sem_outcome = evaluate_task_semantic(
                task,
                antigravity_catalog,
                has_calibrated_evidence=True,
                simulated_suggestion="fast-worker",
            )
            # Demotion attempt must be blocked and fail open to baseline
            assert sem_outcome.demotion_violation
            assert sem_outcome.assigned_tier not in ("fast-worker", "fast-verifier")

    def test_catalog_confinement_contract_429(
        self, antigravity_catalog: Dict[str, Any]
    ) -> None:
        """Candidate models must exist in host catalog; invented slugs are blocked."""
        restricted_catalog = copy.deepcopy(antigravity_catalog)
        # Point fast-worker tier to an invented / unmapped slug
        restricted_catalog["tier_mapping"]["fast-worker"] = ["invented-model-v99"]

        task = HoldoutTask(
            id="test_unmapped_slug",
            description="Task with unmapped model catalog slug",
            domain="pstack-core",
            target_role="comment-sicko",
            diff_loc=15,
            has_test_coverage=True,
            consequence_of_error="low",
            expected_baseline_tier="fast-worker",
            expected_optimal_tier="fast-worker",
        )

        outcome = evaluate_task_deterministic(task, restricted_catalog)
        assert outcome.unmapped_model_violation
        assert outcome.status == "BLOCKED"
        assert not outcome.task_success

    def test_fast_worker_eligible_roster_membership(self) -> None:
        """Ensure designated roles are present in eligible fast worker roster."""
        assert "comment-sicko" in FAST_WORKER_ELIGIBLE_ROLES
        assert "how-explorer" in FAST_WORKER_ELIGIBLE_ROLES
        assert "why-investigators" in FAST_WORKER_ELIGIBLE_ROLES
        assert "swarm-workers" in FAST_WORKER_ELIGIBLE_ROLES
        assert "refactoring" in FAST_WORKER_ELIGIBLE_ROLES

        # Cognitive roles must NOT be in eligible roster
        for role in COGNITIVE_FRONTIER_ROLES:
            assert role not in FAST_WORKER_ELIGIBLE_ROLES

    def test_refactoring_loc_and_coverage_boundary(
        self, antigravity_catalog: Dict[str, Any]
    ) -> None:
        """Refactoring role is eligible for fast-worker ONLY when < 100 LOC, low risk, and tested."""
        # 1. Under 100 LOC, low consequence, with tests -> fast-worker
        task_small = HoldoutTask(
            id="small_refactor",
            description="Small refactor",
            domain="pstack-core",
            target_role="refactoring",
            diff_loc=45,
            has_test_coverage=True,
            consequence_of_error="low",
            expected_baseline_tier="strongest",
            expected_optimal_tier="fast-worker",
        )
        out_small = evaluate_task_deterministic(task_small, antigravity_catalog)
        assert out_small.assigned_tier == "fast-worker"

        # 2. Over 100 LOC -> strongest
        task_large = HoldoutTask(
            id="large_refactor",
            description="Large refactor",
            domain="pstack-core",
            target_role="refactoring",
            diff_loc=150,
            has_test_coverage=True,
            consequence_of_error="low",
            expected_baseline_tier="strongest",
            expected_optimal_tier="strongest",
        )
        out_large = evaluate_task_deterministic(task_large, antigravity_catalog)
        assert out_large.assigned_tier == "strongest"

        # 3. Under 100 LOC, but high consequence of error -> strongest
        task_high_risk = HoldoutTask(
            id="high_risk_refactor",
            description="High risk refactor",
            domain="pstack-core",
            target_role="refactoring",
            diff_loc=30,
            has_test_coverage=True,
            consequence_of_error="high",
            expected_baseline_tier="strongest",
            expected_optimal_tier="strongest",
        )
        out_high_risk = evaluate_task_deterministic(task_high_risk, antigravity_catalog)
        assert out_high_risk.assigned_tier == "strongest"

        # 4. Under 100 LOC, but without tests -> strongest
        task_untested = HoldoutTask(
            id="untested_refactor",
            description="Untested refactor",
            domain="pstack-core",
            target_role="refactoring",
            diff_loc=30,
            has_test_coverage=False,
            consequence_of_error="low",
            expected_baseline_tier="strongest",
            expected_optimal_tier="strongest",
        )
        out_untested = evaluate_task_deterministic(task_untested, antigravity_catalog)
        assert out_untested.assigned_tier == "strongest"

    def test_shadow_mode_when_calibrated_evidence_absent(
        self, antigravity_catalog: Dict[str, Any]
    ) -> None:
        """When calibrated evidence is absent, semantic suggestions remain in shadow mode."""
        task = HoldoutTask(
            id="shadow_refactor_test",
            description="Small refactor needing evidence for promotion",
            domain="pstack-core",
            target_role="refactoring",
            diff_loc=20,
            has_test_coverage=True,
            consequence_of_error="low",
            expected_baseline_tier="strongest",
            expected_optimal_tier="fast-worker",
        )

        outcome = evaluate_task_semantic(
            task,
            antigravity_catalog,
            has_calibrated_evidence=False,
            simulated_suggestion="fast-worker",
        )
        # Without calibrated evidence, executed tier remains baseline
        assert outcome.assigned_tier == "strongest"
        assert "shadow observation" in outcome.notes

    def test_complete_holdout_benchmark_runs_cleanly(self) -> None:
        """Verify the full 3-way benchmark executes with 0 violations."""
        results = run_benchmark(ROOT, host="antigravity")
        assert results["holdout_tasks_count"] == 12
        assert results["qstack_tasks_count"] == 4
        assert results["invariants"]["cognitive_frontier_demotions"] == 0
        assert results["invariants"]["unmapped_model_violations"] == 0
        assert results["invariants"]["zero_qstack_bloat_enforced"] is True
        assert results["cost_savings"]["deterministic_vs_baseline_pct"] > 15.0
