# Source-Pinned Semantic Audit and Cross-Port Parity Matrix — 2026-11-06

**Scope**: Three-source semantic audit and bounded cross-port follow-up across canonical Cursor PStack, comparator `pstack-claude`, and target `tommy-ca/pstack`. Tracked under Epic [#906](https://github.com/tommy-ca/pstack/issues/906) and Unit A [#907](https://github.com/tommy-ca/pstack/issues/907).

---

## 1. Frozen Source Inputs

| Role | Repository | Pinned SHA | Tag / Version | Snapshot Date |
| --- | --- | --- | --- | --- |
| **Canonical** | `cursor/plugins` | `c742dd61706fbacc1b95f1a20b7b988cf096ce6c` | `v0.15.36` (PR #1043) | 2026-10-27 |
| **Comparator** | `michael-denyer/pstack-claude` | `d88063f3355a5ecff0e6dbb890a11bab4b08bc2e` | `v0.9.130` (#410) | 2026-11-05 |
| **Target Base** | `tommy-ca/pstack` | `5d58283f40f7fc8f56a536946abe79418538fe6e` | `v0.15.29-preview.0` | 2026-11-06 |

### Freshness and Deltas
- **Canonical diff (`88d47514...c742dd61`)**: Canonical advanced from 0.15.29 to 0.15.36. In #1043, Orchestrate was converted to an agentic playbook and the standalone `orch` CLI scripts were deleted. Target `tommy-ca/pstack` reconciled this canonical migration in Epic #840 (PRs #852, #858, #859, #860, #861, #862).
- **Comparator diff (`88f6d39f...d88063f3`)**: 86 commits, 300 files changed. Comparator synced to canonical 0.15.36 in commit `dec67d07` (#376), removing legacy `orch` scripts, adding native Antigravity/OMP/OpenCode packaging guidance, and expanding declared fork paths from 48 to 65.
- **Target six-host core**: Target maintains 6 native supported host targets (`grok`, `codex`, `omp`, `opencode`, `antigravity`, `droid`) plus candidate profile `pstack:pi`.

---

## 2. Fork and Policy Classification

Comparator `tools/forks.json` at `d88063f3` declares **65 fork paths** (62 `pstack`, 1 `cursor-team-kit`, 2 `thermos`).
Frozen into target research ledger: [`docs/research/pstack-claude-forks-2026-11-06.json`](file:///home/tommyk/projects/pstack/docs/research/pstack-claude-forks-2026-11-06.json).

### Disposition Breakdown
- **Adapt (14 items)**: Reconciled into host-neutral contracts and native package projections (`agents/comment-sicko.md`, `skills/deslop/SKILL.md`, `skills/no-comments/SKILL.md`, `skills/thermo-nuclear-code-quality-review/SKILL.md`, architectural reconciliation prompts).
- **Preserve Canonical (28 items)**: Principles, core playbooks, and task topologies where target preserves canonical Cursor semantics and rejects comparator rewrites.
- **Policy-Fork (6 items)**: Deliberate comparator behavioral forks (`HOLD` rules in `no-comments`, `why` explainer prompt shortcuts, specific link validator adjustments). Retained as comparator forks; not promoted to canonical.
- **Exclude (17 items)**: Host-specific mechanisms (Claude `~/.claude/orchestrate` store, Windows Node wrapper shims for `statechart/scripts/*`, Pi RPC custom extensions). Target excludes foreign runtime stores.

---

## 3. Semantic Boundary Matrix

| Semantic Boundary | Canonical Intent (`c742dd61`) | Comparator Implementation (`d88063f3`) | Target Baseline (`5d58283f`) | Observable Postcondition / Test |
| --- | --- | --- | --- | --- |
| **Agentic Orchestrate** | Orchestrate is an agentic playbook using host tasks; `orch` CLI deleted. | Synced to 0.15.36 in #376; deleted `orch` scripts; writes objective to `notes.md`. | Reconciled in PR #859; host-owned coordination; no external `orch` binary. | Static check: `verify_harness.py` validates `orchestrate.md` without `orch` references. |
| **Child Lifetime & Completion** | Task tool invocation settles with child exit. | Pi RPC child-process extension with custom transcript watchers. | Host native RPC (`scripts/drivers/omp_rpc.py`) and subagent delegates. | Negative test: Canceled or settled child can never yield PASS. |
| **Worktree Isolation** | Worktree safety playbooks and git cleanup. | `tests/pi/worktree-status-config.test.mjs` checking untracked files and preference keys. | `scripts/worktree_protocol.py` and `tests/test_worktree_cleanup.py`. | Negative test: Untracked files and symlinks outside boundary are rejected. |
| **Permission Verdicts** | Human gate prompt for risky actions. | `pi-verdict` authorization hooks and `headless_ask_must_deny`. | `tests/test_pi_authorization_contracts.py` with 9 test cases. | Negative test: Headless execution with missing permission denies fail-closed. |
| **Scheduler Cancellation** | Bounded timeouts and agent termination. | TLA+ `PiScheduler.tla` model checking timer/wakeup delivery. | Bounded timers, scheduler cancellation, and late wakeup suppression. | Negative test: Late wakeup after cancellation is ignored. |
| **Package Projection** | Cursor plugin layout. | Multi-host generators for Claude, Pi, Codex, Antigravity, OMP. | `scripts/project_package.py` and `scripts/package_lifecycle.py` for 6 hosts. | Conformance: `verify_portable.py doctor --host <host>` validates packaging. |
| **Code Quality Reviews** | `thermos` review skills. | Packaged under `skills/thermos/` with model mapping forks. | Packaged under `skills/thermo-nuclear-code-quality-review/` host-neutral. | Contract test: `verify_harness.py` verifies all review frontmatter and tools. |

---

## 4. License and NOTICE Review

- **Canonical (`cursor/plugins`)**: Lauren Tan / Cursor, MIT License.
- **Comparator (`michael-denyer/pstack-claude`)**: Michael Denyer, MIT License; carries `NOTICE.md`, `NOTICE-skills.md`, and references.
- **Target (`tommy-ca/pstack`)**: MIT License. No third-party proprietary code is incorporated. All adapter scripts and test fixtures are clean-room implementations against published interfaces.

---

## 5. Acceptance and Guardrails

1. **No Unsupported Parity Claims**: Every claim of parity must reference either a static verification check or an observed live test receipt.
2. **Confinement of Experimental Hosts**: Standalone Pi candidate remains an evaluated candidate profile (`profiles/pstack-pi.json`), not a seventh shipped core host.
3. **Reproducibility**: All source pins and blob hashes are verifiable via GitHub API.
