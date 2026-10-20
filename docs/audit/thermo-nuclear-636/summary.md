# Thermo-Nuclear Code Quality Review Summary: Program #636

**Audit Target**: Program [#636](https://github.com/tommy-ca/pstack/issues/636) (Reconcile pstack-claude 0.9.95 semantics against canonical and six-host core)  
**Base Revision**: `329acf2` (merge base for Program #636)  
**Head Revision**: `0517eb2` (`main` @ closeout of Program #636)  
**Audit Scope**: Commits `8e9e51a`, `35a9b59`, `0517eb2` and surrounding interfaces across `scripts/`, `skills/`, and `tests/`  
**Overall Verdict**: **REMEDIATION REQUIRED** (1 Critical Lifecycle Bug, 1 Latent False-Pass Driver Risk, 4 Major 1,000-Line Limit Breaches)

---

### Executive Narrative & High-Conviction Findings

#### 1. OpenSpec Active Change Resolution Crashes on Clean Completed Trees (Correctness / Blocker)
In [`scripts/openspec_change.py`](file:///home/tommyk/projects/pstack/scripts/openspec_change.py), the helper `_active_openspec_changes()` was modified to filter out completed changes (`status != "complete"`). However, the return statement falls back to returning all parsed changes if the in-progress list is empty (`return in_progress if in_progress else parsed`). When all OpenSpec changes in the workspace are marked complete (as they are right now with `2026-10-20-cross-port-semantic-delta` and `2026-10-15-harness-neutral-role-policy`), `in_progress` is empty, so the function returns every completed change. Consequently, `resolve_openspec_change(None)` sees multiple entries and returns `state="ambiguous"`, causing `validate_openspec_change(None)` to crash with exit code 1. This directly breaks the documented invariant that default doctor invocations perform a clean no-op when no active changes remain. The remedy is to eliminate the fallback and return `in_progress` directly so that a completed workspace cleanly resolves to `state="none"`. Full analysis, reproduction, and code-judo replacement are in [`01_openspec_resolution_and_lifecycle.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-636/01_openspec_resolution_and_lifecycle.md).

#### 2. Incomplete Coverage of `-uall` Untracked File Hygiene Creates Latent Isolation False-Passes (Data Safety / False Pass)
While [`skills/poteto-mode/scripts/worktree-audit.sh`](file:///home/tommyk/projects/pstack/skills/poteto-mode/scripts/worktree-audit.sh) was successfully hardened in PR #644 by passing `-uall` to `git status --porcelain -uall` to prevent user scratch loss when `status.showUntrackedFiles = no` is configured, an audit across all other `git status` callers revealed severe omissions. Specifically, [`scripts/drivers/omp.py`](file:///home/tommyk/projects/pstack/scripts/drivers/omp.py) line 143 (`_isolation_residue`) calls `git status --porcelain` without `-uall`. If a repository has `status.showUntrackedFiles = no` configured and a leaked child agent creates untracked files or directories in the parent checkout, the driver returns `tree_clean: True`, producing a false PASS on runtime workspace isolation. Similarly, [`scripts/sync-antigravity-plugin.py`](file:///home/tommyk/projects/pstack/scripts/sync-antigravity-plugin.py) line 287 fails to pass `-uall`, risking publication of untracked files. The remedy is to standardize all status calls on `-uall`. Detailed evidence is in [`02_worktree_audit_and_untracked_hygiene.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-636/02_worktree_audit_and_untracked_hygiene.md).

#### 3. Missing Negative POSIX Process Signaling Guards in Cancellation Contracts (Safety / System Integrity)
In [`tests/test_cross_port_contracts.py`](file:///home/tommyk/projects/pstack/tests/test_cross_port_contracts.py), Scenario 4 validates that child stop/cancel requires native settlement and guards against PID reuse via token matching. However, the contract test omits explicit guards against non-positive PIDs (`pid <= 1`). In POSIX systems, calling `kill` with PID 0 signals the entire process group, and PID -1 signals all processes. Native driver cleanup logic must refuse to signal non-positive PIDs or system init. The remedy is to harden the safe termination contract in `test_cross_port_contracts.py` with explicit boundary assertions against `target_pid <= 1`. Analysis is in [`03_contract_tests_and_domain_modeling.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-636/03_contract_tests_and_domain_modeling.md).

#### 4. Severe Breaches of the 1,000-Line Code Quality Threshold (Modularity & Maintainability)
The codebase currently harbors four files that violate the core thermo-nuclear standard against sprawl beyond 1,000 lines:
1. [`skills/poteto-mode/scripts/orch/store.ts`](file:///home/tommyk/projects/pstack/skills/poteto-mode/scripts/orch/store.ts) has ballooned to **1,677 lines**, tangling domain types, PID lock acquisition, GitHub/Origin CLI querying, and TSV persistence into a single monolith.
2. [`tests/test_verify_harness.py`](file:///home/tommyk/projects/pstack/tests/test_verify_harness.py) spans **1,437 lines**, mixing intent archive validation, playbook text assertions, frontmatter checks, and collision tests.
3. [`tests/test_evidence_durability.py`](file:///home/tommyk/projects/pstack/tests/test_evidence_durability.py) spans **1,016 lines**, and [`tests/test_evidence_settlement.py`](file:///home/tommyk/projects/pstack/tests/test_evidence_settlement.py) spans **1,003 lines**, largely due to duplicate mock receipt builders and synthetic scenario generators.

The remedy is a series of structural "code judo" decompositions: splitting `store.ts` into `types.ts`, `lock.ts`, `frontier.ts`, and a focused `store.ts`; splitting `test_verify_harness.py` into archive, playbook, and core test files; and consolidating evidence fixtures into a shared helper module. Worked decomposition plans are in [`04_codebase_file_size_and_complexity_thresholds.md`](file:///home/tommyk/projects/pstack/docs/audit/thermo-nuclear-636/04_codebase_file_size_and_complexity_thresholds.md).

---

### Proposed Remediation Sequence

1. **Wave 1 (OpenSpec Resolution & Lifecycle)**:
   - Fix `_active_openspec_changes` in `scripts/openspec_change.py` to return `in_progress` directly without falling back to `parsed`.
   - Add unit tests verifying that all-complete change lists resolve cleanly to `state="none"` and exit 0.
2. **Wave 2 (Untracked File Hygiene & Driver Safety)**:
   - Add `-uall` to `_isolation_residue` in `scripts/drivers/omp.py` and `scripts/sync-antigravity-plugin.py`.
   - Add regression tests proving `tree_clean` is `False` when untracked child files exist under `status.showUntrackedFiles = no`.
   - Add `pid <= 1` guards to safe process termination contract in `tests/test_cross_port_contracts.py`.
3. **Wave 3 (Decompose `store.ts` Below 1,000 Lines)**:
   - Extract `skills/poteto-mode/scripts/orch/types.ts` (~260 lines).
   - Extract `skills/poteto-mode/scripts/orch/lock.ts` (~120 lines).
   - Extract `skills/poteto-mode/scripts/orch/frontier.ts` (~320 lines).
   - Keep `store.ts` under 950 lines and verify full suite with `bun test`.
4. **Wave 4 (Decompose Oversized Test Suites)**:
   - Split `tests/test_verify_harness.py` into archive, playbook, and core test suites.
   - Extract shared evidence mock fixtures into `tests/evidence_test_helpers.py`, bringing `test_evidence_durability.py` and `test_evidence_settlement.py` well under 800 lines.
   - Update `scripts/select_checks.py` mappings and verify full pytest pass.
