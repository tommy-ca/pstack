#!/usr/bin/env python3
"""Tests for revision-bound evidence receipt generation and drift detection."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evidence_receipts import (
    can_authorize_controlling_mode,
    check_receipt_staleness,
    compute_file_sha256,
    create_decision_receipt,
    get_git_revision_and_tree,
)


class TestEvidenceReceipts:
    """Tests verifying receipt generation, hashing, and drift semantics."""

    def test_file_sha256_deterministic(self) -> None:
        routing_file = ROOT / "references" / "decision-routing.json"
        hash1 = compute_file_sha256(routing_file)
        hash2 = compute_file_sha256(routing_file)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_create_decision_receipt_binds_revisions(self) -> None:
        receipt = create_decision_receipt(
            root=ROOT,
            source="observation",
            mode="shadow",
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            outcome_status="decided",
            outcome_value="bug-fix",
            confidence=0.96,
        )

        assert receipt.source == "observation"
        assert receipt.mode == "shadow"
        assert receipt.provider_identity == "typesafe-jev"
        assert receipt.model_identity == "jev-pilot-v1"
        assert receipt.outcome_status == "decided"
        assert receipt.outcome_value == "bug-fix"
        assert len(receipt.canonical_mapping_revision) == 64
        assert len(receipt.fixture_revision) == 64

    def test_staleness_detection_clean_when_matching(self) -> None:
        receipt = create_decision_receipt(
            root=ROOT,
            source="observation",
            mode="shadow",
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            outcome_status="decided",
            outcome_value="bug-fix",
        )
        is_stale, reasons = check_receipt_staleness(
            receipt,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
        )
        assert not is_stale
        assert reasons == []

    def test_staleness_detection_flags_provider_and_model_drift(self) -> None:
        receipt = create_decision_receipt(
            root=ROOT,
            source="observation",
            mode="shadow",
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            outcome_status="decided",
        )
        is_stale, reasons = check_receipt_staleness(
            receipt,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-upgraded-v2",
        )
        assert is_stale
        assert any("Model drift" in r for r in reasons)

    def test_unknown_provider_cannot_authorize_control(self) -> None:
        receipt = create_decision_receipt(
            root=ROOT,
            source="observation",
            mode="controlling",
            provider_identity="unknown",
            model_identity="none",
            outcome_status="decided",
        )
        auth_ok, reason = can_authorize_controlling_mode(
            receipt,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
        )
        assert not auth_ok
        assert "unknown" in reason.lower() or "stale" in reason.lower()

    def test_non_decided_receipt_cannot_authorize_control(self) -> None:
        receipt = create_decision_receipt(
            root=ROOT,
            source="observation",
            mode="controlling",
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            outcome_status="abstain",
        )
        auth_ok, reason = can_authorize_controlling_mode(
            receipt,
            current_root=ROOT,
            expected_provider="typesafe-jev",
            expected_model="jev-pilot-v1",
        )
        assert not auth_ok
        assert "decided" in reason.lower()
