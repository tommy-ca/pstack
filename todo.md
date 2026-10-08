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
- [x] Unit 5: Issue #135 Make support states revision-bound and evidence refs durable

### Phase 3: Native Runtime Proof & Package Lifecycle (Sub-epic #130)
- [x] Unit 6: Issue #136 Replace proxy runtime plane with real harness-native drivers
- [x] Unit 7: Issue #137 Replace placeholder lifecycle commands with real native install/update/uninstall proof
- [x] Unit 8: Issue #139 Re-run five-harness evidence matrix on current main

### Phase 4: Final 5-Harness Acceptance, Stacked PRs & Shipping (Gate #131)
- [x] Unit 9: Gate #131 Five-harness current-main Swarm + Interrogate acceptance
- [x] Unit 10: Stacked PRs creation, Babysit protocol, merge and ship

## Epic #209: Refresh portable pstack to upstream 0.15.15 and reconcile proven semantic defects
### Sub-epic #207: Reconcile current upstream semantics without reintroducing host coupling
- [x] Unit 1: Issue #201 Refresh current upstream pstack and classify the 0.15.5 → 0.15.15 delta (PR #224)
- [x] Unit 2: Issue #202 Make poteto-agent a delegate-only contract across host projections (PR #230)
- [x] Unit 3: Issue #203 Make worktree cleanup loss-aware and remove forceful registered deletion (PR #231)
- [x] Unit 4: Issue #204 Correct Test Behavior principle and track the canonical semantic defect (PR #232)

### Sub-epic #208: Prove refreshed current-main portability and semantic safety
- [x] Unit 5: Issue #205 Extend existing conformance levers for current upstream semantic invariants (PR #233)
- [x] Unit 6: Issue #206 Swarm: prove refreshed pstack across all declared harnesses (PR #234)
- [x] Unit 7: Issue #215 Interrogate: adversarially review the refreshed pstack exact-head diff (PR #234)
- [x] Unit 8: Issue #216 Reconcile exact-head evidence and close the upstream refresh program (PR #234)

## Program: Verification Metadata, Scaffold Safety & OpenSpec Target Alignment (Issues #217 & #214)
- [x] Unit 1: Issue #217 Antigravity dry-run read-only purity, drift detection, and symlink parity (PR #218)
- [x] Unit 2: Issue #217 Scaffold verification skill input validation and target safety (PR #219)
- [x] Unit 3: Issue #217 Complete ordered feature map validation and 6-destination proof limits (PR #220)
- [x] Unit 4: Issues #217 & #214 Verification tool dependency fingerprinting, OpenSpec coverage target alignment, candidate staleness safety, and 6-harness receipt matrix refresh

## Epic #193: Integrate optional Jev decision models into pstack with minimal semantic change
### Sub-epic #190: Formalize the optional Jev decision boundary and baseline eval
- [x] Unit 1: Issue #182 Typed decision contract, precedence, and fallback semantics (PR #270)
- [x] Unit 2: Issue #195 Context-minimization and data-egress boundary (PR #270)
- [x] Unit 3: Issue #196 Canonical playbook decision vocabulary and deterministic mapping in `references/decision-routing.json` (PR #271)
- [x] Unit 4: Issue #183 Arena seam comparison between no-change baseline and router-local candidate (PR #272)
- [x] Unit 5: Issue #197 Reconcile, Interrogate, validate, and verify formal spec PR #194 with ADR-0018 tooling (PR #272)
- [x] Unit 6: Recursive graph and execution program reconciliation (PR #273)

### Sub-epic #191: Implement shadow integration and build evidence
- [x] Task #184: Optional Jev provider adapter and explicit default-OFF feature/config gate (PR #274)
- [x] Task #185: Shadow playbook and skill-routing decisions with zero behavior change (PR #275)
- [x] Task #186: Offline routing corpus, calibration, latency, and cost lever (PR #276)
- [x] Task #199: Bind Jev evidence to canonical, provider, model, policy, and fixture revisions (PR #276)
- [x] Task #198: Run blinded pstack Eval for baseline vs Jev-assisted behavior (PR #277)

### Sub-epic #192: Verify and selectively promote Jev shadow decisions
- [x] Task #200: Prove Jev kill-switch and fail-open rollback equivalence (PR #278)
- [x] Task #189: Promote only proven low-risk Jev decisions behind reversible policy (PR #279)
- [x] Task #187: Swarm: run Jev decision regression matrix across task classes and harnesses (PR #280)
- [x] Task #188: Interrogate: adversarial review of Jev semantic drift, safety, and false confidence (PR #280)


## Verification Audit & Stacked Delivery Program (Epic #235, Issues #214, #217, #250)
- [x] PR #218: `fix(antigravity): make dry-run read-only and detect managed content drift` (Issues #217, #250) - commit `9ae43df`
  - Replaced `os.walk(followlinks=True)` with ancestor-tracked safe traversal in `skill_files()`
  - Prevented symlink cycle infinite loops and external target reads with negative test fixtures
  - Protected `sync_live_plugin()` with `make_skill_ignore()`
- [x] PR #219: `fix(verify): validate scaffold inputs and preserve authored targets` (Issue #217) - commit `88e5152`
  - Kebab-case application naming validation and `pstack` doctor reservation
  - Occupied directory and symlink target/ancestor write refusal
- [x] PR #220: `fix(verify): validate ordered feature maps and document proof limits` (Issues #217, #250) - commit `387eb41`
  - Corrected five-host claim to accurately distinguish six declared host census from Droid unproven native model-backed runtime operations
  - Strict ordered feature map validation against sibling Markdown files
- [x] PR #253: `feat(verify): fingerprint tool dependencies and align OpenSpec target` (Issues #214, #217, #250) - commit `3b9291a`
  - Fingerprinted verifier tool dependencies into driver revision hash
  - Added `--change` flag to `verify-portable.py` dynamically aligning OpenSpec scenario description with target
  - Handled candidate host staleness safely in `check-staleness`
  - Synchronized upstream packaging recipe string to 0.15.15
  - Regenerated 6-harness evidence receipts across all 4 planes
  - Full test suite: 455/455 green (100%)

## Epic #235: Harden pstack verification truth, route resolution, and lifecycle safety
### Phase 1: Test Partitioning & Baseline Census (PR #254, Issues #236, #243, #242)
- [x] Unit 1: Record minimal routing/proof/lifecycle decision in ADR-0017 (Issue #242)
- [x] Unit 2: Formalize 3-tier test classification in `docs/verification-test-tiers.md` (Issue #243)
- [x] Unit 3: Partition offline CI workflow in `.github/workflows/portability-offline.yml` (Issue #243)
- [x] Unit 4: Reconcile receipt schema census and Droid integration tests (Issue #236)
- [x] Unit 5: Isolate host-dependent smoke tests in `tests/test_harness_drivers.py` (Issues #236, #243)

### Phase 2: Pure Typed Route Resolver & Profile Alignment (PR #255, Issues #237, #244, #245)
- [x] Unit 6: Extract pure typed route resolution contract and matcher in `scripts/route_resolver.py` (Issue #244)
- [x] Unit 7: Eliminate substring routing collisions across all 6 harness drivers (Issue #245)
- [x] Unit 8: Reconcile profiles (`profiles/*.json`) for missing `prove-it-works`, `Read-only spawn`, and unpacked primaries (Issue #237)
- [x] Unit 9: Add route resolver test suite covering collision avoidance and precedence in `tests/test_route_resolver.py` (Issues #237, #244)

### Phase 3: Failure-First Verdicts & Bounded Subprocesses (PR #256, Issues #238, #246, #247, #248)
- [x] Unit 10: Enforce strict failure-first verdict reduction `FAIL > BLOCKED > UNTESTED > PASS` in `scripts/verify-portable.py` (Issue #246)
- [x] Unit 11: Add bounded 60s timeout handling to all harness driver command runners in `scripts/drivers/base.py` and `scripts/verify-portable.py` (Issue #247)
- [x] Unit 12: Formalize `evidence_level` (`static`, `offline`, `observed_live`, `legacy`) and `UNTESTED` in portability schemas (Issue #247)
- [x] Unit 13: Add verdict reduction and timeout test suite in `tests/test_verdict_reduction.py` (Issues #238, #246)

### Phase 4: Lossless Ownership-Aware Package Lifecycle (PR #257, Issues #239, #249)
- [x] Unit 14: Record `.pstack-managed-files.json` ownership manifest upon install in `scripts/package-lifecycle.py` (Issue #239)
- [x] Unit 15: Replace destructive `shutil.rmtree` with non-destructive file copying in `copy_skills` (Issue #239)
- [x] Unit 16: Protect unmanaged user files, custom skills, and symlinks from deletion during uninstall (Issue #249)
- [x] Unit 17: Add lifecycle safety test suite in `tests/test_package_lifecycle_safety.py` (Issues #239, #249)

### Phase 5: Swarm, Arena & Interrogate Acceptance Gate (PR #258, Issues #240, #251, #252)
- [x] Unit 18: Execute 4-lane Swarm acceptance across canonical, routing, runtime proof, and lifecycle safety (Issue #251)
- [x] Unit 19: Conduct adversarial Interrogate review across stacked diffs (Issue #252)
- [x] Unit 20: Re-run 6-harness verification matrix and refresh durable evidence receipts across all 4 planes (Issue #240)
- [x] Unit 21: Full clean offline CI suite verified: 180 passed, 6 skipped in 36.8s (Issue #240)

## Epic #259: Harden and synchronize verification skills, scaffolding, and conformance tooling across 6 harnesses
### Phase 1: Architecture & Skills Contract (Issues #260, #261)
- [x] Unit 1: Record minimal verification skill scaffolding, driver, and audit decision in ADR-0018 (Issue #260)
- [x] Unit 2: Update `create-verification-skill` and `maintain-verification-skill` with 3 tiers, evidence levels, and 60s timeout bounds (Issue #261)

### Phase 2: Scaffolding Levers & Maintenance Automation (Issue #262)
- [x] Unit 3: Add executable driver script scaffolding and `## Helpers` to `scripts/scaffold-verification-skill.py` (Issue #262)
- [x] Unit 4: Add `--audit` CLI mode to `scripts/scaffold-verification-skill.py` for `/maintain-verification-skill` (Issue #262)
- [x] Unit 5: Add comprehensive tests in `tests/test_scaffold_verification_skill.py` (Issue #262)

### Phase 3: Verifier & Durability Test Parity (Issue #263)
- [x] Unit 6: Reconcile `tests/test_evidence_durability.py` with 6-harness census, including Droid (Issue #263)
- [x] Unit 7: Update `scripts/verify-portable.py` with `SIX_HARNESSES` constant (Issue #263)

### Phase 4: Swarm, Arena & Interrogate Acceptance Gate & Stacked Delivery (Issue #264)
- [x] Unit 8: Execute 4-lane Swarm verification across canonical, routing, runtime proof, and safety (Issue #264)
- [x] Unit 9: Conduct adversarial Interrogate review across stacked diffs (Issue #264)
- [x] Unit 10: Deliver clean stacked PRs on GitHub with passing offline CI (Issue #264)
