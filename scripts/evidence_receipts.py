#!/usr/bin/env python3
"""Revision-bound evidence receipt generation and mechanical staleness detection.

Implements Task #199 and openspec/specs/pstack-jev-decisions/spec.md requirements:
Binds decision receipts to exact pstack implementation revision, canonical tree,
canonical mapping revision, provider/model identity, policy version, and fixture digest.
Mechanically detects drift and prevents stale evidence from authorizing controlling mode.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def compute_file_sha256(path: Path) -> str:
    """Compute deterministic SHA-256 hex digest of a file."""
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def get_git_revision_and_tree(root: Path) -> Tuple[str, str]:
    """Retrieve current git commit SHA and tree SHA for repository."""
    try:
        commit_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = commit_res.stdout.strip()

        tree_res = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        tree_sha = tree_res.stdout.strip()
        return commit_sha, tree_sha
    except Exception:
        return "uncommitted-local", "uncommitted-tree"


@dataclass(frozen=True)
class DecisionReceipt:
    """Durable receipt binding a decision judgment to exact system revisions."""

    source: str  # "deterministic", "semantic_provider", "system_two", "human", "observation"
    mode: str  # "shadow", "advisory", "controlling"
    pstack_revision: str
    canonical_tree: str
    canonical_mapping_revision: str
    provider_identity: str
    model_identity: str
    policy_question_set_revision: str
    fixture_revision: str
    outcome_status: str
    outcome_value: Optional[str] = None
    confidence: Optional[float] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def create_decision_receipt(
    root: Path,
    source: str,
    mode: str,
    provider_identity: str,
    model_identity: str,
    outcome_status: str,
    outcome_value: Optional[str] = None,
    confidence: Optional[float] = None,
    policy_revision: str = "1.0.0",
    metadata: Optional[Dict[str, Any]] = None,
) -> DecisionReceipt:
    """Create a fully bound decision receipt capturing current repository state."""
    commit_sha, tree_sha = get_git_revision_and_tree(root)

    routing_file = root / "references" / "decision-routing.json"
    mapping_rev = (
        compute_file_sha256(routing_file) if routing_file.is_file() else "missing-mapping"
    )

    corpus_file = root / "tests" / "fixtures" / "decision_corpus.json"
    fixture_rev = (
        compute_file_sha256(corpus_file) if corpus_file.is_file() else "missing-fixture"
    )

    return DecisionReceipt(
        source=source,
        mode=mode,
        pstack_revision=commit_sha,
        canonical_tree=tree_sha,
        canonical_mapping_revision=mapping_rev,
        provider_identity=provider_identity,
        model_identity=model_identity,
        policy_question_set_revision=policy_revision,
        fixture_revision=fixture_rev,
        outcome_status=outcome_status,
        outcome_value=outcome_value,
        confidence=confidence,
        metadata=metadata or {},
    )


def check_receipt_staleness(
    receipt: DecisionReceipt,
    current_root: Path,
    expected_provider: Optional[str] = None,
    expected_model: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """Mechanically verify whether a receipt is stale against current environment.

    Returns (is_stale, list_of_drift_reasons).
    """
    drift_reasons: List[str] = []

    # Check provider/model validity
    if receipt.provider_identity in ("unknown", "none", ""):
        drift_reasons.append("Receipt provider_identity is unknown or empty")
    if receipt.model_identity in ("unknown", "none", ""):
        drift_reasons.append("Receipt model_identity is unknown or empty")

    if expected_provider and receipt.provider_identity != expected_provider:
        drift_reasons.append(
            f"Provider drift: receipt has '{receipt.provider_identity}' but current is '{expected_provider}'"
        )
    if expected_model and receipt.model_identity != expected_model:
        drift_reasons.append(
            f"Model drift: receipt has '{receipt.model_identity}' but current is '{expected_model}'"
        )

    # Check canonical mapping drift
    routing_file = current_root / "references" / "decision-routing.json"
    if routing_file.is_file():
        current_mapping_rev = compute_file_sha256(routing_file)
        if receipt.canonical_mapping_revision != current_mapping_rev:
            drift_reasons.append(
                f"Canonical mapping drift: receipt {receipt.canonical_mapping_revision[:8]} != current {current_mapping_rev[:8]}"
            )
    else:
        drift_reasons.append("Canonical routing file is missing")

    # Check fixture drift
    corpus_file = current_root / "tests" / "fixtures" / "decision_corpus.json"
    if corpus_file.is_file():
        current_fixture_rev = compute_file_sha256(corpus_file)
        if receipt.fixture_revision != current_fixture_rev:
            drift_reasons.append(
                f"Fixture drift: receipt {receipt.fixture_revision[:8]} != current {current_fixture_rev[:8]}"
            )

    is_stale = len(drift_reasons) > 0
    return is_stale, drift_reasons


def can_authorize_controlling_mode(
    receipt: DecisionReceipt,
    current_root: Path,
    expected_provider: str,
    expected_model: str,
) -> Tuple[bool, str]:
    """Determine if a receipt possesses fresh authority to permit controlling mode."""
    if receipt.mode != "controlling":
        return False, f"Receipt mode is '{receipt.mode}', not 'controlling'"

    is_stale, reasons = check_receipt_staleness(
        receipt,
        current_root,
        expected_provider=expected_provider,
        expected_model=expected_model,
    )
    if is_stale:
        return False, f"Receipt is stale: {'; '.join(reasons)}"

    if receipt.outcome_status != "decided":
        return False, f"Receipt outcome status is '{receipt.outcome_status}', not 'decided'"

    return True, "Authorized"
