"""Evidence durability checking, scenario pin verification, and support state derivation.

Separated from portability_schema.py for modular decomposition (#593).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.portability_types import (
    MANDATORY_SUPPORT_FLOOR,
    PORTABLE_CAPABILITY_UNIVERSE,
    SETTLEMENT_PROMOTIONS,
    SUPPORT_STATES,
    Binding,
    ChildSettlement,
    HarnessProfile,
    ScenarioResult,
    ValidationError,
    VerificationReceipt,
    _is_observed_settlement,
)
from scripts.surface_revisions import SurfaceRevisions, compute_surface_revisions


def _is_preservable_settlement(scenario: ScenarioResult) -> bool:
    return _is_observed_settlement(scenario) or any(
        _is_observed_settlement(scenario, capability) for capability in SETTLEMENT_PROMOTIONS
    )


@dataclass(frozen=True)
class Preservation:
    """What a durable write keeps, and which prior settlements it would lose."""

    preserved: List[str]
    dropped: List[str]


def preserve_observed_settlements(
    previous: VerificationReceipt,
    current: VerificationReceipt,
) -> Preservation:
    """Carry prior live settlements into `current`, and name the ones it would lose.

    `dropped` holds prior settlements the new receipt neither preserves nor
    re-observes through an attempted live gate. A live attempt that failed still
    produced evidence, so its row is written instead of counted as a loss.
    """
    if previous.host != current.host:
        return Preservation([], [])
    previous.validate()
    current.validate()
    prior = {s.id: s for s in previous.scenarios if _is_preservable_settlement(s)}
    preserved: List[str] = []
    if not previous.evaluate_plane_staleness(current.surface_revisions).get("runtime"):
        for i, scenario in enumerate(current.scenarios):
            candidate = prior.get(scenario.id)
            if candidate is None or _is_preservable_settlement(scenario):
                continue
            # A prior observed_live settlement is preserved when current is a static PASS
            # or an environmental BLOCKED run (e.g. missing route / credentials, #729).
            # A live FAIL represents a real executed attempt that failed and must be published.
            if scenario.verdict not in ("PASS", "BLOCKED"):
                continue
            current.scenarios[i] = replace(
                candidate, preserved_from=candidate.preserved_from or previous.run_id
            )
            preserved.append(scenario.id)
    current_by_id = {s.id: s for s in current.scenarios}
    dropped = [
        sid
        for sid in prior
        if sid not in current_by_id
        or not (_is_preservable_settlement(current_by_id[sid]) or current_by_id[sid].live_attempted)
    ]
    return Preservation(preserved, dropped)


def _row_receipt(binding: Binding, root: Path) -> Optional[VerificationReceipt]:
    if binding.verification_status != "verified":
        return None
    if not binding.receipt_ref or not (root / binding.receipt_ref).is_file():
        return None
    try:
        receipt = VerificationReceipt(
            **json.loads((root / binding.receipt_ref).read_text(encoding="utf-8"))
        )
        receipt.validate()
    except Exception:
        return None
    return receipt


def _row_level(
    receipt: Optional[VerificationReceipt],
    profile: HarnessProfile,
    current_revisions: SurfaceRevisions,
    *,
    require_package: bool,
) -> str:
    if receipt is None or receipt.host != profile.host:
        return ""
    rest = ("canonical", "adapter", "package") if require_package else ("canonical", "adapter")
    if receipt.planes.get("runtime") != "PASS" or any(
        receipt.planes.get(p) != "PASS" for p in rest
    ):
        return ""
    stale = receipt.evaluate_plane_staleness(current_revisions)
    if any(stale.get(p) for p in ("runtime", *rest)):
        return ""
    if profile.host == "omp" and (
        any(not s.evidence_level for s in receipt.scenarios)
        or not any(_is_observed_settlement(s) for s in receipt.scenarios)
    ):
        return ""
    return "supported" if require_package else "verified"


def derive_support_state(
    profile: HarnessProfile,
    root: Path,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> str:
    profile.validate()
    bound_caps = {b.capability: b for b in profile.bindings}
    if not bound_caps or any(c not in bound_caps for c in PORTABLE_CAPABILITY_UNIVERSE):
        return "candidate"

    if current_revisions is None:
        current_revisions = compute_surface_revisions(root, profile.host)

    if profile.tool_mappings is None or profile.runtime_conventions is None:
        return "mapped"

    if not profile.plugin_manifest or not (root / profile.plugin_manifest).is_file():
        return "mapped"
    if not (root / "pstack.package.json").is_file():
        return "mapped"

    for cap_id in MANDATORY_SUPPORT_FLOOR:
        if _row_level(
            _row_receipt(bound_caps[cap_id], root),
            profile,
            current_revisions,
            require_package=False,
        ) != "verified":
            return "packaged"

    for binding in bound_caps.values():
        if _row_level(
            _row_receipt(binding, root),
            profile,
            current_revisions,
            require_package=True,
        ) != "supported":
            return "verified"

    return "supported"


def check_scenario_pins(
    profile: HarnessProfile, receipts_by_ref: Dict[str, VerificationReceipt]
) -> None:
    for binding in profile.bindings:
        scenario_id = binding.scenario_id
        if not scenario_id:
            continue
        receipt = receipts_by_ref.get(binding.receipt_ref or "")
        if receipt is None:
            raise ValidationError(
                f"Dangling evidence path for {profile.host}: {binding.receipt_ref}"
            )
        scenario = next((s for s in receipt.scenarios if s.id == scenario_id), None)
        if scenario is None:
            raise ValidationError(
                f"Binding for {binding.capability} on {binding.host} cites scenario {scenario_id!r}, "
                f"which {binding.receipt_ref} does not record"
            )
        if binding.verification_status == "verified" and not _is_observed_settlement(
            scenario, binding.capability
        ):
            raise ValidationError(
                f"Binding for {binding.capability} on {binding.host} claims verified but scenario "
                f"{scenario_id!r} carries no observed_live settlement (evidence_level="
                f"{scenario.evidence_level!r}, verdict={scenario.verdict!r}); restore the live proof "
                "(omp: PSTACK_RUN_OMP_LIVE=1) or record the row as static-only"
            )


def check_evidence_durability(
    profile: HarnessProfile,
    root: Path,
    check_freshness: bool = True,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> Dict[str, Any]:
    profile.validate()
    refs = {b.receipt_ref for b in profile.bindings if b.receipt_ref}
    refs.update(e.artifact for e in profile.evidence_ledger if e.artifact)

    if profile.support_state in ("verified", "supported") and not refs:
        raise ValidationError(
            f"Harness profile for {profile.host} claims {profile.support_state} but declares no evidence references"
        )

    receipts_by_ref: Dict[str, VerificationReceipt] = {}
    for ref in sorted(refs):
        path = root / ref
        if not path.is_file():
            raise ValidationError(
                f"Dangling evidence path for {profile.host}: {ref}"
            )
        try:
            rdata = json.loads(path.read_text(encoding="utf-8"))
            receipt = VerificationReceipt(**rdata)
            receipt.validate()
        except Exception as err:
            raise ValidationError(
                f"Evidence file {ref} for {profile.host} is not a valid VerificationReceipt: {err}"
            ) from err

        if receipt.host != profile.host:
            raise ValidationError(
                f"Evidence file {ref} host mismatch: expected {profile.host}, got {receipt.host}"
            )
        receipts_by_ref[ref] = receipt

    if current_revisions is None:
        current_revisions = compute_surface_revisions(root, profile.host)

    staleness_by_ref: Dict[str, Dict[str, List[str]]] = {}
    for ref, receipt in receipts_by_ref.items():
        staleness_by_ref[ref] = receipt.evaluate_plane_staleness(current_revisions)

    derived_state = derive_support_state(profile, root, current_revisions=current_revisions)

    check_scenario_pins(profile, receipts_by_ref)

    if check_freshness:
        if profile.support_state in ("verified", "supported", "packaged"):
            stale_details: List[str] = []
            if profile.support_state == "packaged":
                freshness_planes = ("package",)
            else:
                freshness_planes = ("canonical", "adapter", "runtime", "package")
            for b in profile.bindings:
                if b.capability in MANDATORY_SUPPORT_FLOOR:
                    if b.receipt_ref and b.receipt_ref in staleness_by_ref:
                        s_map = staleness_by_ref[b.receipt_ref]
                        for plane in freshness_planes:
                            if s_map.get(plane):
                                stale_details.append(f"{b.capability} ({plane}): {', '.join(s_map[plane])}")
            if stale_details:
                raise ValidationError(
                    f"Profile {profile.host} evidence is stale for claimed {profile.support_state}: {'; '.join(stale_details[:5])}"
                )
        claimed_idx = SUPPORT_STATES.index(profile.support_state)
        derived_idx = SUPPORT_STATES.index(derived_state)
        if claimed_idx > derived_idx:
            raise ValidationError(
                f"Hand-authored support state {profile.support_state!r} for {profile.host} exceeds "
                f"evidence-derived support state {derived_state!r}."
            )

    return {
        "valid": True,
        "host": profile.host,
        "claimed_support_state": profile.support_state,
        "derived_support_state": derived_state,
        "receipts_checked": len(receipts_by_ref),
        "staleness": staleness_by_ref,
    }
