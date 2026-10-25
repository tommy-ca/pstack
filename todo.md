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

## Epic #281: Audit, clean up, and reconcile agents and droids across SOLID, DRY, and host-neutral boundaries
### Step 1: Host-neutral agent definitions and capability boundaries (Task #282)
- [x] Unit 1: Host-neutralize role descriptions and remove leaked host coupling
- [x] Unit 2: Retain capabilityMode invariant per test harness specification (no-write execute sandbox vs prompt-posture advisors)
- [x] Unit 3: Enumerate all 22 canonical roles in `pstack.package.json` under `roles` with `id`, `description`, `default_model_role` (PR #285)
- [x] Unit 4: Verify `scripts/project-package.py` Droid projection and validate 100% parity

### Step 2: Agent/droid schema verification and boundary scanner coverage (Task #283)
- [x] Unit 5: Extend `scripts/scan-host-boundary.py` to cover `agents/` and `droids/` with zero host vocabulary leaks
- [x] Unit 6: Extend `scripts/verify-harness.py` to audit full 22-agent and 22-droid population parity and stems
- [x] Unit 7: Update and add tests in `tests/test_droid_projection.py`, `tests/test_scan_host_boundary.py`, and `tests/test_verify_harness.py` (PR #286)

### Step 3: Swarm, Arena, Interrogate Acceptance & Stacked Delivery (Task #284)
- [x] Unit 8: Run Arena evaluation comparing host-neutral canonical roles vs host-specialized projection architecture (Selected Candidate 1, 38/40)
- [x] Unit 9: Run Swarm 4-plane matrix across all 6 declared harnesses (6-Harness Matrix Verdict: PASS)
- [x] Unit 10: Conduct adversarial Interrogate review across stacked diffs (Final Verdict: PASS)
- [x] Unit 11: Deliver clean stacked PRs on GitHub, merge bottom-up to main, and close issues (PRs #285, #286, #287)

## Epic #288: OMP current-head reconciliation (audit, live proof, spec reconcile)
### Phase 1: Audit and containment (Issue #303, #288)
- [x] Unit 1: Reproduce the route resolver containment escape and record that the named test passed vacuously because its sentinel cannot exist (Issue #303)
- [x] Unit 2: Contain every identifier-derived path with one helper and rewrite the traversal test against a real outside sentinel (PR #318)

### Phase 2: Native runtime proof (Issues #297, #291, #289, #296)
- [x] Unit 3: Bounded OMP RPC v2 session runner with frame reduction into the typed settlement (PR #319)
- [x] Unit 4: Opt-in live child spawn/join proof, durable `observed_live` receipt, spawn and join bindings verified with a deliberate underclaim on support state (PR #319)
- [x] Unit 5: Offline gate covers the new reducer and false-PASS regression tests (PR #319)
- [x] Unit 6: Harden the live predicate and the promotion gate after the multi-model interrogate: one child, post-prompt settlement, negotiated v2, the parent literal, and a gate that refuses a failed settlement (PR #323)

### Phase 3: Packaging arena and spec reconcile (Issues #290, #298, #295)
- [x] Unit 7: Arena over native project skills, a bare root `plugin.json`, a hybrid package and a `package.json` with an `omp` key, run as a probe with the real binary under isolated config roots; the observations are recorded in PR #295 and issue #288, not as shipped code
- [x] Unit 8: Reconcile the OMP adapter change with the merged stack, the arena observations and the live proof, twice, after the merged runtime work inverted its premises (PR #295)

### Phase 4: Verification tooling (Issue #312 core)
- [x] Unit 9: Changed-path check selection inside the existing portable verifier, with the offline gate list read from the workflow (PR #321)
- [x] Unit 10: Exact-head and working-tree evidence binding with invalidation on a dirty tree, an untracked change or a changed patch-id (PR #321)
- [x] Unit 11: `fix-ci`, `babysit` and the tier doc own the contract (PR #321; issues #312, #309, #311, #310 all CLOSED since, recorded 2026-10-14)

### Phase 5: Verification and delivery
- [x] Unit 12: Independent per-PR verdicts: escape hunt, real-consumer regression, live proof reproduction, selection re-verification, spec claim audit, hardened-predicate attack
- [x] Unit 13: Multi-model interrogate over PR #319's diff, two arms driven through the local binary on other providers; their consensus findings were folded into PR #323, and the reviewers themselves flagged that the packed diff did not include the other changes in the run
- [x] Unit 14: Merge bottom-up with a patch-id recheck per PR, receipts regenerated per host, and the live plugin reconciled to trunk
- [x] Unit 15: Close the four evidence gaps an aggregated external review found in the shipped machinery: a digest that read through untracked symlinks, a settlement that could rest on an uncorrelated frame, host IO failures escaping the driver, and a prompt comment claiming a literal the predicate never checked (PR #326)

### Follow-ups opened by this run
- [x] Unit 16: Guard `sync-antigravity-plugin --sync` against uncommitted or non-primary worktree sources (Issue #320)
- [x] Unit 17: Stop a default `verify-portable.py run --host omp` from overwriting the durable live settlement (Issue #322)

## Epic #288 and #305 reconciliation (2026-10-12)
### Verification tooling
- [x] Unit 1: Preserve a matching `observed_live` settlement across a durable refresh, mark it `preserved_from`, and drop it when the runtime surface moves (Issue #322, PR #328)
- [x] Unit 2: Refuse `sync-antigravity-plugin --sync` from a dirty, linked-worktree or non-repository source without `--force` (Issue #320, PR #329)
- [x] Unit 3: Keep `canonical-index --classify-drift` out of the tracked working tree with `--out`, leaving the recorded classification to a deliberate refresh (Issue #312 core, PR #332)

### OMP native packaging (Issues #298, #290)
- [x] Unit 4: Emit the native `package.json#omp` descriptor instead of a generated `plugin.json` OMP never reads, and verify the enrollment key on install (PR #330)
- [x] Unit 5: `scripts/prove-omp-native-package.py` proves enrollment, the skills tree through a sentinel delta, and, with `--live`, a packaged role agent spawned with `agentSource=user`, against an isolated config root with the ambient root snapshotted and uninstalled (PR #330)
- [x] Unit 6: Arena with the real binary: `omp plugin link` refuses a root `plugin.json` package (no `package.json`), and the Agent Plugins standard's closed frontmatter set rejects `disable-model-invocation`, which 49 of 58 canonical skills carry; arm B stays the shipped projection (PR #330)

### Portable quality workflows (Issue #311)
- [x] Unit 7: Resource-isolation rules in `create-verification-skill` and the matching audit item in `maintain-verification-skill`, with a Python and Node fixture pair whose colliding half is the negative control (PR #331)

### Delivery
- [x] Unit 8: Offline gate runs the three new suites; the tiers doc lists them and names the two that are tier-limited, since the OMP suite skips without the binary (PR #333)
- [x] Unit 9: Stacked PRs #328 to #334, per-PR independent verdicts, swarm lanes at each head, arena over the packaging candidates, three-model interrogate over the stack diff
- [x] Unit 10: OMP cancellation landed (runtime-child-cancel-omp observed_live); steering stays an accepted GAP with no primitive, recorded in profiles/omp.json agent.message (Issue #297 CLOSED)

### Poteto audit program (2026-10-12)
- [x] Unit 11: Pilot of program `pstack-poteto-audit-20261012`: the recursive plan and issue-graph reconciliation for epic #288 and program #305, with one section per future PR (P1–P15), a verdict table over all 21 open issues, and the offline gate subset recorded (`openspec/changes/2026-10-12-poteto-audit-reconcile/`)
- [x] Unit 12: Reopened #296 after a premature closure (two acceptance fixtures owed); #298 later closed via PRs #341 + #330, and the gated #290/#311/#312 all CLOSED since (recorded 2026-10-14)
- [x] Unit 13: P1 landed via PR #340: agent.cancel verified receipt-backed, agent.resume/session.resume/monitor static-only, schedule unverified (Issue #289 CLOSED)
- [x] Unit 14: P4 landed via PR #341 + #330: nested-skill/disabled-plugin/omp-key/precedence negatives in tests/test_omp_native_package.py (Issues #290, #298 CLOSED)
- [x] Unit 15: P9 landed via PRs #339/#346: bounded join deadline, dropout rule, evidence binding, declared-host census in swarm/arena/interrogate (verified test_playbook_parity.py)

## Poteto audit program (2026-10-14, direct: RPC-driver batch fan-out undriven; native task fan-out proven in Unit 21)
### Closures reconciled 2026-10-14 (all CLOSED; 0 open issues, 0 open PRs at reconcile time)
- [x] Unit 15a: Graph gap CLOSED 2026-10-14: archived task files record closing PRs for all four remaining issues: #306 via #348 + #350 + #353, #307 via #349 + #351 + #352 + #353 + #354-#364, #314 via #349, #315 via #354-#364 (all PRs verified MERGED). No open graph gaps remain in the tracked set.
- [x] Unit 15b: Validate-gate fixes: refresh-hygiene MODIFIED block scenarios restored (Issue #378, PR #386), skip_specs declared on two docs-only changes (Issue #379, PR #383), pstack-playbooks requirements 1-2 scenarios added (Issue #380, PR #384), installed-copy orchestrate-store conflict closed as intentional-Claude-variant classification record with docs-only direction (Issue #402, no code change), scaffold false-success fixed with honest STUB_NOT_IMPLEMENTED stub exiting 2 (Issue #423, PR #422)
- [x] Unit 16: OMP native adapter reconciliation: cancel settled live with capability-scoped gate (Issue #381, PR #387), dispatch table scoped to driven single-child task lane (Issue #388, PR #400), agent.message recorded as GAP (Issue #389, PR #399), child-resume scoped to observed behavior (Issue #390, PR #401), model/role precedence documented (Issue #391, PR #396), cancel arm in driver smoke (Issue #392, PR #397), OMP drive conventions linked then deduped to host list (Issues #393/#407, PRs #394/#409)
- [x] Unit 17: Verification truth and freshness: installed-copy freshness scoped to repo-owned deploy targets (Issue #404, commit `66c1d7a`), drift classification scoped to upstream-pin-to-HEAD (Issue #403, PR #405), offline-gate inventory reconciled for #382 then re-reconciled for the scaffold suite PR #422 added (tier doc lists all 26 workflow files, 2026-10-14), branch-payload shape fixed before field access (PR #424), dead census aliases deleted with unified verdict lattice and honest scaffold stub (PR #422), sync-requirement deltas reconciled before archiving both changes (Issue #420, PR #421)
- [x] Unit 18: Packaging and docs parity: 24 principle skills stated in spec, guides, leftover scanner, and evidence quotes (PRs #413, #416, #418, #419); porting-guide pin count corrected 23 to 24 with both count-locking tests fixed (PRs #415/#417 superseded 2026-10-14); portability contract and OMP native adapter changes archived (PRs #412, #414), skip_specs harness changes archived (PR #408)
- [x] Unit 19: Broader suite green at fix head e1546b1 (677 passed, 10 skipped, 2026-10-14): the 26-file workflow gate plus the 2 count-fix suites. Follow-up commits through 05d2001 touch only todo.md plus the README-24 test assertion, and the count suites re-ran 48 passed at HEAD 05d2001 (PRs #425 and #426 merged).
- [x] Unit 20: 2026-10-14 reconcile status: real 4-lane swarm joined with 0 dropouts (lanes 1-3 PASS, lane 4 ISSUES with stale-309-312 fix landed); 2-candidate arena ran with cross-judge (base B 35-27, grafted trim landed); full-range interrogate over ad3fabf..HEAD returned 3 Act On findings, all fixed in e1546b1. Delivery direct push, not stacked PRs: queue empty, changes are docs plus test-count correction. Unit 15a gap CLOSED in this branch: #306/#307/#314/#315 closers recorded with merged-PR evidence.
- [x] Unit 22: Swarm fix verified in todo.md scope: grep confirms no remaining open/gated language for #309/#310/#311/#312 in todo.md; gh confirms all four CLOSED. The archived 2026-10-12 reconcile task file retains its historical gated wording as a point-in-time record and is out of scope for this fix.
- [x] Unit 21: Same-turn concurrent task fan-out PROVEN on this host (2026-10-14): two task children spawned in one turn both completed PASS with evidence at head 6e79f90 (lane A: issue #378 CLOSED by #386; lane B: changes holds only archive, issue #379 CLOSED by #383). profiles/omp.json agent_fanout mapping confirmed runtime-observed; the omp-tools.md driver-undriven note covers only the RPC driver lane, not this native route.

## Epic #695 program (2026-10-22, executed, shipped)
- [x] Review: eight read-only lanes, one arena with two candidates and a cross-judge, one two-seat adversarial panel. Verdict FAIL on two blockers. Recorded in `docs/audit/thermo-nuclear-695/` (PR #721).
- [x] `boundary-gate`: rebuilt on arena candidate A, sentence-keyed reviewed prohibition, per-occurrence allowance, clause-scoped negation, profile-derived install paths, fail-closed inputs, exit contract proved as 1 leak / 0 clean / 2 bad input. PR #722.
- [x] `evidence-truth`: `Preservation(preserved, dropped)` from the canonical traversal, attempt state carried as data, atomic writes, one refusal mechanism, vacuous openspec row deleted, canonical drift reported as untested. PR #724.
- [x] `host-authority-sweep`: 22 agent descriptors made host-neutral, `how` sandbox probes deferred to the host reference, `reflect` transcript pattern, doc-sentence asserts replaced by host-set and link checks, dead guard replaced by an unconditional assertion. PR #723.
- [x] `setup-projection`: real production callers, four hardcoded path sites derived from profiles, `GOLDEN` replaced by invariants, suite registered in CI, eleven model references migrated, shared setup entry scanned. PR #719.
- [x] `hermetic-doctor`: one env map binds the whole doctor phase, `PSTACK_DOCTOR_HOME` replaced by a constructor keyword, fake `openspec` on PATH, antigravity mirror read removed, home recorded in the command. PR #727.
- [x] Receipt restamp at the merged head, after `check-staleness` showed REGENERATION NEEDED while `check-evidence` showed five PASS. `check-staleness --host all` now reads ALL FRESH. PR #731.
- [x] Merge gate: full offline gate at `88c3e5e` is 1064 passed, 10 skipped.
- [ ] Deferred with an issue: #725 isolation nondeterminism, #726 `refresh-static --host all`, #728 ambient OMP test, #729 BLOCKED overwrites PASS, #730 DSH probe scope churn.
- [x] Operator gate: #699 SemVer identity migration, approved and shipped as #733. Published label `0.15.29-preview.0` on the descriptor and all six adapters, `upstream_pin` unchanged, explicit breaking upgrade with a named retired-version error, receipts requalified with both checks clean.

## Epic #770: Code Judo Round 5 — Decompose project-package, eliminate dynamic script loaders, and unify test profile construction (CLOSED)
- [x] Unit 1 (Issue #771): Extract `scripts/package_projection.py`, eliminate dynamic `importlib` spec loader hacks across scripts and tests, and reduce `scripts/project-package.py` to a clean facade (PR #774).
- [x] Unit 2 (Issue #772): Eliminate dynamic module loaders in OMP levers (`prove-omp-vertical-slice.py`, `prove-omp-native-package.py`) by reusing canonical `reduce_verdicts` and direct lifecycle imports (PR #775).
- [x] Unit 3 (Issue #773): Deduplicate test profile construction in `tests/evidence_test_helpers.py` and `tests/test_evidence_settlement.py` using `HarnessProfile.from_dict` / `from_file`, safeguarding the 1k sprawl threshold (PR #776).
- [x] Unit 4: 6-Harness Swarm matrix verification, receipts refresh, and adversarial Interrogate review across stacked diffs.
- [x] Unit 5: Stacked PRs creation on GitHub, Babysit / merge bottom-up to main, and close issues.

## Epic #777: Code Judo Round 6 — Extract portable_verifier, prove_omp_vertical_slice, and isolate refresh_static test suite (CLOSED)
- [x] Unit 1 (Issue #778): Extract `scripts/portable_verifier.py` from `scripts/verify-portable.py`, eliminate dynamic `spec_from_file_location` loaders in consumers, and maintain entrypoint facade (PR #781).
- [x] Unit 2 (Issue #779): Extract `scripts/prove_omp_vertical_slice.py` from `scripts/prove-omp-vertical-slice.py` (844L), eliminate dynamic loader in `test_verdict_reduction.py`, and maintain entrypoint facade (PR #784).
- [x] Unit 3 (Issue #780): Extract `tests/test_evidence_refresh_static.py` from `tests/test_evidence_durability.py` (751L) to keep all evidence test files well below 750 lines (PR #785).
- [x] Unit 4: 6-Harness matrix verification, receipts refresh, and multi-model Interrogate review.
- [x] Unit 5: Stacked PRs merged bottom-up to main, and verified end-to-end workflows (6-Harness Matrix Verdict PASS, ALL FRESH).

## Epic #789: Code Judo Round 7 — Decompose scan-host-boundary and canonical-index levers, eliminate dynamic loaders, and isolate OMP RPC cancel test suite (CLOSED)
- [x] Unit 1 (Issue #786): Extract `scripts/scan_host_boundary.py` from `scripts/scan-host-boundary.py`, eliminate dynamic `spec_from_file_location` in tests, and maintain entrypoint facade (PR #790).
- [x] Unit 2 (Issue #787): Extract `scripts/canonical_index.py` from `scripts/canonical-index.py`, eliminate dynamic loaders in tests, and maintain entrypoint facade (PR #793).
- [x] Unit 3 (Issue #788): Extract `tests/test_omp_rpc_cancel.py` from `tests/test_omp_rpc.py` (814L) to bring all test files under 750 lines (PR #794).
- [x] Unit 4: 6-Harness matrix verification, receipts refresh, and multi-model Interrogate review (PASS).
- [x] Unit 5: Stacked PRs merged bottom-up to main, and verified end-to-end workflows (6-Harness Matrix Verdict PASS, ALL FRESH).

## Epic #798: Code Judo Round 8 — Decompose verify-harness, adapt-harness, and scaffold-verification-skill levers, and isolate evidence cancellation test suite
- [x] Unit 1 (Issue #795): Extract `scripts/verify_harness.py` and `scripts/adapt_harness.py`, eliminate dynamic `spec_from_file_location` in tests and cross-script calls, and maintain entrypoint facades.
- [x] Unit 2 (Issue #796): Extract `scripts/scaffold_verification_skill.py` from `scripts/scaffold-verification-skill.py`, eliminate dynamic loader in `tests/test_scaffold_verification_skill.py`, and maintain entrypoint facade.
- [ ] Unit 3 (Issue #797): Extract `tests/test_evidence_cancellation.py` from `tests/test_evidence_settlement.py` (749L) to achieve robust sub-700 line headroom.
- [ ] Unit 4: 6-Harness matrix verification, receipts refresh, and multi-model Interrogate review.
- [ ] Unit 5: Stacked PRs merged bottom-up to main, and verified end-to-end workflows.


