# Harness adapter and JEV decision contracts — implementation map

> **Status:** implementation-derived documentation (2026-10-20; audited at `tommy-ca/pstack@dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`). A source-level audit is **not** a fresh native-host conformance run or an authenticated Jev call. Follow-up graph: [#657](https://github.com/tommy-ca/pstack/issues/657), egress [#658](https://github.com/tommy-ca/pstack/issues/658), evidence [#659](https://github.com/tommy-ca/pstack/issues/659), response/budget [#660](https://github.com/tommy-ca/pstack/issues/660), docs [#661](https://github.com/tommy-ca/pstack/issues/661).

## Current implementation reconciliation — 2026-10-21

**Current checked source:** `main@66648081fbd7b4642f38ba0b273417a8891026ba`. This section **supersedes the audit-status wording below**, which is retained as a dated historical finding record at `dea54d5`. The earlier implementation-map problems are **closed and merged**: [#658](https://github.com/tommy-ca/pstack/issues/658) (privacy/early bypass), [#659](https://github.com/tommy-ca/pstack/issues/659) (persisted receipt admission), [#660](https://github.com/tommy-ca/pstack/issues/660) (typed response/estimated spend guard), [#663](https://github.com/tommy-ca/pstack/issues/663) (canonical registry pin) and [#664](https://github.com/tommy-ca/pstack/issues/664) (official System One request/answer shape). Original [epic #657](https://github.com/tommy-ca/pstack/issues/657) and merged [PR #662](https://github.com/tommy-ca/pstack/pull/662) are closed. Do not interpret the older "Open gaps" list as current issue states.

The portable architecture still owns **12 JSON schemas**, **8 descriptive harness profiles**, **6 built-in host targets**, and a **pure role/model planner**: package `pstack.package.json#roles` owns role IDs, host profiles own declared capabilities, host-native drivers own spawn/join/isolation, and source/receipt checks own independent observed proof. Package `0.15.29-grokbuild.0` is based on canonical upstream plugin 0.15.29 at `88d47514...`, not a newer canonical version. Planned worker seats do not imply live model dispatch. Verify status from profile and current exact-head scenario receipts, never from the number of driver files.

### JEV implementation after the fixes

- `scripts/route_resolver.py` now computes baseline first, invokes `_is_egress_bypassed` before provider call, validates current canonical mapping revision and router blob, and gates advisory on a persisted calibrated evidence file. `none` and `shadow` preserve acting baseline; `advisory` remains opt-in and may modify **only eligible low-risk playbook suggestions** under its checks.
- `scripts/decision_adapter.py` now serializes **named `questions` / `answers`** System One requests/responses using `urllib`, with finite confidence handling and default-OFF operation; the legacy `results` response fallback remains. This is a unit-/fixture-tested client, **not an authenticated live provider acceptance receipt**.
- **New outstanding [#676](https://github.com/tommy-ca/pstack/issues/676):** the checked-in `references/calibrated-evidence.json` calls itself `accepted` and asserts 120 evaluated samples with 0.958 pass rate, but the validator merely checks identity, mapping digest, expiry and nonempty `eval_evidence` metadata. It does not verify independent run artifacts, blinded holdout provenance or reviewer authority. Thus `accepted` is a **declared fixture**, not independently established model accuracy or authorization.
- **New outstanding [#677](https://github.com/tommy-ca/pstack/issues/677):** paid request handling compares an in-memory, postresponse **estimated** spend figure with the configured budget. It assigns $0.001 when usage is missing and accounts only for decided responses. It does **not** enforce a hard upper charge bound for a single request, concurrent calls, or a global account. Paid use remains an operator-controlled risk and must not be advertised as strict cost containment.
- **Verification maintenance [#675](https://github.com/tommy-ca/pstack/issues/675):** the Codex `verify-decision-contract` skill now documents 135 bounded finite-state combinations, source revision mapping, a mutation negative control, and a canonical-verifier driver that refuses PASS without independently captured official commit/tree objects. This is **bounded code-level state exploration**, not TLA+/Lean proof, native harness conformance, or model-family independence.
- **Benchmark interpretation [#678](https://github.com/tommy-ca/pstack/issues/678):** `scripts/eval_fast_role_task_fit.py` uses configured hypothetical `TIER_COST_USD`, `TIER_BASE_LATENCY_MS` and `JEV_PROVIDER_ROUNDTRIP_MS` for a 12-case policy comparison. Its 21.3% modeled savings and reported latencies are **scenario assumptions/results**, not measured cost, observed wall-clock routing latency or observed JEV transport timings.

**Formal verification workflow:** [Codex decision verification skill](../../.codex/skills/verify-decision-contract/SKILL.md) and [bounded invariants feature](../../.codex/skills/verify-decision-contract/features/bounded-invariants.md). [New maintenance epic #674](https://github.com/tommy-ca/pstack/issues/674) owns the distinction between checked-in proofs and externally witnessed provider/host acceptance.

## Authority and architecture

- **Canonical behavior:** [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack), as pinned in `UPSTREAM` and `pstack.package.json#upstream_pin` (`88d47514b82e7c44f00f2b2a72ff6dd12158038c`, upstream plugin 0.15.29).
- **Port release:** `pstack.package.json#version = 0.15.29-grokbuild.0`; that suffix denotes a portability release, not a newer upstream canonical contract.
- **Portability implementation:** this repository. `skills/` owns shared semantic intent; `profiles/`, `scripts/drivers/`, host tool references, projected native manifests and receipts own host-specific mechanics.
- **Role identity:** `pstack.package.json#/roles` is the unique shipped role ID/tier registry. `examples/portability/model-role-policy.example.json` demonstrates typed host choices, **not** an independent role registry or a live availability claim.
- **Execution/control:** host runtime owns spawn/join/cancel, workspaces, session persistence and durable orchestration. Do not introduce a pstack scheduler, generic agent gateway, workflow DSL, role database or second model registry.
- **Domain overlays:** domain rules (for example QStack) apply after the shared routing boundary. They cannot authorize a blocked harness/JEV action or override human gates.

```text
 canonical skills / principles / playbooks / poteto-mode
                        |
            pstack.package.json#/roles
                        |
     host profile + capability bindings + model-role policy
              |                           |
       route resolver               pure model planner
              |                           |
         native adapter / projected package & host driver
                        |
          host-owned execution + settlement
                        |
         scenario evidence + version-bound receipt

 optional Jev side path (NOT a host executor)
 deterministic route -> explicit bypass + egress eligibility
   -> closed-set Choice -> Jev provider observation
   -> class-specific admission / durable evidence / no-change fallback
```

### Atomic ownership boundaries

| Block | Canonical implementation | Contract |
| --- | --- | --- |
| Semantic skills, principle policies, playbooks | `skills/`; `skills/poteto-mode/` | Reuse upstream intent; never embed another host's tool ID in shared semantics |
| Package & role registry | `pstack.package.json` | `roles[]`, `host_targets[]`, `host_adapters`; static metadata only |
| Host identity | `scripts/host_identity.py`; `host-id.schema.json` | Six built-in IDs; namespaced declarations are candidate by default |
| Capability/profile schema & models | `schemas/portability/`; `scripts/portability_types.py` | Descriptive claims validated independently from observed live proof |
| Host role resolution | `scripts/model_role_policy.py`, `scripts/model_role_resolver.py` | Pure planning; model catalog != observed dispatch; no JEV model-choice authority |
| Native projection | `scripts/project-package.py` | Generate host manifests/roles from descriptor; avoid hand-maintained duplicates |
| Native execution and conformance | `scripts/drivers/*.py`, `scripts/verify-portable.py` | Live host-specific scenarios and honest BLOCKED/UNTESTED outcomes |
| Evidence and staleness | `scripts/evidence_*.py`, `scripts/surface_revisions.py`, `.audit/evidence/` | Receipt is bounded to identified source surfaces; no inference from prose |
| Optional semantic decision | `scripts/decision_adapter.py`, `scripts/route_resolver.py` | Default-OFF, opt-in bounded classifier only; baseline always precomputed |

## Schema registry (current checked-in shapes)

All schemas are under `schemas/portability/`, Draft 2020-12. JSON-schema validation is supplemented by cross-document Python checks; standalone JSON Schema does not prove role/catalog/host/receipt consistency.

| Schema | Important data shape / invariant |
| --- | --- |
| `host-id.schema.json` | Built-ins `grok`, `codex`, `omp`, `opencode`, `antigravity`, `droid`; compatibility aliases `claude`, `custom`; external ID `namespace:name`. Host identity alone grants no capability |
| `capability.schema.json` | Semantic capability ID and nonempty `required_postconditions` |
| `binding.schema.json` | `host`, `capability`, `implementation_status` (`native|shim|version-gated|gap`), `enforcement` (`hard|soft|advisory`), `verification_status` (`verified|static-only|unverified|stale`), optional `primitive` and scenario-pinned `evidence_ref` |
| `profile.schema.json` | `host`, `support_state`, `bindings`, `skills_dir`, `plugin_manifest`; optional `plugins_dir`, `tool_mappings`, `skill_order`, `runtime_conventions`, `evidence_ledger` |
| `tool-mapping.schema.json` | Host-native names for reading/writing, shell, agent spawn/join, plan update and user question, with optional fanout/message/background/search |
| `runtime-conventions.schema.json` | Per-host execution/isolation/model spawn conventions; do not interpret as cross-host guarantees |
| `skill-order.schema.json` | Ordered pstack/user/builtin skill resolution rows and fallbacks |
| `package-descriptor.schema.json` | Static descriptor, role/tier and host targets, never durable task or scheduler state |
| `model-role-policy.schema.json` | `version`, `role_source='pstack.package.json#/roles'`, `hosts`, optional role constraints; host catalog, per-tier/role choices, fallback, effort and selection topology |
| `model-plan.schema.json` | Selected seat(s), role, host, selection, reason and `PLANNED|DEGRADED|BLOCKED` result; **not** execution proof |
| `evidence.schema.json` | Proof/observation claim with declared source and level |
| `receipt.schema.json` | Run, host/version, canonical/adapter/package/runtime planes, source revisions and scenario-level `static|offline|observed_live|legacy` evidence; **current** receipt contract explicitly does not bind all model-catalog hashes |

### Host support snapshot (source at audited commit)

| Profile ID | Built-in shipped target? | Declared support state | Binding-level live claim |
| --- | --- | --- | --- |
| `grok` | Yes | `packaged` | No `verified` binding |
| `codex` | Yes | `packaged` | No `verified` binding |
| `omp` | Yes | `packaged` | `agent.spawn`, `agent.join`, `agent.cancel`, `workspace.isolated` individually pinned to an OMP live receipt |
| `opencode` | Yes | `packaged` | No `verified` binding |
| `antigravity` | Yes | `packaged` | No `verified` binding |
| `droid` | Yes | `candidate` | No bindings / no live claim |
| `claude` | No — compatibility identity/candidate profile | `candidate` | No `verified` binding |
| `github:copilot` | No — namespaced candidate profile | `candidate` | No `verified` binding |

Eight profile files and eight Python driver modules do **not** imply eight fully instantiated native host packages. `verify-portable.py --host` currently enumerates the six built-ins; candidate profiles can be inspected/validated without being runnable through that entrypoint. Historical five-host `PASS` claims from earlier docs do not override current receipt state. OMP's four `verified` bindings are limited to specific observed scenarios; they do not imply complete harness support, multi-model independence, arbitrary nested spawning or durable scheduling.

### Role/model resolution

1. Resolve canonical role ID and tier from `pstack.package.json#/roles`.
2. Resolve model precedence: **explicit invocation > project override > user override > host-role override > host tier default > inherit-parent/fail-closed**.
3. Validate configured model IDs, requested effort, required capability enforcement and selection topology against typed host policy. Check model catalog discovery freshness; an unproven catalog yields a `DEGRADED` plan.
4. For a panel, make distinct **seats**; separate model-family diversity is an independently checked requirement. Cross-judge cannot label same-family evaluation as independent.
5. Translate the plan to native spawn arguments only in the respective host adapter; collect runtime settlement, model identity, workspace proof and a receipt. `PLANNED` never means `VERIFIED`.

Refer to [ADR-0021](../../adr/0021-harness-neutral-model-role-policy.md), [design](../../openspec/changes/2026-10-15-harness-neutral-role-policy/design.md), and [porting guide](../guide/12-porting.md).

## JEV / System One: exact present behavior vs accepted contract

JEV is a *decision model*, not a generative coding worker, model-role catalog, reviewer family or execution harness. Current neutral data classes are `SafeContext`, `ChoiceOption`, `ChoiceRequest`, `ScoreRequest`, `BooleanRequest`, `DecisionOutcome`, `ProviderObservation` and `SemanticDecisionProvider.decide` in `scripts/decision_adapter.py`. The wire implementation is **Choice-only**; score and boolean return abstention at phase one.

**Feature controls:** `PSTACK_JEV_ENABLED` defaults OFF; `PSTACK_JEV_MODE` is `none|shadow|advisory` and defaults to shadow only when a provider is supplied to the wrapper; `PSTACK_JEV_PROFILE` selects an allowlisted endpoint profile. `PSTACK_JEV_ALLOW_PAID` is a paid-consent switch, **not** a measured or enforced spend budget.

**Transport implementation at audit SHA:** `JevDecisionAdapter` builds `{model,state,questions:[{id,type:'choice',options}]}` and uses `urllib.request` (or injected test transport) to POST to the configured `.../v1/systemone` endpoint. It does **not** currently import or instantiate `typesafe-sdk`, despite the preferred SDK wording in [provider options](../../references/jev-provider-options.md) and historical issue #515. Built-in configuration rows in code are `opencode-zen`, `opencode-console`, `openrouter`, `typesafe-direct`; configuration and tests do not prove entitlement, live authenticated exchange, price or model quality. The constructor also accepts a caller-provided `JevProviderProfile` object with an arbitrary `api_root`, so **the endpoint allowlist applies only to built-in string profiles**, not to all possible `JevDecisionAdapter` instances.

**Wire-contract discrepancy (verified against current provider documentation):** the official [OpenCode Zen System One example](https://docs.opencode.ai/docs/zen/) and [OpenRouter's official TypeSafe SDK guide](https://openrouter.ai/docs/guides/community/typesafe-sdk) specify `questions` as a **name-keyed object** containing `type`, `instructions` and `criteria`; the response contains an `answers` object indexed by question name. The current adapter instead sends `questions: []` and expects `results: []`, which are the shapes constructed by its local mocked tests, **not the documented wire contract**. This source-level mismatch is tracked by [#664](https://github.com/tommy-ca/pstack/issues/664). Exact provider behavior remains unverified without an opt-in live fixture; do not infer a successful live request from mocks.

**Existing path** (`scripts/route_resolver.py:resolve_skill_order_with_shadow`): compute deterministic route; load `references/decision-routing.json`; build a closed-set `ChoiceRequest`; collect provider observation; in `shadow` return the baseline; in `advisory` check candidate ID, per-class threshold, optional probability margin and a freshly computed receipt's staleness, otherwise fall back. The provider response status is `decided|abstain|unavailable|invalid`.

**Open gaps — do not confuse present code with the intended security contract:**

- **[#658, P0] Egress/bypass ordering:** the wrapper currently asserts `SAFE_TO_SEND` for the **raw user query** and calls the provider before excluding slash/direct/system-two routes. The living spec prohibits assuming raw task prompts are public; regex-based secret blocking is not a positive privacy classification.
- **[#659, P1] Admission freshness:** an in-memory decision receipt made from the same observation and immediately compared against itself is **not** preexisting persisted calibration/eval proof and must not grant controlling authority.
- **[#660, P1] Response/paid controls:** confidence and probabilities need finite bounded validation; missing actual provider/model response fields and response question ID are not adequately proven; `max_spend_usd` metadata is not an enforced budget. Closed historical JEV provider tasks do not settle these new negative cases.
- **[#664, P1] Official System One wire parity:** the serializer and response parser disagree with documented questions/answers DTOs, and unit mocks embed the same nonconformant dialect. Correct via one SDK or one small transport, not a parallel implementation.
- **[#663, P1] Canonical mapping revision drift:** the applied 0.15.29 pin is `88d47514...`, but `references/decision-routing.json#source.revision` remains `d0ef80d8...`. Comparing the pinned upstream Git tree with the mapping finds the same 23 playbook IDs but **18 different canonical playbook blob SHAs** and a different poteto-mode router blob (`21993f54...` vs stored `de51c561...`). The runtime reads semantic eligibility from this map without first validating it against the applied pin. Same inventory count is not version or policy equivalence. Until #663 reconciles classifications and gates freshness, advisory mapping authority is unproven.
- **[#517] Scope:** model/fast-worker/leaf-skill selection remains research. No JEV model routing or autonomous execution authority is accepted.

**Required safe data flow (target, not a claim about current execution):**

```text
query
 -> deterministic baseline / policy gate
 -> if explicit, direct, system-two or risky: return baseline; ZERO provider call
 -> approved public summary or fixture? if no: return baseline
 -> strict bounded closed-set Choice
 -> default-OFF / optional shadow observation
 -> validate finite probabilities, exact question ID and true provider/model evidence
 -> preexisting durable calibration/eval/freshness and explicit promotion policy?
    NO: baseline
    YES: only preapproved low-risk advisory playbook hint
 -> native host routing/verification/human gates remain authoritative
```

No private code, file contents, diffs, transcripts, secrets, repository or quant risk state may be inferred safe from a short length or absence of regex matches. Explicit consent to billing is distinct from consent to transfer task data. Follow [living JEV spec](../../openspec/specs/pstack-jev-decisions/spec.md).

## Thermo-Nuclear review / SOLID-KISS-DRY-YAGNI dispositions

| Concern | Disposition |
| --- | --- |
| Side effects before route/egress gates | Fix narrowly in the JEV decision boundary, not inside every harness driver; prove `provider.decide` was never invoked on bypass |
| Synthetic evidence used as authorization | Separate observation from prior accepted promotion evidence; forbid self-approving receipts |
| Repeated model/host defaults | Keep role IDs in descriptor, host identity in shared registry and model tier policy in one validator; no copied per-host role registries |
| Structural expansion | Avoid adding TypeScript/PydanticAI runtime, separate per-provider clients, general schedulers and new workflow engine without measured value |
| Large or branching code | Prefer pure preflight decision, bounded provider call and pure admission predicate instead of extra booleans in `route_resolver.py` |
| Compatibility | Keep OFF/shadow byte-for-byte route equivalent, keep legacy aliases candidate, and do not change generated manifests just to update docs |

The upstream [Thermo Nuclear Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-review) limits diff findings to actual modified code. [Thermo Nuclear Code Quality Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-code-quality-review) looks for structural simplification and non-atomic updates. The observations above are a **baseline audit**, not a claim of a completed multi-model / native-host Thermos run.

## Reproducibility and next evidence

Run on the **candidate PR SHA** with dependencies installed; do not copy a PASS from the audited base SHA:

```sh
python3 scripts/project-package.py --check
python3 scripts/verify-portable.py doctor --host all
python3 scripts/verify-decision-contract.py --help
python3 -m pytest -q tests/test_decision_adapter.py tests/test_jev_transport_and_profiles.py tests/test_advisory_promotion.py tests/test_model_role_policy.py tests/test_portability_schemas.py
# explicitly opt-in live driver only with native CLI/configured credentials,
# isolated harmless fixture, declared scope and a durable observed_live receipt.
```

Recursive work: documentation [#661](https://github.com/tommy-ca/pstack/issues/661) can land alone; safety [#658](https://github.com/tommy-ca/pstack/issues/658) blocks any live JEV use; mapping freshness [#663](https://github.com/tommy-ca/pstack/issues/663), wire contract [#664](https://github.com/tommy-ca/pstack/issues/664), evidence [#659](https://github.com/tommy-ca/pstack/issues/659) and transport [#660](https://github.com/tommy-ca/pstack/issues/660) must independently pass negative fixtures before any advisory-promotion gate. [#517](https://github.com/tommy-ca/pstack/issues/517) remains research-only. Exact-head **Swarm** partitions tests/review by adapter versus JEV, **Arena** compares baseline-only/shadow/advisory with predeclared rubric, **Interrogate** checks privacy, false PASS, model-family independence and rollback. Mark these BLOCKED when only source inspection or one reviewer is available.
