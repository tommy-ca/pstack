# Recursive plan — #906

Status 2026-11-06. These are issue-owned work items, not automatic proof of completion.

## A. Source classification — #907
- [x] Freeze source SHA and scope canonical upstream pstack/ (cursor c742dd6), comparator port (d88063f), target base (5d58283).
- [x] Record 86-commit GitHub compare with 300-file listing cap; partial path inventory only.
- [x] Recover all changed blob paths via two untruncated Git-tree snapshots (464 add / 51 delete / 134 modify), documented in references/comparator-tree-delta.md.
- [ ] Annotate all relevant semantic hunks, policy forks, host-specific mechanisms, canonical drift and negative scenarios; do not equate path completeness with behavioral audit.
- [ ] Audit license/NOTICE before any verbatim import. Reconcile with closed #429, #840 and #894.

## B. Functional verification — #908, after A
- [ ] Select only genuinely uncovered negative postconditions from tests/pi and docs/pi-equivalence.
- [ ] Extend existing host-specific driver / verify-<host> feature map; do not build a universal process manager.
- [ ] Fault-inject canceled child, hidden worktree output, invalid authorization, scheduler late delivery and stale receipts.
- [ ] Collect exact-head Tier 1 offline receipts, then Tier 2 CLI and Tier 3 native receipts only when real host is available.

## C. Formal verification — #909, after A and selected B code paths
- [ ] Choose the highest-impact code-level state machine.
- [ ] Bind one model transition to one atomic code action, document host assumptions and liveness fairness.
- [ ] Reuse create-formal-verification-skill, checker and maintainer; demonstrate failure for each safety/liveness mutant.
- [ ] Report checker absence or counterexample as BLOCKED/FAIL, not PASS.

## D. LLMWiki semantic composition — #910, after A
- [x] Add candidate source-attributed wiki analytical crosswalk with explicit source-only status.
- [ ] Source-ingest immutable local artifacts with scripts/llm_wiki.py ingest only when rights-safe and hash-logged.
- [ ] Generate index; run wiki check, verify-sources, graph/orphans and source-provenance validations on current head.

## E. Independent exact-head review — #911, after A–D
- [ ] Swarm: genuinely independent source, security, verification and knowledge lanes, with recorded IDs/models.
- [ ] Arena: compare no-code, minimal fixtures, larger engine and document evidence-backed choice.
- [ ] Interrogate: deny and cancellation races, wrong model family, hidden files and stale receipt attacks.
- [ ] Apply canonical thermo-nuclear-review + thermo-nuclear-code-quality-review to actual patch; triage all findings.
- [ ] CI, exact-head evidence, human approval where required, then merge a reviewed stack or report BLOCKED.

Dependencies: #907 -> (#908, #909, #910) -> #911; #909 also consumes #908's selected code-path list. Historical #429/#840/#871/#887/#894 remain closed.

The present branch modifies docs and skill guidance only; no runtime, independent model or formal checker execution is asserted.
