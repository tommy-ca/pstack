from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    CONDITIONAL_CAPABILITIES,
    ScenarioResult,
    ValidationError,
    VerificationReceipt,
    check_scenario_pins,
    derive_support_state,
    preserve_observed_settlements,
    reduce_verdicts,
    settle_planes,
)
from tests.evidence_test_helpers import (
    _adversarial_receipt,
    _observed_scenario,
    _profile_pinning,
    _success_settlement,
    _synthetic_evidence_root,
)


def _receipt_with_scenario(
    previous: VerificationReceipt, run_id: str, scenario: ScenarioResult
) -> VerificationReceipt:
    planes = settle_planes([scenario])
    receipt = replace(
        previous,
        run_id=run_id,
        planes=planes,
        overall_verdict=reduce_verdicts(planes.values()),
        scenarios=[scenario],
    )
    receipt.validate()
    return receipt


def test_a_session_pickup_never_satisfies_a_child_resume_pin() -> None:
    assert CONDITIONAL_CAPABILITIES["session.resume"] != CONDITIONAL_CAPABILITIES["agent.resume"]

    ref = ".audit/evidence/omp-receipt.json"
    pickup = _adversarial_receipt(_observed_scenario("session-pickup", settlement=None))
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(_profile_pinning(ref, "session-pickup"), {ref: pickup})

    child = _adversarial_receipt(
        _observed_scenario("child-resume", settlement=_success_settlement())
    )
    check_scenario_pins(_profile_pinning(ref, "child-resume"), {ref: child})


@pytest.mark.parametrize("outcome", ["cancelled", "timeout", "error"])
def test_a_non_success_child_settlement_never_satisfies_a_verified_pin(outcome: str) -> None:
    ref = ".audit/evidence/omp-receipt.json"
    scenario_id = f"child-{outcome}"
    failed = _adversarial_receipt(
        _observed_scenario(
            scenario_id, settlement=replace(_success_settlement(), terminal_outcome=outcome)
        )
    )
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(_profile_pinning(ref, scenario_id), {ref: failed})


def test_a_typed_cancellation_settles_only_the_cancel_capability() -> None:
    ref = ".audit/evidence/omp-receipt.json"
    scenario_id = "runtime-child-cancel-omp"
    cancelled = _adversarial_receipt(
        _observed_scenario(
            scenario_id, settlement=replace(_success_settlement(), terminal_outcome="cancelled")
        )
    )
    check_scenario_pins(_profile_pinning(ref, scenario_id, "agent.cancel"), {ref: cancelled})
    for capability in ("agent.spawn", "agent.join", "agent.resume"):
        with pytest.raises(ValidationError, match="carries no observed_live settlement"):
            check_scenario_pins(_profile_pinning(ref, scenario_id, capability), {ref: cancelled})

    for outcome in ("timeout", "error"):
        failed = _adversarial_receipt(
            _observed_scenario(
                scenario_id, settlement=replace(_success_settlement(), terminal_outcome=outcome)
            )
        )
        with pytest.raises(ValidationError, match="carries no observed_live settlement"):
            check_scenario_pins(_profile_pinning(ref, scenario_id, "agent.cancel"), {ref: failed})


def test_a_settled_cancellation_survives_a_durable_refresh() -> None:
    scenario_id = "runtime-child-cancel-omp"
    cancelled = _observed_scenario(
        scenario_id, settlement=replace(_success_settlement(), terminal_outcome="cancelled")
    )
    previous = _adversarial_receipt(cancelled)
    downgraded = replace(cancelled, evidence_level="static", settlement=None)
    current = replace(previous, run_id="refresh-run", scenarios=[downgraded])
    current.validate()

    assert preserve_observed_settlements(previous, current).preserved == [scenario_id]
    assert current.scenarios[0].evidence_level == "observed_live"
    assert current.scenarios[0].preserved_from == previous.run_id

    timed_out_previous = _adversarial_receipt(
        replace(cancelled, settlement=replace(_success_settlement(), terminal_outcome="timeout"))
    )
    timed_out_current = replace(timed_out_previous, run_id="refresh-run", scenarios=[downgraded])
    timed_out_current.validate()
    assert preserve_observed_settlements(timed_out_previous, timed_out_current).preserved == []


def test_route_missing_blocked_run_preserves_prior_observed_live_settlement() -> None:
    """#729: an environmental BLOCKED run preserves prior observed_live PASS without overwriting."""
    scenario_id = "runtime-child-spawn-omp"
    prior_scenario = _observed_scenario(
        scenario_id, settlement=_success_settlement()
    )
    previous = _adversarial_receipt(prior_scenario)

    # 1. Blocked attempt (e.g. route missing): must preserve prior PASS
    blocked_scenario = replace(
        prior_scenario,
        verdict="BLOCKED",
        exit_code=1,
        evidence_level="offline",
        settlement=None,
        live_attempted=False,
        stdout_snippet="BLOCKED: no configured model route",
    )
    current_blocked = _receipt_with_scenario(previous, "blocked-run", blocked_scenario)

    preservation = preserve_observed_settlements(previous, current_blocked)
    assert preservation.preserved == [scenario_id]
    assert preservation.dropped == []
    assert current_blocked.scenarios[0].evidence_level == "observed_live"
    assert current_blocked.scenarios[0].verdict == "PASS"
    assert current_blocked.scenarios[0].preserved_from == previous.run_id

    # 2. Executed live attempt that genuinely failed: must publish FAIL and NOT preserve prior PASS
    failed_scenario = replace(
        prior_scenario,
        verdict="FAIL",
        exit_code=1,
        evidence_level="offline",
        settlement=None,
        live_attempted=True,
        stdout_snippet="child failed",
    )
    current_failed = _receipt_with_scenario(previous, "failed-run", failed_scenario)

    preservation_failed = preserve_observed_settlements(previous, current_failed)
    assert preservation_failed.preserved == []
    assert preservation_failed.dropped == []
    assert current_failed.scenarios[0].verdict == "FAIL"


def test_a_cancellation_only_receipt_never_derives_verified(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, replace(_success_settlement(), terminal_outcome="cancelled")],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "packaged"


def test_a_verified_pin_naming_an_unrecorded_scenario_is_a_dangling_reference() -> None:
    ref = ".audit/evidence/omp-receipt.json"
    receipt = _adversarial_receipt(
        _observed_scenario("child-resume", settlement=_success_settlement())
    )
    with pytest.raises(ValidationError, match="does not record"):
        check_scenario_pins(_profile_pinning(ref, "child-resume-typo"), {ref: receipt})
