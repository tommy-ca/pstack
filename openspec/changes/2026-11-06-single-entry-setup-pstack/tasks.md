# Recursive implementation and validation plan — epic #948

Source discovery + formal specs can proceed as one reviewable intent PR. No runtime merge is claimed by this PR.

~~~text
#948 One setup-pstack skill (epic)
  |
  +-> #949 SP-01: source/caller inventory + owner boundaries
        |
        +-> #950 SP-02: OpenSpec single-entry/reference and profile authority requirements
              |
              +-> #951 SP-03: merge Grok setup into setup references; migrate, retire old skill
              |
              +-> #952 SP-04: canonical packaged profiles + deterministic root mirror
                      |
            #951 + #952 + #950 -> #953 SP-05 exact-head review and acceptance
~~~

## SP-01 — #949 Source and consumer inventory
- [x] Inspect official setup-pstack, local two skills, 4 Grok references, profile layout and typed setup projection.
- [x] Identify the nine existing profile setup dispositions and existing closed #703/#937 work.
- [ ] Freeze a complete indexed caller inventory and actual applied UPSTREAM pin against latest candidate, including all config readers.

## SP-02 — #950 Existing OpenSpec capability update
- [x] Draft source-attributed proposal, ADR, typed delta, code/data flow and GIVEN/WHEN/THEN scenarios.
- [ ] Independently review scope/compatibility with live `pstack-setup-overlays` and role resolution; run OpenSpec validator where available.
- [ ] Confirm staged `skill` -> `reference` compatibility transition and profile authority contract.

## SP-03 — #951 One public setup implementation
- [ ] Move Grok instructions/assets under `setup-pstack/references/` and preserve native safety.
- [ ] Add profile-selected, path-confined reference dispatch; migrate all required readers, schemas, docs, manifests, tests.
- [ ] Remove Grok skill only after proof; preserve upstream setup/budget/panel and optional verifier semantics.

## SP-04 — #952 Profile single-source compatibility
- [ ] Make packaged setup profiles the only editable source.
- [ ] Generate root compatibility mirror idempotently using existing projection machinery.
- [ ] Verify schema, byte identity, tests for stale mirror and installed/repo resolution, protect user-owned files.
- [ ] Only propose root mirror removal once no live reader/package constraint requires it.

## SP-05 — #953 Review and shipping
- [ ] Actual Swarm coverage review and honest dropout accounting.
- [ ] Actual Arena equal-brief candidate comparison, independent judge or explicit skipped state.
- [ ] Interrogate independently rerun each claimed defect.
- [ ] Both Thermos changed-diff reviews, OpenSpec validation, targeted tests, six-host doctor and native proof where available.
- [ ] Exact-head CI and PR review; merge stack in dependency order when proven.

## Acceptance boundary
Do not copy execution orchestration into PStack; do not add a second router, new registry or unsupported native host setup. `qstack-mode -> poteto-mode` remains the downstream dependency. Every unexecuted acceptance step remains unchecked; static specification acceptance is not native conformance.
