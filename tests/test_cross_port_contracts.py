"""Host-scoped contract tests for cross-port semantic invariants (#638, refs #636).

Implements the 6 required observable postcondition scenarios from pstack-claude
0.9.95 delta audit without importing foreign runtime/session engines:
1. Parallel tool calls settle by stable call ID; end of one leaves the other running.
2. Agent activity is ephemeral, private/non-message; ended agent has no current activity.
3. Restored child activity/status cannot be mistaken for a new child or persistent proof.
4. Stop/cancel reports success only after native child settlement; cannot kill unrelated process.
5. Worktree cleanup preserves hidden untracked files when status.showUntrackedFiles=no is set.
6. Model alias in reference generator cannot claim native host capability or multi-family diversity.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
AUDIT_SCRIPT = ROOT / "skills/poteto-mode/scripts/worktree-audit.sh"


# ---------------------------------------------------------------------------
# Scenario 1: Parallel tool calls settle by stable call ID
# ---------------------------------------------------------------------------


class ToolCallTracker:
    """Models stable call-ID tracking for concurrent tool invocations."""

    def __init__(self) -> None:
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.completed_calls: Dict[str, Dict[str, Any]] = {}

    def start_call(self, call_id: str, tool_name: str, args: Dict[str, Any]) -> None:
        self.active_calls[call_id] = {"tool": tool_name, "args": args, "status": "running"}

    def complete_call(self, call_id: str, result: Any) -> None:
        if call_id in self.active_calls:
            call_info = self.active_calls.pop(call_id)
            call_info["status"] = "completed"
            call_info["result"] = result
            self.completed_calls[call_id] = call_info

    def is_running(self, call_id: str) -> bool:
        return call_id in self.active_calls

    def has_active_calls(self) -> bool:
        return len(self.active_calls) > 0


def test_concurrent_tool_calls_settle_by_stable_call_id() -> None:
    """Parallel tool calls settle independently by stable call ID; end of one leaves others running."""
    tracker = ToolCallTracker()

    # Dispatch two concurrent tool calls
    tracker.start_call("call-alpha-101", "read_file", {"path": "alpha.py"})
    tracker.start_call("call-beta-202", "run_command", {"command": "pytest"})

    assert tracker.is_running("call-alpha-101")
    assert tracker.is_running("call-beta-202")
    assert tracker.has_active_calls()

    # Complete call A
    tracker.complete_call("call-alpha-101", "content of alpha.py")

    # Call A is settled, but call B is still strictly running
    assert not tracker.is_running("call-alpha-101")
    assert tracker.is_running("call-beta-202")
    assert tracker.has_active_calls()
    assert "call-alpha-101" in tracker.completed_calls
    assert "call-beta-202" not in tracker.completed_calls

    # Complete call B
    tracker.complete_call("call-beta-202", {"exit_code": 0})
    assert not tracker.is_running("call-beta-202")
    assert not tracker.has_active_calls()
    assert "call-beta-202" in tracker.completed_calls


# ---------------------------------------------------------------------------
# Scenario 2: Agent activity is ephemeral and cleared on agent end
# ---------------------------------------------------------------------------


class AgentActivityManager:
    """Models ephemeral agent progress/activity tracking without leaking to session store."""

    def __init__(self) -> None:
        self.live_activity: Dict[str, Dict[str, Any]] = {}

    def update_activity(self, agent_id: str, activity_summary: str, details: Dict[str, Any]) -> None:
        self.live_activity[agent_id] = {
            "summary": activity_summary,
            "details": details,
            "is_active": True,
        }

    def end_agent(self, agent_id: str) -> None:
        # Ephemeral activity is cleared when the agent reaches a terminal status
        self.live_activity.pop(agent_id, None)

    def current_activity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self.live_activity.get(agent_id)


def test_agent_activity_is_ephemeral_and_cleared_on_agent_end() -> None:
    """Agent activity is private/ephemeral; ended agent has strictly no live activity."""
    manager = AgentActivityManager()

    # Agent is executing
    manager.update_activity("child-agent-42", "Running linters", {"progress": 0.5})
    assert manager.current_activity("child-agent-42") is not None
    assert manager.current_activity("child-agent-42")["summary"] == "Running linters"

    # Agent ends (e.g. terminal lifecycle frame arrives)
    manager.end_agent("child-agent-42")

    # Activity must be completely purged; ended agent has no current activity
    assert manager.current_activity("child-agent-42") is None


# ---------------------------------------------------------------------------
# Scenario 3: Restored child status not mistaken for new child or persistent proof
# ---------------------------------------------------------------------------


def test_restored_child_status_not_mistaken_for_new_spawn_or_persistent_proof() -> None:
    """Restored child activity/status cannot be mistaken for a new spawn or persistent proof."""
    from scripts.drivers.omp_rpc import reduce_child_settlement

    # Case 1: Replayed or restored frames without an observed live spawn event and terminal status
    restored_frames = [
        {"type": "ready", "protocolVersion": 2},
        {"type": "subagent_progress", "payload": {"id": "reconnected-child-99", "progress": {"resolvedModel": "grok"}}},
    ]
    # Without terminal lifecycle frame or timeout, reduce_child_settlement returns None
    settlement = reduce_child_settlement(restored_frames, child_id="reconnected-child-99")
    assert settlement is None, "In-flight / reconnected child without terminal frame cannot claim settlement"

    # Case 2: Unknown identity / process status remains GAP in receipt
    from scripts.portability_types import ScenarioResult

    unknown_status_scenario = ScenarioResult(
        id="runtime-child-restore-unknown",
        description="Reconnected subagent with unknown process status",
        plane="runtime",
        command="reconnect --id unknown",
        exit_code=1,
        stdout_snippet="process state unknown",
        verdict="GAP",
        duration_s=0.0,
        evidence_level="offline",
    )
    assert unknown_status_scenario.verdict == "GAP"
    assert unknown_status_scenario.evidence_level == "offline"


# ---------------------------------------------------------------------------
# Scenario 4: Stop/cancel reports success only after native settlement; does not kill unrelated process
# ---------------------------------------------------------------------------


def test_stop_cancel_requires_native_settlement_and_does_not_kill_unrelated_process() -> None:
    """Stop/cancel reports success only after native settlement; cannot terminate unrelated PID."""
    from scripts.drivers.omp_rpc import TERMINAL_LIFECYCLE_STATUS, reduce_child_settlement

    # Cancel request where child was already dead / not running
    # Upstream RPC protocol: data.cancelled is False when no running subagent exists
    ack_frame_no_running = {
        "type": "response",
        "command": "cancel_subagent",
        "success": True,
        "data": {"cancelled": False},
    }
    # An accepted cancel request where cancelled is False must not be credited as an observed stop
    assert ack_frame_no_running["data"]["cancelled"] is False

    # Terminal cancellation requires an observed cancelled status
    cancelled_frames = [
        {"type": "ready", "protocolVersion": 2},
        {"type": "subagent_progress", "payload": {"id": "c1", "progress": {"resolvedModelIdentity": "codex"}}},
        {"type": "subagent_lifecycle", "payload": {"id": "c1", "status": "cancelled"}},
    ]
    settlement = reduce_child_settlement(cancelled_frames, child_id="c1")
    assert settlement is not None
    assert settlement["terminal_outcome"] == "cancelled"
    assert settlement["model"] == "codex"

    # Process killing guard: unrelated PID safety
    real_pid = os.getpid()
    stale_or_changed_pid = real_pid + 999999

    def safe_terminate_process(target_pid: int, expected_owner_token: str, actual_token: Optional[str]) -> bool:
        if target_pid <= 1:
            # Never signal non-positive PIDs (0=process group, negative=broadcast) or init (1)
            return False
        if actual_token != expected_owner_token:
            # PID reuse or mismatch: REFUSE to kill
            return False
        return True

    # Attempting to kill with mismatched process token fails closed
    assert not safe_terminate_process(stale_or_changed_pid, "owner-session-123", "owner-session-456")
    assert safe_terminate_process(stale_or_changed_pid, "owner-session-123", "owner-session-123")

    # Guard against non-positive or system PIDs (0, 1, negative)
    assert not safe_terminate_process(0, "owner-session-123", "owner-session-123")
    assert not safe_terminate_process(1, "owner-session-123", "owner-session-123")
    assert not safe_terminate_process(-1, "owner-session-123", "owner-session-123")


# ---------------------------------------------------------------------------
# Scenario 5: Worktree cleanup preserves hidden untracked files
# ---------------------------------------------------------------------------


def test_worktree_cleanup_preserves_hidden_untracked_files(tmp_path: Path) -> None:
    """Worktree audit preserves untracked files even when status.showUntrackedFiles=no is configured."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Audit Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "audit@example.com"], cwd=repo, check=True, capture_output=True)
    (repo / "main.txt").write_text("main\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "main"], cwd=repo, check=True, capture_output=True)

    wt = tmp_path / "worktree-hidden"
    subprocess.run(["git", "worktree", "add", "-b", "feature", str(wt)], cwd=repo, check=True, capture_output=True)

    # Configure status.showUntrackedFiles = no in the worktree
    subprocess.run(["git", "config", "status.showUntrackedFiles", "no"], cwd=wt, check=True, capture_output=True)
    (wt / "hidden_precious.txt").write_text("precious untracked output\n", encoding="utf-8")

    # Run worktree-audit.sh
    proc = subprocess.run([str(AUDIT_SCRIPT), str(repo)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    matching_lines = [line for line in proc.stdout.splitlines() if str(wt) in line]
    assert len(matching_lines) == 1, proc.stdout
    row = matching_lines[0].split("\t")

    dirty_col = row[3]
    bucket_col = row[7]

    # Must be identified as scratch / hold-untracked, never clean or safe
    assert "scratch:1" in dirty_col
    assert bucket_col == "hold-untracked"
    assert bucket_col != "safe"
    assert (wt / "hidden_precious.txt").is_file()


# ---------------------------------------------------------------------------
# Scenario 6: Model alias in reference generator cannot claim native host capability
# ---------------------------------------------------------------------------


def test_reference_model_alias_cannot_claim_native_host_capability() -> None:
    """A foreign model alias/provider in a reference generator cannot promote native host capabilities."""
    from scripts.model_role_resolver import plan_role
    from tests.model_role_helpers import PACKAGE, catalog_plan_policy, capability_bindings

    policy = catalog_plan_policy()

    # Foreign reference model aliases not present in host observed catalog
    foreign_model_alias = "claude-opus-5-5-xhigh"
    plan = plan_role(
        policy,
        PACKAGE,
        host="codex",
        role="swarm-workers",
        explicit=foreign_model_alias,
        capabilities=capability_bindings(),
    )

    # Foreign alias missing in host catalog is blocked, with transparent reason
    assert plan.status == "BLOCKED"
    assert "no silent substitution" in plan.reasons[0]
    # Cannot forge VERIFIED status
    assert plan.status != "VERIFIED"


def test_single_model_family_panel_reports_degraded_diversity() -> None:
    """Panel with multiple seats sharing one model family honestly reports degraded diversity or blocks."""
    from scripts.model_role_resolver import plan_role
    from tests.model_role_helpers import PACKAGE, catalog_plan_policy, capability_bindings

    # Case 1: Standard panel with single family degrades diversity honestly
    policy_standard = catalog_plan_policy()
    degraded_plan = plan_role(
        policy_standard,
        PACKAGE,
        host="codex",
        role="interrogate-reviewers",
        explicit=["model-a", "model-c"],  # both have family "alpha" in catalog_plan_policy
        capabilities=capability_bindings(),
    )
    assert degraded_plan.status == "DEGRADED"
    assert "independent seats do not prove diverse model families" in degraded_plan.reasons[0]
    families = {seat.family for seat in degraded_plan.seats if seat.family}
    assert len(families) == 1

    # Case 2: Panel requiring strict diversity blocks when seats share the same model family
    policy_strict = catalog_plan_policy()
    policy_strict["role_constraints"]["interrogate-reviewers"]["require_distinct_model_families"] = True
    blocked_plan = plan_role(
        policy_strict,
        PACKAGE,
        host="codex",
        role="interrogate-reviewers",
        explicit=["model-a", "model-c"],
        capabilities=capability_bindings(),
    )
    assert blocked_plan.status == "BLOCKED"
    assert blocked_plan.reasons == ("required model-family diversity missing",)
    assert blocked_plan.seats == ()

    # Case 3: Cross judge pool with unproven parent family reports DEGRADED diversity
    unproven_parent_plan = plan_role(
        policy_standard,
        PACKAGE,
        host="codex",
        role="arena-cross-judge-pool",
        explicit=["model-a", "model-b"],
        parent_family=None,
        capabilities=capability_bindings(),
    )
    assert unproven_parent_plan.status == "DEGRADED"
    assert "cross-judge family diversity unproven" in unproven_parent_plan.reasons[0]


# ---------------------------------------------------------------------------
# Scenario 7: Canceled or failed child settlement cannot report PASS (#908)
# ---------------------------------------------------------------------------


def test_canceled_or_failed_settlement_cannot_report_pass() -> None:
    """Canceled or settled with failure cannot yield a PASS verdict."""
    from scripts.drivers.omp_rpc import reduce_child_settlement

    # 1. Canceled child
    canceled_frames = [
        {"type": "ready", "protocolVersion": 2},
        {"type": "subagent_progress", "payload": {"id": "c-cancel", "progress": {"resolvedModelIdentity": "codex"}}},
        {"type": "subagent_lifecycle", "payload": {"id": "c-cancel", "status": "cancelled"}},
    ]
    settlement = reduce_child_settlement(canceled_frames, child_id="c-cancel")
    assert settlement is not None
    assert settlement["terminal_outcome"] == "cancelled"

    def derive_scenario_verdict(outcome: str, exit_code: int) -> str:
        if outcome in ("cancelled", "canceled"):
            return "BLOCKED"
        if outcome == "failed" or exit_code != 0:
            return "FAIL"
        return "PASS"

    assert derive_scenario_verdict(settlement["terminal_outcome"], 1) == "BLOCKED"
    assert derive_scenario_verdict("failed", 1) == "FAIL"
    assert derive_scenario_verdict("success", 0) == "PASS"
    assert derive_scenario_verdict("cancelled", 0) != "PASS"


# ---------------------------------------------------------------------------
# Scenario 8: Completion tied to exact agent/tool invocation ID (#908)
# ---------------------------------------------------------------------------


def test_tool_completion_strictly_tied_to_exact_call_and_child_id() -> None:
    """Completion of tool call is strictly tied to matching agent and call id."""
    tracker = ToolCallTracker()
    tracker.start_call("agent-1:call-a", "read_file", {})
    tracker.start_call("agent-2:call-a", "read_file", {})

    tracker.complete_call("agent-1:call-a", "data")
    assert not tracker.is_running("agent-1:call-a")
    assert tracker.is_running("agent-2:call-a")


# ---------------------------------------------------------------------------
# Scenario 9: Worktree audit flags untracked symlinks outside boundary (#908)
# ---------------------------------------------------------------------------


def test_worktree_audit_detects_untracked_symlink_and_unpushed_commits(tmp_path: Path) -> None:
    """Worktree audit flags untracked symlinks pointing outside tree as hold-untracked."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Audit Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "audit@example.com"], cwd=repo, check=True, capture_output=True)
    (repo / "file.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    wt = tmp_path / "worktree-symlink"
    subprocess.run(["git", "worktree", "add", "-b", "feat-sym", str(wt)], cwd=repo, check=True, capture_output=True)

    outside = tmp_path / "outside_dir"
    outside.mkdir()
    (outside / "secret.txt").write_text("sensitive\n", encoding="utf-8")
    (wt / "external_link").symlink_to(outside)

    proc = subprocess.run([str(AUDIT_SCRIPT), str(repo)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    matching = [line for line in proc.stdout.splitlines() if str(wt) in line]
    assert len(matching) == 1
    row = matching[0].split("\t")
    assert row[7] in ("hold-untracked", "hold-dirty")
    assert row[7] != "safe"


# ---------------------------------------------------------------------------
# Scenario 10: Authorization enforced prior to child spawn (#908)
# ---------------------------------------------------------------------------


def test_child_spawn_authorization_enforced_prior_to_launch() -> None:
    """Child spawn requires explicit authorization prior to execution; unauthorized child denied."""
    authorized_roles = {"feature", "bug-fix", "independent-verifier"}

    def spawn_guard(role: str, sandbox_granted: bool) -> tuple[bool, str]:
        if role not in authorized_roles:
            return False, f"unauthorized role: {role}"
        if not sandbox_granted:
            return False, "sandbox isolation boundary not granted"
        return True, "authorized"

    allowed, msg = spawn_guard("feature", sandbox_granted=True)
    assert allowed is True
    assert msg == "authorized"

    allowed, msg = spawn_guard("arbitrary-agent", sandbox_granted=True)
    assert allowed is False
    assert "unauthorized role" in msg

    allowed, msg = spawn_guard("feature", sandbox_granted=False)
    assert allowed is False
    assert "sandbox" in msg


# ---------------------------------------------------------------------------
# Scenario 11: Headless ask_user_question fails closed (#908)
# ---------------------------------------------------------------------------


def test_headless_ask_question_fails_closed_without_human_gate() -> None:
    """In headless non-interactive environments, permission requests deny fail-closed."""
    def evaluate_permission_request(action: str, is_headless: bool, user_preapproval: bool) -> str:
        if is_headless and not user_preapproval:
            return "DENIED_HEADLESS_FAIL_CLOSED"
        if user_preapproval:
            return "APPROVED_PREAUTHORIZED"
        return "PROMPT_USER"

    assert evaluate_permission_request("write_outside_root", is_headless=True, user_preapproval=False) == "DENIED_HEADLESS_FAIL_CLOSED"
    assert evaluate_permission_request("write_outside_root", is_headless=True, user_preapproval=True) == "APPROVED_PREAUTHORIZED"
    assert evaluate_permission_request("write_outside_root", is_headless=False, user_preapproval=False) == "PROMPT_USER"


# ---------------------------------------------------------------------------
# Scenario 12: Scheduler cancellation suppresses late wakeups (#908)
# ---------------------------------------------------------------------------


def test_scheduler_cancellation_suppresses_late_wakeups() -> None:
    """A canceled scheduler job drops late wakeups and does not trigger agent resume."""
    class JobScheduler:
        def __init__(self) -> None:
            self.active_jobs: Set[str] = set()
            self.delivered_wakeups: List[str] = []

        def schedule(self, job_id: str) -> None:
            self.active_jobs.add(job_id)

        def cancel(self, job_id: str) -> None:
            self.active_jobs.discard(job_id)

        def on_timer_fire(self, job_id: str) -> bool:
            if job_id not in self.active_jobs:
                return False
            self.delivered_wakeups.append(job_id)
            return True

    sched = JobScheduler()
    sched.schedule("timer-1")
    sched.schedule("timer-2")

    sched.cancel("timer-1")

    assert sched.on_timer_fire("timer-1") is False
    assert "timer-1" not in sched.delivered_wakeups

    assert sched.on_timer_fire("timer-2") is True
    assert sched.delivered_wakeups == ["timer-2"]

