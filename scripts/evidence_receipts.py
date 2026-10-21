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
import os
import stat
import subprocess
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T", bound="ReceiptBase")


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


class ReceiptBase:
    """Standardized serialization and safe deserialization for revision-bound receipts."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> Optional[T]:
        """Safely instantiate dataclass from dict, ignoring extraneous keys."""
        if not isinstance(data, dict):
            return None
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        try:
            return cls(**filtered)
        except Exception:
            return None

    @classmethod
    def load(cls: Type[T], path: Optional[Union[Path, str]]) -> Optional[T]:
        """Load and parse receipt from a JSON file path."""
        if path is None:
            return None
        p = Path(path)
        if not p.is_file():
            return None
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            return cls.from_dict(raw)
        except Exception:
            return None


@dataclass(frozen=True)
class DecisionReceipt(ReceiptBase):
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


@dataclass(frozen=True)
class CalibratedEvidenceReceipt(ReceiptBase):
    """Separately persisted, pre-existing calibrated evidence receipt required for route promotion (#659, #676)."""

    receipt_type: str  # "calibrated_routing_evidence"
    status: str  # "valid" or "specimen_fixture"
    review_decision: str  # "accepted", "promoted", or "specimen_fixture"
    source_revision: str  # upstream canonical pin or git commit
    canonical_mapping_revision: str  # sha256 of references/decision-routing.json
    provider_identity: str
    model_identity: str
    policy_revision: str
    class_thresholds: Dict[str, float]
    eval_evidence: Dict[str, Any]
    created_at: str
    expires_at: str
    provenance: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def load_calibrated_evidence_receipt(path: Optional[Union[Path, str]]) -> Optional[CalibratedEvidenceReceipt]:
    """Safely load and parse a persisted CalibratedEvidenceReceipt from disk."""
    return CalibratedEvidenceReceipt.load(path)


def validate_calibrated_evidence(
    receipt: CalibratedEvidenceReceipt,
    current_root: Path,
    expected_provider: str,
    expected_model: str,
    candidate_class: str,
    confidence: float,
    allow_fixture: bool = False,
) -> Tuple[bool, List[str]]:
    """Mechanically validate a persisted calibrated evidence receipt for advisory route promotion (#659, #676).

    Enforces:
    1. Valid receipt_type ('calibrated_routing_evidence')
    2. Distinction between specimen fixture and promoted provenance receipt (#676):
       - Specimen fixtures (status='specimen_fixture' or review_decision='specimen_fixture')
         require explicit allow_fixture=True (or PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE=1)
         and cannot authorize live advisory promotion by default.
       - Promoted receipts require immutable evaluator_run_id, reviewer_identity, and dataset_digest.
    3. Positive match against expected provider and model identity snapshots
    4. Exact match of canonical mapping revision against current references/decision-routing.json
    5. Receipt freshness: must not be expired relative to current UTC time
    6. Non-empty evaluation evidence payload with performance indicators
    7. Calibrated per-class threshold satisfied by confidence
    """
    reasons: List[str] = []

    if os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE") == "1":
        allow_fixture = True

    if receipt.receipt_type != "calibrated_routing_evidence":
        reasons.append(
            f"Invalid receipt_type: '{receipt.receipt_type}' (expected 'calibrated_routing_evidence')"
        )

    is_fixture = (
        receipt.status == "specimen_fixture"
        or receipt.review_decision == "specimen_fixture"
        or (isinstance(receipt.provenance, dict) and receipt.provenance.get("kind") == "fixture")
        or receipt.metadata.get("is_specimen_fixture") is True
    )

    if is_fixture and not allow_fixture:
        reasons.append(
            "Checked-in specimen fixture cannot authorize live advisory promotion without independent provenance"
        )
    elif not is_fixture:
        if receipt.status != "valid":
            reasons.append(f"Receipt status is '{receipt.status}', not 'valid'")

        if receipt.review_decision not in ("accepted", "promoted"):
            reasons.append(
                f"Receipt review_decision is '{receipt.review_decision}', not 'accepted' or 'promoted'"
            )

        prov = receipt.provenance or receipt.metadata.get("provenance")
        if not isinstance(prov, dict):
            reasons.append("Receipt lacks required provenance metadata for live promotion")
        else:
            run_id = str(prov.get("evaluator_run_id", "")).strip()
            reviewer = str(prov.get("reviewer", "")).strip()
            digest = str(prov.get("dataset_digest", "")).strip()

            if not run_id or (run_id.startswith("fixture:") and not allow_fixture):
                reasons.append(f"Invalid or synthetic evaluator_run_id: '{run_id}'")
            if not reviewer or reviewer.lower() in ("unverified", "none", "placeholder", "unknown"):
                reasons.append(f"Unverified reviewer identity: '{reviewer}'")
            if not digest or len(digest) < 16:
                reasons.append("Missing or invalid dataset immutable digest in provenance")

    if not receipt.provider_identity or receipt.provider_identity != expected_provider:
        reasons.append(
            f"Provider mismatch: receipt has '{receipt.provider_identity}', expected '{expected_provider}'"
        )

    if not receipt.model_identity or receipt.model_identity != expected_model:
        reasons.append(
            f"Model mismatch: receipt has '{receipt.model_identity}', expected '{expected_model}'"
        )

    routing_file = current_root / "references" / "decision-routing.json"
    if not routing_file.is_file():
        reasons.append("Canonical routing file references/decision-routing.json is missing")
    else:
        current_mapping_rev = compute_file_sha256(routing_file)
        if receipt.canonical_mapping_revision != current_mapping_rev:
            reasons.append(
                f"Canonical mapping drift: receipt {receipt.canonical_mapping_revision[:8]} != current {current_mapping_rev[:8]}"
            )

    try:
        raw_exp = receipt.expires_at.replace("Z", "+00:00")
        expires_dt = datetime.fromisoformat(raw_exp)
        now_dt = datetime.now(timezone.utc)
        if expires_dt <= now_dt:
            reasons.append(f"Receipt expired at {receipt.expires_at}")
    except Exception as exc:
        reasons.append(f"Invalid or unparseable expires_at timestamp: {exc}")

    if not receipt.eval_evidence:
        reasons.append("Receipt contains no eval_evidence holdout metrics")

    if candidate_class not in receipt.class_thresholds:
        reasons.append(f"Class '{candidate_class}' has no calibrated threshold in receipt")
    else:
        threshold = float(receipt.class_thresholds[candidate_class])
        if confidence < threshold:
            reasons.append(
                f"Confidence {confidence:.2f} below calibrated threshold {threshold:.2f} for class '{candidate_class}'"
            )

    is_valid = len(reasons) == 0
    return is_valid, reasons


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
            # lstat, never stat: an untracked symlink must contribute its target text,
            # not the contents of whatever it points at outside the tree.
            try:
                info = target.lstat()
            except OSError:
                hasher.update(b"<missing>")
                continue
            if stat.S_ISLNK(info.st_mode):
                hasher.update(b"<symlink>")
                hasher.update(os.readlink(target).encode())
            elif stat.S_ISREG(info.st_mode):
                hasher.update(target.read_bytes())
            else:
                hasher.update(b"<special>")
    return hasher.hexdigest()


@dataclass(frozen=True)
class CheckEvidenceReceipt(ReceiptBase):
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


def _reduce_outcomes(outcomes: Dict[str, str]) -> str:
    """Failure-first reduction: FAIL > BLOCKED > UNTESTED > PASS.

    Single lattice lives in scripts/verify-portable.py::reduce_verdicts;
    this keeps the Dict[str, str] receipt boundary and passes values.
    """
    import importlib

    lattice = importlib.import_module("scripts.verify-portable").reduce_verdicts
    return lattice(outcomes.values())


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


def load_check_evidence_receipt(path: Union[Path, str]) -> CheckEvidenceReceipt:
    receipt = CheckEvidenceReceipt.load(path)
    if receipt is None:
        raise ValueError(f"Failed to load CheckEvidenceReceipt from {path}")
    return receipt


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
    """May the recorded result be quoted as the *current* CI/check state?

    A yes names the head it is current *at*, and only that head. A pure rebase
    rewrites the receipt's SHA while keeping the patch, so the receipt SHA alone
    would name a head that no longer exists; the claim then carries the recheck
    the operator still owes: the checks re-run at the current head against the
    current base.
    """
    is_stale, reasons = check_check_evidence_staleness(receipt, root, base=base, head=head)
    if is_stale:
        return False, f"Recorded evidence is stale: {'; '.join(reasons)}"
    if receipt.verdict != "PASS":
        return False, f"Recorded verdict at {receipt.head_sha[:8]} is {receipt.verdict}"
    current_head_sha = resolve_revision(root, head)
    claim = f"Current at {current_head_sha[:8]} (patch-id {receipt.patch_id[:8]})"
    if current_head_sha != receipt.head_sha:
        current_base_sha = resolve_merge_base(root, base or receipt.base, head)
        claim += (
            f"; rebased from {receipt.head_sha[:8]}, so re-run the checks at "
            f"{current_head_sha[:8]} against base {current_base_sha[:8]}"
        )
    return True, claim
