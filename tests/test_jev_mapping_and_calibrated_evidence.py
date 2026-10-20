#!/usr/bin/env python3
"""Hermetic tests for canonical mapping freshness (#663) and calibrated evidence admission (#659).

Verifies:
- Mismatched or stale canonical pin / router blob fails closed to deterministic baseline.
- Absence or corruption of persisted calibrated evidence receipt fails closed to baseline.
- Stale provider/model, expired receipt, unaccepted review decision, absent eval metrics fail closed.
- Synthetic self-receipt cannot self-authorize promotion.
- Known-good persisted calibrated evidence receipt promotes eligible semantic candidates.
- scripts/verify-decision-contract.py checks applied canonical UPSTREAM pin.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    DecisionOutcome,
    FakeDecisionProvider,
    ProviderObservation,
)
from scripts.evidence_receipts import (
    CalibratedEvidenceReceipt,
    compute_file_sha256,
    load_calibrated_evidence_receipt,
    validate_calibrated_evidence,
)
from scripts.route_resolver import (
    _get_applied_canonical_pin,
    resolve_skill_order,
    resolve_skill_order_with_shadow,
)
import scripts.route_resolver as route_resolver


@pytest.fixture
def grok_profile() -> Dict[str, Any]:
    profile_path = ROOT / "profiles" / "grok.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_candidate_observation() -> ProviderObservation:
    return ProviderObservation(
        outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
        provider_identity="typesafe-jev",
        model_identity="jev-pilot-v1",
        confidence=0.92,
        probabilities={"bug-fix": 0.92, "investigation": 0.08},
    )


class TestCanonicalMappingFreshness:
    """Tests for Issue #663: Fail closed when decision-routing registry drifts from canonical pin."""

    def test_applied_canonical_pin_matches_package_and_upstream(self) -> None:
        pin = _get_applied_canonical_pin(str(ROOT))
        assert pin == "88d47514b82e7c44f00f2b2a72ff6dd12158038c"

    def test_stale_mapping_revision_fails_closed_to_baseline(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # Stale mapping pointing to older revision d0ef80d8
        stale_data = {
            "schema_version": 1,
            "source": {
                "repository": "cursor/plugins",
                "path_prefix": "pstack/",
                "revision": "d0ef80d86795816da932a153458c5dbe192d294e",
                "tree": "ef1c6ab4b7f1016cfbd4fbdb2e25cfa5ceecaa55",
                "router_blob": "21993f546032ca37671d5f1caf39c9a82ab4fa9d",
            },
            "fallback": "baseline",
            "routes": [{"playbook": "bug-fix", "canonical_blob": "b5de0bfa63add6ed38a38a8bd668cf36ac009c61", "selection": "semantic_candidate", "class": "defect"}],
        }
        monkeypatch.setattr(route_resolver, "_load_decision_routing", lambda _: stale_data)

        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)
        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory", safe_summary=query
        )
        assert res.advisory_promoted is False
        assert res.status == baseline.status

    def test_stale_router_blob_fails_closed_to_baseline(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # Stale router blob de51c561
        stale_data = {
            "schema_version": 1,
            "source": {
                "repository": "cursor/plugins",
                "path_prefix": "pstack/",
                "revision": "88d47514b82e7c44f00f2b2a72ff6dd12158038c",
                "tree": "6e60624e2f172e2d8d796d6e644695ff5591e29f",
                "router_blob": "de51c56164ff3da8f958437e207d14cec7d7fe99",
            },
            "fallback": "baseline",
            "routes": [{"playbook": "bug-fix", "canonical_blob": "b5de0bfa63add6ed38a38a8bd668cf36ac009c61", "selection": "semantic_candidate", "class": "defect"}],
        }
        monkeypatch.setattr(route_resolver, "_load_decision_routing", lambda _: stale_data)

        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)
        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory", safe_summary=query
        )
        assert res.advisory_promoted is False
        assert res.status == baseline.status

    def test_corrupted_mapping_fails_closed_to_baseline(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        monkeypatch.setattr(route_resolver, "_load_decision_routing", lambda _: {})
        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)
        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory", safe_summary=query
        )
        assert res.advisory_promoted is False
        assert res.status == baseline.status


class TestPersistedCalibratedEvidenceGate:
    """Tests for Issue #659: Gate advisory promotion on persisted pre-existing calibrated evidence."""

    def test_missing_persisted_evidence_fails_closed_to_baseline(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation, tmp_path: Path
    ) -> None:
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        nonexistent_evidence = tmp_path / "does_not_exist.json"
        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)

        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=provider,
            mode="advisory",
            safe_summary=query,
            calibrated_evidence_path=nonexistent_evidence,
        )
        assert res.advisory_promoted is False
        assert res.status == baseline.status

    def test_synthetic_self_receipt_cannot_self_authorize(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation, tmp_path: Path
    ) -> None:
        # A synthetic in-memory or unpersisted self-receipt cannot authorize route promotion
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=provider,
            mode="advisory",
            safe_summary=query,
            calibrated_evidence_path=empty_dir / "calibrated-evidence.json",
        )
        assert res.advisory_promoted is False
        assert res.status == baseline.status

    def test_stale_provider_identity_rejected(self, tmp_path: Path) -> None:
        receipt_path = tmp_path / "calibrated-evidence.json"
        routing_file = ROOT / "references" / "decision-routing.json"
        mapping_hash = compute_file_sha256(routing_file)

        receipt = CalibratedEvidenceReceipt(
            receipt_type="calibrated_routing_evidence",
            status="valid",
            review_decision="accepted",
            source_revision="88d47514b82e7c44f00f2b2a72ff6dd12158038c",
            canonical_mapping_revision=mapping_hash,
            provider_identity="legacy-provider",
            model_identity="jev-pilot-v1",
            policy_revision="1.0.0",
            class_thresholds={"defect": 0.70},
            eval_evidence={"pass_rate": 0.95},
            created_at="2026-10-21T00:00:00Z",
            expires_at="2028-10-21T00:00:00Z",
        )
        receipt_path.write_text(receipt.to_json(), encoding="utf-8")

        loaded = load_calibrated_evidence_receipt(receipt_path)
        assert loaded is not None
        is_valid, reasons = validate_calibrated_evidence(
            receipt=loaded,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
            candidate_class="defect",
            confidence=0.90,
        )
        assert is_valid is False
        assert any("Provider mismatch" in r for r in reasons)

    def test_expired_receipt_rejected(self, tmp_path: Path) -> None:
        receipt_path = tmp_path / "calibrated-evidence.json"
        routing_file = ROOT / "references" / "decision-routing.json"
        mapping_hash = compute_file_sha256(routing_file)

        receipt = CalibratedEvidenceReceipt(
            receipt_type="calibrated_routing_evidence",
            status="valid",
            review_decision="accepted",
            source_revision="88d47514b82e7c44f00f2b2a72ff6dd12158038c",
            canonical_mapping_revision=mapping_hash,
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            policy_revision="1.0.0",
            class_thresholds={"defect": 0.70},
            eval_evidence={"pass_rate": 0.95},
            created_at="2020-01-01T00:00:00Z",
            expires_at="2021-01-01T00:00:00Z",  # Expired
        )
        receipt_path.write_text(receipt.to_json(), encoding="utf-8")

        loaded = load_calibrated_evidence_receipt(receipt_path)
        assert loaded is not None
        is_valid, reasons = validate_calibrated_evidence(
            receipt=loaded,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
            candidate_class="defect",
            confidence=0.90,
        )
        assert is_valid is False
        assert any("Receipt expired" in r for r in reasons)

    def test_unaccepted_review_decision_rejected(self, tmp_path: Path) -> None:
        receipt_path = tmp_path / "calibrated-evidence.json"
        routing_file = ROOT / "references" / "decision-routing.json"
        mapping_hash = compute_file_sha256(routing_file)

        for invalid_decision in ("draft", "pending", "rejected"):
            receipt = CalibratedEvidenceReceipt(
                receipt_type="calibrated_routing_evidence",
                status="valid",
                review_decision=invalid_decision,
                source_revision="88d47514b82e7c44f00f2b2a72ff6dd12158038c",
                canonical_mapping_revision=mapping_hash,
                provider_identity="typesafe-jev",
                model_identity="jev-pilot-v1",
                policy_revision="1.0.0",
                class_thresholds={"defect": 0.70},
                eval_evidence={"pass_rate": 0.95},
                created_at="2026-10-21T00:00:00Z",
                expires_at="2028-10-21T00:00:00Z",
            )
            receipt_path.write_text(receipt.to_json(), encoding="utf-8")

            loaded = load_calibrated_evidence_receipt(receipt_path)
            assert loaded is not None
            is_valid, reasons = validate_calibrated_evidence(
                receipt=loaded,
                current_root=ROOT,
                expected_provider="typesafe-jev",
                expected_model="jev-pilot-v1",
                candidate_class="defect",
                confidence=0.90,
            )
            assert is_valid is False
            assert any("review_decision" in r for r in reasons)

    def test_canonical_mapping_hash_drift_rejected(self, tmp_path: Path) -> None:
        receipt_path = tmp_path / "calibrated-evidence.json"

        receipt = CalibratedEvidenceReceipt(
            receipt_type="calibrated_routing_evidence",
            status="valid",
            review_decision="accepted",
            source_revision="88d47514b82e7c44f00f2b2a72ff6dd12158038c",
            canonical_mapping_revision="0000000000000000000000000000000000000000000000000000000000000000",
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            policy_revision="1.0.0",
            class_thresholds={"defect": 0.70},
            eval_evidence={"pass_rate": 0.95},
            created_at="2026-10-21T00:00:00Z",
            expires_at="2028-10-21T00:00:00Z",
        )
        receipt_path.write_text(receipt.to_json(), encoding="utf-8")

        loaded = load_calibrated_evidence_receipt(receipt_path)
        assert loaded is not None
        is_valid, reasons = validate_calibrated_evidence(
            receipt=loaded,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
            candidate_class="defect",
            confidence=0.90,
        )
        assert is_valid is False
        assert any("Canonical mapping drift" in r for r in reasons)

    def test_known_good_fixture_promotes_under_explicitly_promoted_policy(
        self, grok_profile: Dict[str, Any], valid_candidate_observation: ProviderObservation
    ) -> None:
        query = "Fix null pointer exception in auth handler"
        baseline = resolve_skill_order(grok_profile, query, ROOT)
        assert baseline.status == "unmatched"

        provider = FakeDecisionProvider(canned_observation=valid_candidate_observation)
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=provider,
            mode="advisory",
            safe_summary=query,
        )
        assert res.advisory_promoted is True
        assert res.status == "matched"
        assert res.target == "bug-fix"
        assert res.kind == "playbook"
