# Recursive epic and issue graph — Pi extension-package follow-on #973

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
- [x] Observe official Pi v1.5.0 and pi-subagents v0.87.0 release after pinned 0.86.0.
- [x] Preserve 4 engineering + 1 research + transitional extension list and source-only status.
- [ ] Inspect actual locally installed Pi `pi --version`, `pi list`, extension source/digests, effective activation and conflicts. No local Pi access in this docs task.
- [ ] Prove compatibility of 0.87.0 model-provider and drain semantics before considering updated pin.

## #975 Opt-in package (proposed, NOT implemented)
- [x] Source official Pi `package.json#pi` manifest and git/package behavior.
- [x] Design skills-only package (no executable extensions) and distinct package-vs-checkout settings/roles.
- [ ] Implement reviewed native Pi manifest in a separate PR, exercising project-local disposable installed package, skill lookup, Pi role lookup and conflicts.
- [ ] Verify no source/template overlay duplicated by @zenspc/pi-pstack and no user home writes or auto third-party installation.

## #976 Functional verification (implemented P0 source correction; native proof pending)
- [x] Change preflight success to runtime BLOCKED instead of PASS.
- [x] Change unconditional cleanup PASS to BLOCKED without actor/resource ledger.
- [x] Update existing functional Pi verification skill, source/extension feature map and false-PASS regression tests.
- [ ] Demonstrate negative tests and exact-head CI.
- [ ] Implement and run a truly native child actor/denial/OS-confinement suite on authorized installed Pi, with effects and source/version receipts. Without this, keep candidate runtime BLOCKED.

## #977 Formal/security invariants (source bounded; live checker pending)
- [x] Update the *existing* formal skill to identify 53 source mutants accurately and enumerate future code-linked native properties.
- [ ] Pick real installed checker, model source transition granularity, bounds, failing variant, exact-head trace and tool/version.
- [ ] Prove denied launch, child permission ceiling, drain/provider status and independent hard human gate. Without it: formal NOT_RUN and human.gate GAP.

## #978 Review/ship gate (not completed)
- [ ] OpenSpec strict CLI and exact-head offline CI, and review that changed skill source doesn't invalidate evidence fixtures.
- [ ] Genuine Swarm/Arena/Interrogate + two Thermos changed-diff reviews with outputs/model identities.
- [ ] Native Pi package install plus exact-head actor runtime receipts; distinguish optional research profile.
- [ ] Keep all six built-in host controls unchanged and Pi candidate until proofs pass.
- [ ] Ship the package only with a reversible, opt-in versioned release and no auto-install or second orchestration controller.

## Status
Specification, P0 source verification corrections and tests may land before native actor/package execution. Do not mark #975/#977/#978 completed merely because an OpenSpec document or a bounded source test exists.
