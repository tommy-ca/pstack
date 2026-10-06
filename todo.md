# Epic Execution Program

## Epic #48 & PR #47 Execution Program
- [x] Unit 1: Spec repair and OpenSpec change proposal (PR #47 fix, tests green)
- [x] Unit 2: Issue #49 Canonical Index Lever (`scripts/canonical-index.py`)
- [x] Unit 3: Issues #50 & #76 Typed Schemas (Capability, Binding, Adaptation, Evidence, Package Descriptor)
- [x] Unit 4: Issues #51 & #54 Host-Neutral Boundary & Lever Verifier (`scripts/verify-portable.py`)
- [x] Unit 5: Issue #79 Architecture Gate (Arena + Interrogate)
- [x] Unit 6: Issue #61 Codex Pilot (Capability Map, Native Package, Conformance)
- [x] Unit 7: Issue #80 Pilot Reconciliation
- [x] Unit 8 & 9: Issues #62 & #63 OMP & OpenCode Adapters
- [x] Unit 10: Issues #78 & #56 Cross-Harness Acceptance (Swarm, Interrogate, Lever Proof)

## Epic #106: Portable Verification Skills & Tooling across 5 Harnesses
- [x] Unit 1: #101 Formalize harness skill and plugin layouts in portability schemas (PR #107)
- [x] Unit 2: #102 Arena + Interrogate portable verification skill architecture in ADR-0014 (PR #108)
- [x] Unit 3: #103 Port create-verification-skill and maintain-verification-skill (PR #109)
- [x] Unit 4: #104 Generalize subagent dispatch in swarm, arena, interrogate, setup-pstack (PR #110)
- [x] Unit 5: #105 5-Harness Swarm acceptance and 3-plane lever verification (PR #111)

## Epic #112: 5-Harness Adapter Audit, Core Skills Portability & Verification Generalization
- [x] Unit 1: Audit and eliminate single-harness lock-in across core skills (`poteto-mode`, `how`, `architect`, `why`)
- [x] Unit 2: Extend `scripts/verify-portable.py` with `--host all` for single-command 5-harness lever runs
- [x] Unit 3: Sync `scripts/verify-harness.py` and `leftover-scanner.md` with all 5 harness tool references
- [x] Unit 4: Execute 5-Harness Lever Verification (Grok, Codex, OMP, OpenCode, Antigravity 3-plane PASS)
- [x] Unit 5: Full test suite verification (165/165 passed in 95s)
- [x] Unit 6: Live Antigravity plugin synchronization (`scripts/sync-antigravity-plugin.py --sync`)
- [x] Unit 7: GitHub issue state and epic reconciliation

## Epic #125: AGY Installed Plugin Reconciliation, 8-Skill Canonical Ingestion & 5-Harness Lever Verification
- [x] Unit 1: Issue #121 Ingest & harden 8 PR/review skills into canonical repository (`skills/`)
- [x] Unit 2: Issue #122 Formalize Antigravity commands and 22 subagents packaging projection (`scripts/project-package.py`)
- [x] Unit 3: Issue #123 Upgrade Antigravity plugin synchronization lever with bidirectional verification (`scripts/sync-antigravity-plugin.py`)
- [x] Unit 4: Issue #124 Update multi-harness profiles, skill orders, and portability schemas (`profiles/antigravity.json`)
- [x] Unit 5: Swarm, Arena, Interrogate, and 5-Harness Lever verification (`verify-portable.py run --host all`)
- [x] Unit 6: Stacked PRs creation and Babysit protocol execution

## Epic #127: Revalidate Current Pstack Portability Against the Formal Contract
### Phase 1: Canonical Truth & Upstream Freshness (Sub-epic #128)
- [x] Unit 1: Issue #132 Eliminate hardcoded canonical counts from portable verification (`verify-portable.py`, `verify-harness.py`, `test_canonical_index.py`)
- [x] Unit 2: Issue #133 Classify upstream drift from pinned 0.15.5 to current 0.15.13 (`canonical-index.py`, `canonical-drift.json`, `classification-0.15.13.tsv`)

### Phase 2: Contract, Adapter Boundary & Evidence Reconciliation (Sub-epic #129)
- [x] Unit 3: Issue #134 Reconcile portable capability universe with support-floor semantics
- [x] Unit 4: Sub-epic #142 Enforce host-neutral shared-skill adapter boundary
  - [x] Unit 4a: Issue #143 Move host execution primitives out of shared skills/playbooks
  - [x] Unit 4b: Issue #144 Move model/default and verification-lane policy behind harness profiles
  - [x] Unit 4c: Issue #145 Add forbidden-host-vocabulary scanner
- [ ] Unit 5: Issue #135 Make support states revision-bound and evidence refs durable

### Phase 3: Native Runtime Proof & Package Lifecycle (Sub-epic #130)
- [ ] Unit 6: Issue #136 Replace proxy runtime plane with real harness-native drivers
- [ ] Unit 7: Issue #137 Replace placeholder lifecycle commands with real native install/update/uninstall proof
- [ ] Unit 8: Issue #139 Re-run five-harness evidence matrix on current main

### Phase 4: Final 5-Harness Acceptance, Stacked PRs & Shipping (Gate #131)
- [ ] Unit 9: Gate #131 Five-harness current-main Swarm + Interrogate acceptance
- [ ] Unit 10: Stacked PRs creation, Babysit protocol, merge and ship

