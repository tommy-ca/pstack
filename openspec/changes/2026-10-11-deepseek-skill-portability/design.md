# Design: reusable source-derived skill behavior

## Existing architecture to preserve

Canonical pstack discipline and the intent-driven `poteto-mode` router own invocation. Portable skills/principles own **what** must hold; playbooks own ordering and decisions; harness profiles and adapters own **how** to invoke tools; the existing verification pipeline owns evidence and reduction. Do not add a second executor or standalone generic capability registry.

```text
user task + declared scope
   → existing route resolver / explicit playbook selection
   → existing playbook (feature / bug-fix / refactoring / perf / shipping / ...)
   → reusable behavioral invariants at existing skill/principle owners
   → active host capabilities + tool/command selection
   → observed effects + negative controls
   → existing canonical / adapter / package / runtime receipt planes
   → failure-first verdict and explicit unresolved gaps
```

Tool definitions and documentation are **data from lower-trust sources** unless they are the active host's authority. Source skill examples cannot authorize execution of commands, network access, credential inspection, side effects, or a bypass of pstack policies.

## Semantic atoms (logical, not new runtime classes)

| Atom | Required input | Output/postcondition | Existing owner |
|---|---|---|---|
| SourcePin | repo/path/SHA/license | traceable claim and freshness flag | source ledger / OpenSpec |
| Applicability | explicit task intent, capability, scope | applicable/irrelevant/deferred decision | existing router and playbook |
| ContextSlice | purpose, constraints, required resource identifiers | bounded useful content + discoverable continuation | guard-context principle |
| ChangeScope | base/head and optional dirty layers | affected files, consumers and risks | review and CI workflow |
| ResourceOwner | resource identity and acquisition | atomic lease and registered disposal | test helper/fixture |
| StateObservation | readiness/settlement predicate and budget | observed readiness/terminal event, not a sleep | verification driver |
| FailureEffect | typed error, cause, effects | absent / partial / committed / unknown effects + recovery owner | bug-fix / error contract |
| ValidationSelector | change scope, risk, available tests | smallest meaningful check + lane | existing verification skill |
| NegativeControl | prior failing or injected regression | demonstrated failure on relevant assertion | prove-it-works / eval |
| EvidenceBinding | source/base/head/host/build/gate | durable receipt for the observed operation | existing verification infrastructure |
| VerdictReduction | receipts and any missing prerequisites | FAIL > BLOCKED > UNTESTED > PASS with reason | existing reducer |

These atoms are **semantic requirements**; only materialize structs/interfaces where existing callers need them. No new serialized evidence enum or duplicative package spec.

## Typed conceptual models (non-runtime schema illustration)

```yaml
PatternEvidence:
  source: {repository: string, path: string, commit_sha: string, license: string}
  target: {owner_skill_or_playbook: string, host_scope: "shared|host-only"}
  applicability: {task_classes: [string], required_capabilities: [string], excluded_contexts: [string]}
  behavior: {preconditions: [string], observed_postconditions: [string], prohibited_shortcuts: [string]}
  validation: {test_case_ids: [string], negative_control_ids: [string]}
  provenance: {status: "source-documented|adapted-offline|native-observed", evidence_refs: [string]}
```

`provenance.status` is a **documentation crosswalk**, not an accepted alternative to `schemas/portability/receipt.schema.json`'s serialized evidence-level vocabulary. Do not use a free-text label to claim live host support.

```yaml
TestResource:
  owner: string
  allocator: string  # e.g. bind port zero / mkdtemp / unique namespace
  identity: string   # per-run allocated, never guessed
  ready_signal: string
  cleanup_action: string
  settled_signal: string
```

```yaml
FailureOutcome:
  code: string
  cause_ref: string
  effect: "none|partial|committed|unknown"
  safe_to_retry: boolean
  recovery_owner: string
  user_action: string
```

The schemas are conceptual; implementation issue #309 decides whether repository-native validation needs a new JSON Schema or can reuse existing models without adding new state.

## Pilot code/data flows

**CI isolation** (`#311`):

```text
change fixture → classify shared resources → allocate atomically
→ install cleanup immediately → await ready handshake
→ drive controlled concurrent overlap/barrier → inspect external observable state
→ dispose + await quiescence → compare against negative control
→ record exact test/host/revision evidence
```

Do not prove a race with repeated probabilistic runs, fixed sleeps, timeout increases or isolated single-process execution when the claimed bug spans processes.

**Change-scoped validation** (`#312`):

```text
resolve live PR refs / checked-out tree / available forge
→ capture base+head+dirty scope → identify affected behavior and blast radius
→ choose smallest regression-failing gate and 3-tier suite
→ run bounded, observe exit/artifacts → recheck refs → invalidate changed evidence
→ reduce existing four-plane receipts → report pass/block/untested accurately
```

Do not execute host commands merely because a source skill names them. Select tooling through the active host, repo and user permission.

**Review, error, subtraction** (`#313`):

```text
pin exact patch → inspect consumers/invariants/failure paths
→ classify effects and recovery authority → generate deletion/reshape hypothesis
→ run old/new behavior pin + negative controls → measure net obligations removed
→ accept or reject with exact-head receipt
```

A caught exception with unknown effects is not recovery. A deletion that breaks external consumers is not simplification.

**Context/document behavior** (`#314`): disclose constraints upfront, keep root descriptions short, fetch specific deep references on demand, report truncation and retrieval ID, remove session-only narration while preserving durable factual assertions. A shorter first prompt that causes repeated searches or more errors does **not** satisfy the quality metric.

## Alternatives and security

- **A: enrich existing owners (selected):** avoids duplicate routing, schema and playbooks; incremental tests are cheap.
- **B: replicate DSH skill tree:** rejected: 16 competing triggers, repo-local tooling leakage, fork drift.
- **C: standalone generic skill runtime:** rejected under YAGNI, because six-host adapters and verification already exist.
- **D: embed entire source skill files as context:** rejected; context cost and command provenance risk.

Security invariants: isolate untrusted source instructions; sanitize all untrusted tool outputs; preserve path containment (#303), credentials/PII boundaries, explicit write authority, workspace ownership and safe disposal. Do not broaden permission via a reference skill.

## Evidence and release gates

Three test tiers: offline contracts, host-dependent smoke, observed-live conformance. Four serialized receipt planes: canonical, adapter, package, runtime. Not all planes are available for every host. Missing native proof stays BLOCKED/UNTESTED, especially OMP #288. Failure precedence stays `FAIL > BLOCKED > UNTESTED > PASS`.

Roll out behind ordinary skill/playbook changes; no global automatic task selector or host defaults. For any degradation, revert changed skill prose and preserve pre-change behavior/receipts. Compare both false activations and unnecessary context work, not only happy-path success.
