#!/usr/bin/env python3
"""Tests for revision-bound evidence receipt generation and drift detection."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evidence_receipts
from scripts.evidence_receipts import (
    can_authorize_controlling_mode,
    check_receipt_staleness,
    compute_file_sha256,
    create_decision_receipt,
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


def test_worktree_digest_hashes_symlink_text_without_following_it(tmp_path: Path) -> None:
    """An untracked symlink contributes its target text, never the target's contents."""
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    link = repo / "link.txt"
    link.symlink_to(outside)

    with_link = evidence_receipts.compute_worktree_digest(repo)

    outside.write_text("rotated\n", encoding="utf-8")
    assert evidence_receipts.compute_worktree_digest(repo) == with_link

    link.unlink()
    link.symlink_to(tmp_path / "other.txt")
    assert evidence_receipts.compute_worktree_digest(repo) != with_link


def test_calibrated_evidence_receipt_post_init_sets_provenance_from_metadata() -> None:
    data = {
        "receipt_type": "calibrated_routing_evidence",
        "status": "valid",
        "review_decision": "accepted",
        "source_revision": "88d47514b82e7c44f00f2b2a72ff6dd12158038c",
        "canonical_mapping_revision": "a" * 64,
        "provider_identity": "typesafe-jev",
        "model_identity": "jev-pilot-v1",
        "policy_revision": "1.0.0",
        "class_thresholds": {"defect": 0.70},
        "eval_evidence": {"pass_rate": 0.95},
        "created_at": "2026-10-21T00:00:00Z",
        "expires_at": "2028-10-21T00:00:00Z",
        "metadata": {"provenance": {"kind": "fixture", "evaluator_run_id": "eval-1"}},
    }
    receipt = evidence_receipts.CalibratedEvidenceReceipt(**data)
    assert receipt.provenance == {"kind": "fixture", "evaluator_run_id": "eval-1"}

    loaded = evidence_receipts.CalibratedEvidenceReceipt.from_dict(data)
    assert loaded is not None
    assert loaded.provenance == {"kind": "fixture", "evaluator_run_id": "eval-1"}


def test_receipt_base_from_dict_does_not_swallow_frozen_instance_error() -> None:
    from dataclasses import dataclass, FrozenInstanceError

    @dataclass(frozen=True)
    class BuggyReceipt(evidence_receipts.ReceiptBase):
        name: str

        def __post_init__(self) -> None:
            self.name = "mutated"

    with pytest.raises(FrozenInstanceError):
        BuggyReceipt.from_dict({"name": "test"})
