#!/usr/bin/env python3
"""Revision-bound evidence receipt generation and mechanical staleness detection.

Implements Task #199 and openspec/specs/pstack-jev-decisions/spec.md requirements:
Binds decision receipts to exact pstack implementation revision, canonical tree,
canonical mapping revision, provider/model identity, policy version, and fixture digest.
Mechanically detects drift and prevents stale evidence from authorizing controlling mode.

Also binds change-scoped check selections (head SHA + `git patch-id` of the
merge-base..head diff + selected check outcomes) so a retargeted or reworked
patch cannot quote its previous result as current CI (#312).
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@lru_cache(maxsize=128)
def _cached_file_sha256(path_str: str) -> str:
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Compute deterministic SHA-256 hex digest of a file."""
    return _cached_file_sha256(str(path.resolve()))


@lru_cache(maxsize=32)
def _cached_git_revision_and_tree(root_str: str) -> Tuple[str, str]:
    try:
        commit_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root_str,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = commit_res.stdout.strip()

        tree_res = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=root_str,
            capture_output=True,
            text=True,
            check=True,
        )
        tree_sha = tree_res.stdout.strip()
        return commit_sha, tree_sha
    except Exception:
        return "uncommitted-local", "uncommitted-tree"


def get_git_revision_and_tree(root: Path) -> Tuple[str, str]:
    """Retrieve current git commit SHA and tree SHA for repository."""
    return _cached_git_revision_and_tree(str(root.resolve()))


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


def _git(root: Path, args: List[str], input_text: Optional[str] = None) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        input=input_text,
        check=True,
    )
    return res.stdout


def resolve_merge_base(root: Path, base: str, head: str = "HEAD") -> str:
    """Resolve the real merge base of `base` and `head`."""
    return _git(root, ["merge-base", base, head]).strip()


def resolve_revision(root: Path, ref: str = "HEAD") -> str:
    return _git(root, ["rev-parse", ref]).strip()


def compute_patch_id(root: Path, base_sha: str, head: str = "HEAD") -> str:
    """Stable `git patch-id` of the base..head diff, rebase-invariant."""
    diff = _git(root, ["diff", base_sha, head])
    out = _git(root, ["patch-id", "--stable"], input_text=diff).strip()
    if not out:
        return "empty-patch"
    return out.split()[0]


def compute_worktree_digest(root: Path) -> str:
    """Digest of the working tree: status, staged/unstaged diff, untracked content.

    The patch-id cannot see a dirty edit or a new untracked file, so a receipt
    that binds only SHAs and patch-id would fail open on exactly the state a
    selection run is recorded from. Record from a clean tree when the verdict
    should survive; any later dirty state invalidates it.
    """
    hasher = hashlib.sha256()
    status = _git(root, ["status", "--porcelain=v1", "-z", "-uall"])
    hasher.update(status.encode())
    hasher.update(_git(root, ["diff", "HEAD"]).encode())

    entries = status.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        code, rel = entry[:2], entry[3:]
        if code[0] in ("R", "C"):
            index += 1  # the following entry is the rename/copy source
        if code == "??":
            target = root / rel
            hasher.update(rel.encode())
            hasher.update(target.read_bytes() if target.is_file() else b"<missing>")
    return hasher.hexdigest()


@dataclass(frozen=True)
class CheckEvidenceReceipt:
    """Binds a selected check set and its outcomes to one exact head revision.

    `patch_id` is the stable id of the merge-base..head diff, so a pure rebase
    keeps the verdict while a retarget or a rework invalidates it. `worktree_digest`
    covers the dirty state the patch-id cannot see.
    """

    base: str
    base_sha: str
    head_sha: str
    patch_id: str
    worktree_digest: str
    check_ids: List[str]
    outcomes: Dict[str, str]
    verdict: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _reduce_outcomes(outcomes: Dict[str, str]) -> str:
    """Failure-first reduction: FAIL > BLOCKED > UNTESTED > PASS."""
    values = set(outcomes.values())
    if not values:
        return "UNTESTED"
    if "FAIL" in values:
        return "FAIL"
    if "BLOCKED" in values:
        return "BLOCKED"
    if values != {"PASS"}:
        return "UNTESTED"
    return "PASS"


def create_check_evidence_receipt(
    root: Path,
    base: str,
    check_ids: List[str],
    outcomes: Optional[Dict[str, str]] = None,
    head: str = "HEAD",
) -> CheckEvidenceReceipt:
    """Record the selected check set and its outcomes at the current head."""
    base_sha = resolve_merge_base(root, base, head)
    head_sha = resolve_revision(root, head)
    resolved_outcomes = {cid: outcomes.get(cid, "UNTESTED") for cid in check_ids} if outcomes else {}
    return CheckEvidenceReceipt(
        base=base,
        base_sha=base_sha,
        head_sha=head_sha,
        patch_id=compute_patch_id(root, base_sha, head),
        worktree_digest=compute_worktree_digest(root),
        check_ids=list(check_ids),
        outcomes=resolved_outcomes,
        verdict=_reduce_outcomes(resolved_outcomes),
    )


def load_check_evidence_receipt(path: Path) -> CheckEvidenceReceipt:
    return CheckEvidenceReceipt(**json.loads(path.read_text(encoding="utf-8")))


def check_check_evidence_staleness(
    receipt: CheckEvidenceReceipt,
    root: Path,
    base: Optional[str] = None,
    head: str = "HEAD",
) -> Tuple[bool, List[str]]:
    """Is the recorded check verdict still bound to the current patch?

    A moved head with an identical patch-id (pure rebase) stays valid. A changed
    patch-id — a retarget, a rework, or a reverted commit — invalidates it.
    """
    reasons: List[str] = []
    current_base_sha = resolve_merge_base(root, base or receipt.base, head)
    current_head_sha = resolve_revision(root, head)
    current_patch_id = compute_patch_id(root, current_base_sha, head)

    if receipt.patch_id != current_patch_id:
        reasons.append(
            f"Patch drift: receipt {receipt.patch_id[:8]} != current {current_patch_id[:8]}"
        )
    if receipt.head_sha != current_head_sha:
        reasons.append(
            f"Head moved: receipt {receipt.head_sha[:8]} != current {current_head_sha[:8]}"
        )
    if receipt.head_sha != current_head_sha and receipt.patch_id == current_patch_id:
        # Documented rebase case: SHAs are rewritten, the patch is identical.
        reasons = [r for r in reasons if not r.startswith("Head moved")]

    if receipt.worktree_digest != compute_worktree_digest(root):
        reasons.append("Worktree changed since recording")

    return bool(reasons), reasons


def can_claim_current_ci(
    receipt: CheckEvidenceReceipt,
    root: Path,
    base: Optional[str] = None,
    head: str = "HEAD",
) -> Tuple[bool, str]:
    """May the recorded result be quoted as the *current* CI/check state?"""
    is_stale, reasons = check_check_evidence_staleness(receipt, root, base=base, head=head)
    if is_stale:
        return False, f"Recorded evidence is stale: {'; '.join(reasons)}"
    if receipt.verdict != "PASS":
        return False, f"Recorded verdict at {receipt.head_sha[:8]} is {receipt.verdict}"
    return True, f"Current at {receipt.head_sha[:8]} (patch-id {receipt.patch_id[:8]})"
