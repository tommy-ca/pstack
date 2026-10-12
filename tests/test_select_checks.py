"""Change-scoped check selection and exact-head evidence binding (#312).

The selection table and the patch-id invalidation rule are the two contracts here:
a changed path must choose the minimal gate that can fail for it, and a recorded
verdict must stop counting as current CI once the patch under it changes.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evidence_receipts

PY = sys.executable


def _load_verifier():
    script = ROOT / "scripts" / "verify-portable.py"
    spec = importlib.util.spec_from_file_location("verify_portable_select", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_portable_select"] = module
    spec.loader.exec_module(module)
    return module


vp = _load_verifier()

# The offline PR gate as named in .github/workflows/portability-offline.yml. Read from
# the workflow rather than re-typed, so a gate list change cannot leave this stale.
OFFLINE_GATE = re.findall(
    r"tests/[\w./-]+\.py",
    (ROOT / ".github" / "workflows" / "portability-offline.yml").read_text(encoding="utf-8"),
)


def _ids(result) -> list[str]:
    return [check["id"] for check in result["checks"]]


def _commands(result) -> list[list[str]]:
    return [check["command"] for check in result["checks"]]


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    )
    return res.stdout


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "selection@example.com")
    _git(repo, "config", "user.name", "Selection Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    return repo


class TestCheckSelectionTable:
    def test_offline_gate_list_comes_from_the_workflow(self) -> None:
        assert vp.offline_contract_tests(ROOT) == OFFLINE_GATE

    def test_docs_only_selects_docs_gate_never_the_runtime_matrix(self) -> None:
        result = vp.select_checks(["docs/verification-test-tiers.md"])

        assert result["unmapped_paths"] == []
        assert _commands(result) == [[PY, "-m", "pytest", "-q", "tests/test_verify_docs_sync.py"]]
        assert _ids(result) == ["pytest:tests/test_verify_docs_sync.py"]
        assert result["checks"][0]["tier"] == "outside_gate"
        # Negative control: a docs-only change must not drag in the offline contract set.
        assert "pytest:tests/test_portability_schemas.py" not in _ids(result)
        assert _ids(result) != sorted(f"pytest:{m}" for m in OFFLINE_GATE)

    def test_scripts_only_selects_the_owning_module(self) -> None:
        result = vp.select_checks(["scripts/sync-antigravity-plugin.py"])

        assert result["unmapped_paths"] == []
        assert _commands(result) == [
            [PY, "-m", "pytest", "-q", "tests/test_sync_antigravity_plugin.py"]
        ]

    def test_tests_only_selects_only_the_changed_module(self) -> None:
        result = vp.select_checks(["tests/test_shadow_routing.py"])

        assert _commands(result) == [[PY, "-m", "pytest", "-q", "tests/test_shadow_routing.py"]]
        assert result["checks"][0]["tier"] == "outside_gate"

    def test_offline_listed_module_keeps_the_offline_tier_without_opt_in(self) -> None:
        result = vp.select_checks(["tests/test_route_resolver.py"])

        assert _commands(result) == [[PY, "-m", "pytest", "-q", "tests/test_route_resolver.py"]]
        assert result["checks"][0]["tier"] == "offline"

    def test_host_dependent_module_carries_the_documented_opt_in(self) -> None:
        result = vp.select_checks(["scripts/drivers/omp.py"])

        assert result["checks"][0]["tier"] == "host_dependent"
        assert _commands(result) == [
            ["env", "PSTACK_RUN_HOST_DEPENDENT_TESTS=1", PY, "-m", "pytest", "-q", "tests/test_harness_drivers.py"],
            [PY, "-m", "pytest", "-q", "tests/test_route_resolver.py"],
        ]

    def test_specific_script_rule_beats_the_scripts_fallback(self) -> None:
        result = vp.select_checks(["scripts/verify-harness.py"])

        assert _ids(result) == ["pytest:tests/test_verify_harness.py"]
        assert _commands(result) == [[PY, "-m", "pytest", "-q", "tests/test_verify_harness.py"]]

    def test_skill_markdown_uses_the_skill_rule_not_the_docs_rule(self) -> None:
        result = vp.select_checks(["skills/fix-ci/SKILL.md"])

        assert _ids(result) == [
            "pytest:tests/test_scan_host_boundary.py",
            "pytest:tests/test_skill_frontmatter.py",
            "script:scan-host-boundary.py",
        ]
        assert result["checks"][-1]["command"] == [PY, "scripts/scan-host-boundary.py"]

    def test_references_change_selects_contract_tests_and_inventory_check(self) -> None:
        result = vp.select_checks(["references/decision-routing.json"])

        # test_evidence_receipts.py entered the offline gate, so it sorts with the
        # offline pytest checks instead of trailing as an outside_gate module.
        assert _ids(result) == [
            "pytest:tests/test_droid_routing.py",
            "pytest:tests/test_evidence_receipts.py",
            "pytest:tests/test_route_resolver.py",
            "script:canonical-index.py",
        ]
        assert all(check["tier"] == "offline" for check in result["checks"])
        by_id = {check["id"]: check for check in result["checks"]}
        assert by_id["script:canonical-index.py"]["command"] == [
            PY,
            "scripts/canonical-index.py",
            "--check",
        ]

    def test_spec_only_change_selects_the_docs_gate(self) -> None:
        result = vp.select_checks(
            [
                "openspec/changes/2026-10-11-omp-native-adapter/.openspec.yaml",
                "openspec/changes/2026-10-11-omp-native-adapter/tasks.md",
                "openspec/specs/pstack-portability/spec.md",
            ]
        )

        assert result["unmapped_paths"] == []
        assert _ids(result) == ["pytest:tests/test_verify_docs_sync.py"]
        assert _commands(result) == [[PY, "-m", "pytest", "-q", "tests/test_verify_docs_sync.py"]]
        # Negative control: spec prose must not select the whole offline matrix.
        assert _ids(result) != sorted(f"pytest:{m}" for m in OFFLINE_GATE)
        assert len(result["checks"]) == 1

    def test_root_level_prose_selects_the_docs_gate(self) -> None:
        """Root markdown has no directory prefix, so it needs its own table row."""
        result = vp.select_checks(["todo.md", "README.md", "TEST-PLAN.md"])

        assert result["unmapped_paths"] == []
        assert _ids(result) == ["pytest:tests/test_verify_docs_sync.py"]
        assert len(result["checks"]) == 1

    def test_unmapped_paths_default_to_the_full_offline_set_and_are_reported(self) -> None:
        result = vp.select_checks(["UPSTREAM", "plugin.json"])

        # Negative control: an unmapped path must never be silently skippable.
        assert result["unmapped_paths"] == ["UPSTREAM", "plugin.json"]
        assert _ids(result) == sorted(f"pytest:{m}" for m in OFFLINE_GATE)
        assert all(check["tier"] == "offline" for check in result["checks"])
        assert result["checks"][0]["paths"] == [
            "UPSTREAM",
            "plugin.json",
        ]

    def test_selection_deduplicates_shared_modules(self) -> None:
        result = vp.select_checks(["agents/a.md", "droids/b.md"])

        assert _ids(result) == [
            "pytest:tests/test_scan_host_boundary.py",
            "script:scan-host-boundary.py",
            "pytest:tests/test_droid_projection.py",
            "pytest:tests/test_plugin_agents.py",
            "pytest:tests/test_verify_harness.py",
        ]
        assert result["unmapped_paths"] == []
        assert result["checks"][0]["paths"] == ["agents/a.md", "droids/b.md"]


class TestChangedPathResolution:
    def test_merge_base_scopes_the_committed_diff(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _git(repo, "checkout", "-b", "feat")
        (repo / "feat.txt").write_text("feat\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "feat")

        diff = vp.changed_paths(repo, "main")
        assert diff["changed_paths"] == ["feat.txt"]
        assert diff["merge_base"] == _git(repo, "rev-parse", "main").strip()

    def test_staged_unstaged_and_untracked_context_at_head(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        (repo / "staged.txt").write_text("s\n", encoding="utf-8")
        _git(repo, "add", "staged.txt")
        (repo / "untracked.txt").write_text("u\n", encoding="utf-8")
        (repo / "base.txt").write_text("edited\n", encoding="utf-8")

        diff = vp.changed_paths(repo, "main")
        assert set(diff["changed_paths"]) == {"staged.txt", "untracked.txt", "base.txt"}
        # A non-HEAD ref has no worktree context to include.
        assert vp.changed_paths(repo, "main", "main")["changed_paths"] == []

    def test_plan_binds_patch_id_to_the_scoped_diff(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        _git(repo, "checkout", "-b", "feat")
        (repo / "docs").mkdir()
        (repo / "docs" / "note.md").write_text("n\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "docs: note")

        plan = vp.select_checks_plan("main", "HEAD", repo, OFFLINE_GATE)
        assert plan["changed_paths"] == ["docs/note.md"]
        assert plan["patch_id"] == evidence_receipts.compute_patch_id(
            repo, plan["merge_base"], "HEAD"
        )
        assert [check["id"] for check in plan["checks"]] == ["pytest:tests/test_verify_docs_sync.py"]


class TestCheckEvidenceBinding:
    def _record(self, repo: Path, **kwargs) -> evidence_receipts.CheckEvidenceReceipt:
        outcomes = kwargs.pop("outcomes", {"pytest:tests/test_x.py": "PASS"})
        return evidence_receipts.create_check_evidence_receipt(
            repo, "main", ["pytest:tests/test_x.py"], outcomes, "HEAD"
        )

    def _branch_with_patch(self, tmp_path: Path) -> Path:
        repo = _init_repo(tmp_path)
        _git(repo, "checkout", "-b", "feat")
        (repo / "work.txt").write_text("work\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "feat: work")
        return repo

    def test_unchanged_head_keeps_the_verdict_and_may_be_quoted(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)

        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (False, [])
        claimable, reason = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
        assert claimable is True
        assert receipt.head_sha[:8] in reason

    def test_changed_head_and_patch_invalidates(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)

        (repo / "work.txt").write_text("reworked\n", encoding="utf-8")
        _git(repo, "commit", "-am", "feat: rework")

        assert evidence_receipts.resolve_revision(repo) != receipt.head_sha
        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert stale is True
        assert any("Patch drift" in r for r in reasons)
        assert any("Head moved" in r for r in reasons)
        claimable, reason = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
        assert claimable is False
        assert "stale" in reason.lower()

    def test_pure_rebase_keeps_the_verdict(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)
        original_patch_id = receipt.patch_id

        _git(repo, "checkout", "main")
        (repo / "trunk.txt").write_text("trunk\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "trunk: unrelated")
        _git(repo, "checkout", "feat")
        _git(repo, "rebase", "main")

        assert evidence_receipts.resolve_revision(repo) != receipt.head_sha
        assert receipt.worktree_digest == evidence_receipts.compute_worktree_digest(repo)
        assert evidence_receipts.compute_patch_id(
            repo, receipt.base_sha, "HEAD"
        ) != original_patch_id  # recomputed against the stale base
        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (False, [])
        current_head_sha = evidence_receipts.resolve_revision(repo)
        current_base_sha = evidence_receipts.resolve_merge_base(repo, "main", "HEAD")
        claimable, claim = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
        assert claimable is True
        # The claim is currency for the rewritten head, not the receipt's stale one,
        # and it names the recheck it still owes: the checks at that head, that base.
        assert (
            claim.startswith(f"Current at {current_head_sha[:8]}")
            and "re-run the checks" in claim
            and current_base_sha[:8] in claim
        ), claim

    def test_failed_or_blocked_outcomes_are_reported_not_promoted(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        failed = self._record(repo, outcomes={"pytest:tests/test_x.py": "FAIL"})
        blocked = self._record(repo, outcomes={"pytest:tests/test_x.py": "BLOCKED"})

        assert failed.verdict == "FAIL"
        assert blocked.verdict == "BLOCKED"
        for receipt in (failed, blocked):
            claimable, reason = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
            assert claimable is False
            assert receipt.verdict in reason

    def test_unrecorded_outcomes_cannot_be_claimed_as_current_ci(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo, outcomes={})

        assert receipt.verdict == "UNTESTED"
        claimable, reason = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
        assert claimable is False
        assert "UNTESTED" in reason

    def test_unchanged_worktree_does_not_invalidate(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)

        assert receipt.worktree_digest == evidence_receipts.compute_worktree_digest(repo)
        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (False, [])

    def test_dirty_tracked_edit_invalidates(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)

        (repo / "work.txt").write_text("uncommitted rework\n", encoding="utf-8")

        assert evidence_receipts.resolve_revision(repo) == receipt.head_sha
        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (True, ["Worktree changed since recording"])
        claimable, reason = evidence_receipts.can_claim_current_ci(receipt, repo, "main")
        assert claimable is False
        assert "Worktree changed since recording" in reason

    def test_new_untracked_file_invalidates(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)

        (repo / "scratch.py").write_text("print('untracked')\n", encoding="utf-8")

        assert evidence_receipts.resolve_revision(repo) == receipt.head_sha
        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (True, ["Worktree changed since recording"])

    def test_untracked_content_change_after_cleaning_invalidates(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        (repo / "scratch.py").write_text("first\n", encoding="utf-8")
        receipt = self._record(repo)  # recorded from a dirty tree

        (repo / "scratch.py").write_text("second\n", encoding="utf-8")

        stale, reasons = evidence_receipts.check_check_evidence_staleness(receipt, repo, "main")
        assert (stale, reasons) == (True, ["Worktree changed since recording"])

    def test_receipt_roundtrips_through_json(self, tmp_path: Path) -> None:
        repo = self._branch_with_patch(tmp_path)
        receipt = self._record(repo)
        path = tmp_path / "checks.json"
        path.write_text(receipt.to_json(), encoding="utf-8")

        loaded = evidence_receipts.load_check_evidence_receipt(path)
        assert loaded == receipt
        assert loaded.check_ids == ["pytest:tests/test_x.py"]
        assert loaded.outcomes == {"pytest:tests/test_x.py": "PASS"}


if __name__ == "__main__":  # pragma: no cover - manual self-check
    raise SystemExit(pytest.main([__file__, "-q"]))
