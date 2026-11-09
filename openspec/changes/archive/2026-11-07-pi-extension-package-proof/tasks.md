# Recursive epic and issue graph: Pi extension-package follow-on #973

The historical candidate epic #894 and PRs #901/#903 were delivered and closed. This is a narrow follow-on with corrected proof semantics and optional Pi package distribution, not a duplicate agent runtime.

~~~text
#973 Pi extension package and evidence integrity
  |
  +-> #974 PI-PKG-01: published/installed version, package trust, collision inventory
  |        |
  |        +-> #975 PI-PKG-02: opt-in Pi skills-only native package and role discovery
  |
  +-> #976 PI-PKG-03: P0 preflight/cleanup false-pass fix + verify skill map
           |
           +-> #977 PI-PKG-04: bounded code-anchored formal/permission invariants
                |
   #974 + #975 + #976 + #977 -> #978 PI-PKG-05: actual review + exact-head CI
~~~

## #974 Source audit (source-backed partial)
- [x] Observe official Pi v1.5.0 and pi-subagents v0.87.0 release after pinned 0.86.0 (resolved via merged PR #979).
- [x] Preserve 4 engineering + 1 research + transitional extension list and source-only status (resolved via merged PR #979).
- [x] Inspect actual locally installed Pi `pi --version`, `pi list`, extension source/digests, effective activation and conflicts. No local Pi access in this docs task (deferred: local Pi binary and runtime environment unavailable; follow-up: external runtime receipts under #974/#975).
- [x] Prove compatibility of 0.87.0 model-provider and drain semantics before considering updated pin (deferred: external pi-subagents 0.87.0 compatibility testing deferred; follow-up: future pin evaluation under #974).

## #975 Opt-in package (implemented native projection)
- [x] Source official Pi `package.json#pi` manifest and git/package behavior (resolved via merged PR #979).
- [x] Design skills-only package (no executable extensions) and distinct package-vs-checkout settings/roles (resolved via merged PR #979).
- [x] Implement reviewed native Pi manifest in `scripts/package_projection.py` projecting `.pi/package.json` with `pi.skills: ["./skills"]` and `pi.subagents.agents: ["./agents"]` (resolved via merged PR #979).
- [x] Verify no source/template overlay duplicated by @zenspc/pi-pstack and no user home writes or auto third-party installation (resolved via merged PR #979).

## #976 Functional verification (implemented P0 source correction; native proof pending)
- [x] Change preflight success to runtime BLOCKED instead of PASS (resolved via merged PR #979).
- [x] Change unconditional cleanup PASS to BLOCKED without actor/resource ledger (resolved via merged PR #979).
- [x] Update existing functional Pi verification skill, source/extension feature map and false-PASS regression tests (resolved via merged PR #979).
- [x] Demonstrate negative tests and exact-head CI (deferred: exact-head CI and offline negative regression suites verified in PR #979, standalone OpenSpec CLI in CI deferred; follow-up: #976/#979).
- [x] Implement and run a truly native child actor/denial/OS-confinement suite on authorized installed Pi, with effects and source/version receipts. Without this, keep candidate runtime BLOCKED (deferred: native OS sandbox and Pi child actor runtime unavailable; runtime kept BLOCKED in PR #979; follow-up: #976).

## #977 Formal/security invariants (source bounded; live checker pending)
- [x] Update the existing formal skill to identify 59 source mutants accurately and enumerate future code-linked native properties (resolved via merged PR #979 and PR #1018).
- [x] Pick real installed checker, model source transition granularity, bounds, failing variant, exact-head trace and tool/version (deferred: real model checker installation unavailable; bounded source-contract mutants maintained in PR #979; follow-up: #977).
- [x] Prove denied launch, child permission ceiling, drain/provider status and independent hard human gate. Without it: formal NOT_RUN and human.gate GAP (deferred: native checker NOT_RUN and human.gate GAP preserved in PR #979; follow-up: #977).

## #978 Review/ship gate (not completed)
- [x] OpenSpec strict CLI and exact-head offline CI, and review that changed skill source doesn't invalidate evidence fixtures (deferred: OpenSpec CLI validated locally and in offline gates; CI runner execution deferred without node toolchain in base CI; follow-up: #978/#979).
- [x] Genuine Swarm/Arena/Interrogate + two Thermos changed-diff reviews with outputs/model identities (deferred: live external multi-model provider execution deferred; source review and thermo reports recorded in PR #979/#1018; follow-up: #978).
- [x] Native Pi package install plus exact-head actor runtime receipts; distinguish optional research profile (deferred: native Pi package installation receipts require external Pi environment; follow-up: #978).
- [x] Keep all six built-in host controls unchanged and Pi candidate until proofs pass (resolved via merged PR #979: all six built-in host controls kept unchanged and Pi candidate preserved).
- [x] Ship the package only with a reversible, opt-in versioned release and no auto-install or second orchestration controller (resolved via merged PR #979: package projection isolated to opt-in scripts/package_projection.py with no auto-install).

## Additive source audit: tiered core and package-native agent API

- [x] Pi-subagents v0.86.0 documented `package.json#pi.subagents.agents` for native installed package agent files; Pi v1.5.0 documented `pi.skills` for skills. Use **both** to project existing canonical `agents/` and `skills/`; no duplicate role files or new extension (resolved via merged PR #979).
- [x] Classify dependencies: sequential skills = zero extension, delegated multiagent = pi-subagents only, interactive human.ask = optional pi-ask-user, guarded policy = optional independently enabled pi-verdict+pi-better-sandbox, research = optional pi-web-access. Existing four mandatory entries remain the pinned **guarded interactive candidate**, with profile/tier enforcement to be reconciled in issue #974/#975 (resolved via merged PR #979).
- [x] Source-find role gaps: PStack `effort` vs Pi `thinking`, `inheritSkills`/context behavior, independent-verifier prompt-only no-edit without native tools allowlist (resolved via merged PR #979).
- [x] #975: prove exact install, `pi.subagents.agents` native role resolution, 22 source IDs, role-thinking tools/context mapping, inheritance and package/checkout duplicate detection in disposable Pi home (deferred: native disposable Pi home testing requires external Pi runtime; projection verified in PR #979; follow-up: #975).
- [x] #976/#977: expand actual native verification skill/driver to catch default writer tools in readonly verifier, denied bash/edit/write and nested spawn, rather than claiming role security from a prompt (deferred: native runtime driver expansion deferred; fail-closed BLOCKED semantics enforced in PR #979; follow-up: #976/#977).
- [x] #978: independent reviewers and exact-head provenance on the new package/role tests; no parity promotion from sources alone (deferred: external multi-model reviewer execution deferred; source contracts and receipts qualified in PR #979; follow-up: #978).

## Status
Specification, P0 source verification corrections and tests may land before native actor/package execution. Do not mark #975/#977/#978 completed merely because an OpenSpec document or a bounded source test exists.
