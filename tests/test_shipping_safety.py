"""Safety gates and delivery ordering invariants for shipping and autopilot playbooks (#627).

Validates:
1. Frozen exact-head candidates and patch-id preservation.
2. Independent per-PR verdicts (author cannot verify self; CI green or bot approval is not a verdict).
3. Contiguous verified stack (landing stops at the first unverified gap).
4. No unapproved apply/merge (gated on verified head).
5. Stale CI / moved head invalidation unless patch-id matches or diff is verified build noise only.
6. Overnight run persisted then scheduled via host-native mechanisms without Cursor /loop leaks.
7. Acceptance examples: red check, stale verdict, head moved, dropped reviewer, closed/merged PR,
   missing native host, cancellation, and dirty worktree.
8. Rejection of false shipping PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS_DIR = ROOT / "skills" / "poteto-mode" / "playbooks"


@dataclass(frozen=True)
class CandidatePR:
    number: int
    branch: str
    base: str
    head_sha: str
    patch_id: str
    ci_status: str  # "success" | "failure" | "pending"
    state: str  # "open" | "closed" | "merged"
    verdict: str | None  # "PASS" | "PASS+NOTES" | "FAIL" | None
    verdict_head_sha: str | None
    verdict_patch_id: str | None
    verdict_author: str | None
    pr_author: str
    is_dropped: bool = False
    is_cancelled: bool = False
    build_noise_only: bool = False


@dataclass(frozen=True)
class ShippingEvaluation:
    is_landable: bool
    status: str  # "PASS" | "BLOCKED" | "DROPOUT" | "GAP"
    reason: str


def evaluate_pr_verdict(
    pr: CandidatePR,
    host_has_scheduler: bool = True,
    worktree_clean: bool = True,
) -> ShippingEvaluation:
    """Evaluate whether a PR candidate is safe to land according to shipping.md safety gates."""
    if not worktree_clean:
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason="Dirty worktree: uncommitted edits in working tree halt landing",
        )

    if pr.is_cancelled:
        return ShippingEvaluation(
            is_landable=False,
            status="DROPOUT",
            reason="Cancellation: lane was cancelled by operator and settles as dropout",
        )

    if pr.is_dropped:
        return ShippingEvaluation(
            is_landable=False,
            status="DROPOUT",
            reason="Dropout: reviewer dropped out or timed out, never a pass",
        )

    if pr.state != "open":
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason=f"Closed or merged PR: state is {pr.state!r}, cannot land",
        )

    if pr.verdict is None:
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason="Missing verdict: no independent verifier report",
        )

    if pr.verdict not in ("PASS", "PASS+NOTES"):
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason=f"Verdict is {pr.verdict!r}, expected PASS or PASS+NOTES",
        )

    if pr.verdict_author and pr.verdict_author == pr.pr_author:
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason="Author self-verdict: author cannot verify own code",
        )

    if pr.ci_status != "success":
        return ShippingEvaluation(
            is_landable=False,
            status="BLOCKED",
            reason=f"Red check: CI status is {pr.ci_status!r}",
        )

    # Check exact-head or patch-id preservation
    if pr.verdict_head_sha != pr.head_sha:
        if pr.verdict_patch_id == pr.patch_id:
            # Rebase preserved the patch exactly
            pass
        elif pr.build_noise_only:
            # Difference is verified build noise / embedded commit SHA only
            pass
        else:
            return ShippingEvaluation(
                is_landable=False,
                status="BLOCKED",
                reason=(
                    f"Stale verdict: head moved ({pr.verdict_head_sha} -> {pr.head_sha}) "
                    f"and patch changed ({pr.verdict_patch_id} -> {pr.patch_id}) without verified build noise"
                ),
            )

    if not host_has_scheduler:
        return ShippingEvaluation(
            is_landable=False,
            status="GAP",
            reason="Missing native host: runtime lacks background scheduler/monitor capability",
        )

    return ShippingEvaluation(
        is_landable=True,
        status="PASS",
        reason="Verified and landable: independent verdict, green CI, matching patch-id",
    )


def evaluate_stack(
    stack: list[CandidatePR],
    host_has_scheduler: bool = True,
    worktree_clean: bool = True,
) -> tuple[list[CandidatePR], CandidatePR | None, str]:
    """Evaluate a bottom-up stack and find the contiguous verified run and ceiling."""
    verified_run: list[CandidatePR] = []
    for pr in stack:
        eval_result = evaluate_pr_verdict(
            pr,
            host_has_scheduler=host_has_scheduler,
            worktree_clean=worktree_clean,
        )
        if not eval_result.is_landable:
            return verified_run, pr, eval_result.reason
        verified_run.append(pr)
    return verified_run, None, "Complete verified run"


# --- Acceptance Tests Covering 8 Negative Scenarios ---------------------------

def test_shipping_rejects_red_check() -> None:
    pr = CandidatePR(
        number=101,
        branch="feat/1",
        base="main",
        head_sha="aaa111",
        patch_id="pid111",
        ci_status="failure",
        state="open",
        verdict="PASS",
        verdict_head_sha="aaa111",
        verdict_patch_id="pid111",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result = evaluate_pr_verdict(pr)
    assert not result.is_landable
    assert result.status == "BLOCKED"
    assert "Red check" in result.reason


def test_shipping_rejects_stale_verdict_when_head_moved_and_patch_changed() -> None:
    pr = CandidatePR(
        number=102,
        branch="feat/2",
        base="main",
        head_sha="bbb222",
        patch_id="pid222_changed",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="bbb111",
        verdict_patch_id="pid222_original",
        verdict_author="independent-verifier",
        pr_author="author-worker",
        build_noise_only=False,
    )
    result = evaluate_pr_verdict(pr)
    assert not result.is_landable
    assert result.status == "BLOCKED"
    assert "Stale verdict" in result.reason


def test_shipping_accepts_head_moved_with_identical_patch_id() -> None:
    pr = CandidatePR(
        number=103,
        branch="feat/3",
        base="main",
        head_sha="ccc222",
        patch_id="pid333_constant",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="ccc111",
        verdict_patch_id="pid333_constant",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result = evaluate_pr_verdict(pr)
    assert result.is_landable
    assert result.status == "PASS"


def test_shipping_accepts_head_moved_with_verified_build_noise_only() -> None:
    pr = CandidatePR(
        number=104,
        branch="feat/4",
        base="main",
        head_sha="ddd222",
        patch_id="pid444_comment_diff",
        ci_status="success",
        state="open",
        verdict="PASS+NOTES",
        verdict_head_sha="ddd111",
        verdict_patch_id="pid444_base",
        verdict_author="independent-verifier",
        pr_author="author-worker",
        build_noise_only=True,
    )
    result = evaluate_pr_verdict(pr)
    assert result.is_landable
    assert result.status == "PASS"


def test_shipping_rejects_dropped_reviewer_as_pass() -> None:
    pr = CandidatePR(
        number=105,
        branch="feat/5",
        base="main",
        head_sha="eee111",
        patch_id="pid555",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="eee111",
        verdict_patch_id="pid555",
        verdict_author="independent-verifier",
        pr_author="author-worker",
        is_dropped=True,
    )
    result = evaluate_pr_verdict(pr)
    assert not result.is_landable
    assert result.status == "DROPOUT"
    assert "Dropout" in result.reason


def test_shipping_rejects_cancelled_lane_as_pass() -> None:
    pr = CandidatePR(
        number=106,
        branch="feat/6",
        base="main",
        head_sha="fff111",
        patch_id="pid666",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="fff111",
        verdict_patch_id="pid666",
        verdict_author="independent-verifier",
        pr_author="author-worker",
        is_cancelled=True,
    )
    result = evaluate_pr_verdict(pr)
    assert not result.is_landable
    assert result.status == "DROPOUT"
    assert "Cancellation" in result.reason


def test_shipping_rejects_closed_or_merged_pr() -> None:
    pr_closed = CandidatePR(
        number=107,
        branch="feat/7",
        base="main",
        head_sha="ggg111",
        patch_id="pid777",
        ci_status="success",
        state="closed",
        verdict="PASS",
        verdict_head_sha="ggg111",
        verdict_patch_id="pid777",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result_closed = evaluate_pr_verdict(pr_closed)
    assert not result_closed.is_landable
    assert result_closed.status == "BLOCKED"
    assert "Closed or merged PR" in result_closed.reason

    pr_merged = CandidatePR(
        number=108,
        branch="feat/8",
        base="main",
        head_sha="hhh111",
        patch_id="pid888",
        ci_status="success",
        state="merged",
        verdict="PASS",
        verdict_head_sha="hhh111",
        verdict_patch_id="pid888",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result_merged = evaluate_pr_verdict(pr_merged)
    assert not result_merged.is_landable
    assert result_merged.status == "BLOCKED"


def test_shipping_rejects_missing_native_host_background_claim() -> None:
    pr = CandidatePR(
        number=109,
        branch="feat/9",
        base="main",
        head_sha="iii111",
        patch_id="pid999",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="iii111",
        verdict_patch_id="pid999",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result = evaluate_pr_verdict(pr, host_has_scheduler=False)
    assert not result.is_landable
    assert result.status == "GAP"
    assert "Missing native host" in result.reason


def test_shipping_rejects_dirty_worktree() -> None:
    pr = CandidatePR(
        number=110,
        branch="feat/10",
        base="main",
        head_sha="jjj111",
        patch_id="pid1010",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="jjj111",
        verdict_patch_id="pid1010",
        verdict_author="independent-verifier",
        pr_author="author-worker",
    )
    result = evaluate_pr_verdict(pr, worktree_clean=False)
    assert not result.is_landable
    assert result.status == "BLOCKED"
    assert "Dirty worktree" in result.reason


def test_shipping_rejects_author_self_verdict() -> None:
    pr = CandidatePR(
        number=111,
        branch="feat/11",
        base="main",
        head_sha="kkk111",
        patch_id="pid1111",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="kkk111",
        verdict_patch_id="pid1111",
        verdict_author="author-worker",
        pr_author="author-worker",
    )
    result = evaluate_pr_verdict(pr)
    assert not result.is_landable
    assert result.status == "BLOCKED"
    assert "Author self-verdict" in result.reason


def test_contiguous_stack_stops_at_unverified_gap() -> None:
    pr1 = CandidatePR(
        number=1,
        branch="feat/1",
        base="main",
        head_sha="sha1",
        patch_id="pid1",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="sha1",
        verdict_patch_id="pid1",
        verdict_author="independent-verifier",
        pr_author="author1",
    )
    pr2 = CandidatePR(
        number=2,
        branch="feat/2",
        base="feat/1",
        head_sha="sha2",
        patch_id="pid2",
        ci_status="pending",  # Unverified / not green
        state="open",
        verdict=None,
        verdict_head_sha=None,
        verdict_patch_id=None,
        verdict_author=None,
        pr_author="author2",
    )
    pr3 = CandidatePR(
        number=3,
        branch="feat/3",
        base="feat/2",
        head_sha="sha3",
        patch_id="pid3",
        ci_status="success",
        state="open",
        verdict="PASS",
        verdict_head_sha="sha3",
        verdict_patch_id="pid3",
        verdict_author="independent-verifier",
        pr_author="author3",
    )
    verified_run, ceiling_pr, reason = evaluate_stack([pr1, pr2, pr3])
    assert len(verified_run) == 1
    assert verified_run[0].number == 1
    assert ceiling_pr is not None
    assert ceiling_pr.number == 2
    assert "Missing verdict" in reason


# --- Playbook Invariants and Host-Neutral Contracts ---------------------------

def test_shipping_playbook_invariants() -> None:
    shipping_path = PLAYBOOKS_DIR / "shipping.md"
    assert shipping_path.is_file()
    text = shipping_path.read_text(encoding="utf-8")

    # Condensed 6-step flow
    for step_num in range(1, 7):
        assert f"{step_num}. **" in text, f"shipping.md missing step {step_num}"

    # Independent verifier requirement (different model family from author)
    assert "pstack:independent-verifier" in text
    assert "agent that did not write the code" in text
    assert "Green CI and an approving bot review are not verdicts" in text

    # Contiguous verified run rooted at bottom
    assert "Land only the contiguous verified run rooted at the bottom" in text
    assert "stop at the first one without `PASS` or `PASS+NOTES`" in text

    # Patch-id and build noise rules
    assert "git patch-id" in text
    assert "builds the same at both SHAs apart from noise" in text
    assert "Noise is a difference that also shows up between two builds of the verdict SHA" in text

    # Bottom-up landing with forge commands
    assert "Land bottom-up, one PR at a time" in text
    assert "origin pr merge <pr>" in text
    assert "gh pr merge <pr> --squash" in text
    assert "retarget the PR whose base was the merged branch to trunk" in text

    # Host-neutral monitor / schedule
    assert "host `monitor` or `schedule` capability" in text
    assert "/loop" not in text

    # No Graphite requirement
    assert "Never require Graphite (`gt`)" in text


def test_autopilot_full_playbook_invariants() -> None:
    autopilot_path = PLAYBOOKS_DIR / "autopilot-full.md"
    assert autopilot_path.is_file()
    text = autopilot_path.read_text(encoding="utf-8")

    # One owner per PR
    assert "Spawn one owner per PR with the full lifecycle" in text
    assert "show-me-your-work" in text
    assert "children.tsv" in text

    # Swarm-verify once rule
    assert "Swarm-verify once" in text
    assert "A full swarm runs once, at the code-ready head" in text
    assert "A rebase, a merge-conflict resolution, or a minor fix gets a single verifier" in text

    # Lockfile and caller/dependency checks on merge result
    assert "A lockfile both sides changed needs no rebase when a frozen install passes" in text

    # 1-hour audit tick and ketchup catchup
    assert "host's schedule capability" in text
    assert "ketchup" in text
    assert "Replace a stuck agent at once" in text


def test_autopilot_stack_playbook_invariants() -> None:
    stack_path = PLAYBOOKS_DIR / "autopilot-stack.md"
    assert stack_path.is_file()
    text = stack_path.read_text(encoding="utf-8")

    # Single writer on topology
    assert "Give the topology one writer" in text
    assert "Never require `gt`" in text
    assert "origin pr edit <pr> --base <parent-branch>" in text
    assert "gh pr edit <pr> --base <parent-branch>" in text

    # Hands off during landing
    assert "Deliver the chain, then keep your hands off it" in text
    assert "ketchup" in text
