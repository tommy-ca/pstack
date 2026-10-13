# OMP adapter architecture and decisions

**Host-neutral semantic foundation:** [semantic-building-blocks.md](./semantic-building-blocks.md) and the [pstack-portability delta](./specs/pstack-portability/spec.md). These map existing canonical artifacts and the 17 established portability capabilities; no portable scheduler, WorkPool, extra capability enum or DSL is introduced. This document covers the OMP-specific projection and verification surface.


## Semantic decomposition
```text
canonical pstack skills/principles/playbooks (unchanged semantics)
               │ host-neutral Capability / Playbook / Evidence
               ▼
          pstack portable contract
               │
               ▼
OMP host projection: package assets + profile + native driver
  ├─ skill files: skills/<name>/SKILL.md, references and playbooks
  ├─ role files: agents/<name>.md → model: "@role", tools/spawns policy
  ├─ optional extension: package.json#omp.extensions (only if essential)
  ├─ user/project configuration: OMP modelRoles, no credential copy
  └─ live proof: real OMP CLI/SDK/RPC with observed child outputs
               │
               ▼
OMP native task/eval/agent()/wait()/workpool(), session & worktrees
```

## Native capability bindings (documentation ≠ observed proof)
| Portable contract | Native OMP candidate | Design guard | Proof target |
|---|---|---|---|
| agent.spawn/join | `task` or `eval agent(...).wait()` | separate host tool paths; no fictitious wire alias | child id/output + terminal status |
| agent.message/cancel | `AgentHandle.send/cancel`, or task/agent hub by documented route | only claim for mechanism exercised | steer + cancellation fixture |
| agent.resume | OMP child/agent-hub revival where proven | `omp --resume` restores parent *session*, not proof of same child handle | cold restart & child identity |
| workspace.shared | cwd + native task, policy-controlled | prevent overlapping writers | two readers vs conflicting writers |
| workspace.isolated | `agent({isolated:true, apply:false})` or supported task isolation | verify filesystem boundary and no unapproved apply/merge | sentinel + diff/cleanup |
| workspace.readonly | constrained tool set / approval + no-writing tests | advisory unless hard isolation demonstrated | negative write probe |
| model.role | agents frontmatter `model: "@role"` + `modelRoles` | no hardcoded provider defaults; project override | chosen model receipt |
| plan/progress | native task/todo/session facilities | policy, not durable pstack database | state observable |
| session.persist/resume | OMP session tree/`--resume` | do not conflate in-memory eval kernel persistence | cold process resume |
| fan-out | `task` batch, independent `agent()` handles, optional `workpool()` | WorkPool workers are keep-alive; use fresh contexts for independent judges | per-child lineage |
| schedule/monitor | OMP jobs/Agent Hub where applicable | async jobs ≠ durable scheduler; leave schedule gap unless proved | explicit gap/limit |
| evidence.capture | pstack receipt writer around driver | OMP doesn't natively write pstack's evidence | observed command/exits/output hashes |

OMP defaults described in reference docs (e.g. `task.maxRecursionDepth=2`, `task.maxConcurrency=32`, `async.maxJobs=100`) are version-specific observations, not requirements. Eval's `agent()` uses background-job capacity rather than WorkPool concurrency allocation. Eval agent selection uses a named agent/frontmatter model role, **not** a per-call `model` parameter.

### Depth and Orchestrate parity exception
Upstream Cursor pstack `skills/poteto-mode/playbooks/orchestrate.md` (observed at its 2026-10-11 revision) allows coordinator → sub-coordinator → worker nesting (depth 3). The existing portable port's `orchestrate.md` instead deliberately uses one coordinator and flat workers, and `profiles/omp.json` advertises depth 1. These are **not equivalent behavioral contracts**. Preserve the portable flat coordinator as the default (one writer, no nested state manager) while explicitly classifying canonical nested-coordinator parity as **adapted / not-proven**; do not advertise full upstream Orchestrate depth parity. If the user requests nested tracks, the adapter MUST either demonstrate native task/eval depth, ownership, and safe join with live evidence or explicitly report the host-port feature gap. A pstack policy depth guard MUST not be mislabeled as OMP host default depth. OMP native task/eval depth checks share `resolveEffectiveSubagentPolicy()` and must be tested with forbidden child spawn and permitted root worker paths.

## Model/role resolution precedence (as implemented)

The adapter pins no provider model; every path below is host-resolved and only the receipt observes the outcome. Highest first, for an OMP task child:

1. **Explicit spawn selector** — `model` is an allowed spawn field (`profiles/omp.json:268-272`, `runtime_conventions.allowed_spawn_fields`), so a caller-supplied selector bypasses every default below. `capability_mode` and `environment` are forbidden (`profiles/omp.json:273-276`).
2. **Agent frontmatter `model:`** — a named agent may bind a role, e.g. `model: "@review"`. **Not shipped:** every `agents/*.md` declares only `effort` (e.g. `agents/bug-fix.md:4`) and no `model:`, so this rung is unused in-tree; `scripts/prove-omp-vertical-slice.py:174-193` binds the role on a temp copy because the shipped frontmatter omits it (`:177`).
3. **OMP `modelRoles` mapping** — a `@role` selector resolves through the user's `~/.omp/agent/config.yml` `modelRoles` block to a concrete selector (`scripts/prove-omp-vertical-slice.py:135-152`, `:156-171`); the adapter copies no credentials and writes only a run-local overlay (`:167-171`).
4. **Parent-session inheritance (`model: inherit`)** — all 22 `droids/pstack-*.md` carry `model: inherit` (e.g. `droids/pstack-bug-fix.md:4`) with no effort field, so a spawned droid child resolves to the parent session's active model; the portable `effort` ladder in `agents/*.md` (medium/high/xhigh) does **not** flow to droids.
5. **Profile default `pi`** — when no selector resolves, the adapter's declared default is `pi` (`profiles/omp.json:267`, `runtime_conventions.default_model`).

**Gap:** no `.omp-plugin/models.json` exists — `.omp-plugin/` holds only `package.json` — so there is no packaged model table. The `model: "@role"` binding above (`design.md:16,34`, `spec.md:26`) is a projection target, not a shipped artifact; `agents/*.md` carry effort only and droids carry `inherit` only.

## Verification plane reconciliation

The existing `pstack-portability` specification describes **three conceptual concerns** (canonical, adapter, runtime) but the authoritative `receipt.schema.json` has **four actual planes** (`canonical`, `adapter`, `package`, `runtime`). The package plane is adapter-derived and independently verifies native plugin projection and lifecycle. The accompanying [formal portability delta](./specs/pstack-portability/spec.md) MODIFIES the old three-plane requirement to make this mapping explicit while preserving the current four-key receipt. Do not collapse package into adapter or create a fifth plane.

## Data models and evidence-plane reconciliation

Use the existing `schemas/portability/receipt.schema.json` as the **only authoritative serialized receipt schema**. Its scenario `evidence_level` is exactly `static | offline | observed_live | legacy`; `documented` belongs to the separate design/source matrix, not a receipt. The existing receipt `surface_revisions` object is closed to unknown fields: any new OMP-specific fields must either be included through an explicit, backward-compatible schema change or stored in a referenced immutable evidence artifact. Do not silently output an incompatible `OMPReceipt` as though it validated against the current schema.

```yaml
# Documentation/implementation mapping; no new runtime JSON Schema
OMPBindingEvidence:
  capability: agent.spawn
  native_api: task or eval.agent
  source_omp_sha: <full-sha>
  provenance: documented | static | observed
  implementation: native | shim | version-gated | gap
  enforcement: hard | soft | advisory
  host_mode: cli | rpc | sdk
  known_limitations: [string]

# Receipts remain schemas/portability/receipt.schema.json
ExistingScenarioReceipt:
  plane: runtime
  command: "actual native command or stable scenario identifier"
  evidence_level: static | offline | observed_live | legacy
  verdict: PASS | FAIL | BLOCKED | UNTESTED
  # Additional host-specific evidence belongs in an artifact URI/path
```

Minimum evidence artifacts: exact pstack and OMP revisions, installed package checksum, profile/driver checksums, selected transport and effective mode configuration, OMP model identity where available, spawn/parent/child ids, terminal state/error, elapsed time, parent sentinel/diff, worktree cleanup, bounded cancellation record. Always redact credentials and avoid storing raw prompts containing secrets. Derive support only from mandatory **observed_live** scenarios and the current exact artifact fingerprints; keep known historical PASS receipts as `legacy`. Aggregation precedence: `FAIL > BLOCKED > UNTESTED > PASS`, with proof strength evaluated separately.

## Native verification transport selection

```text
offline: profile, schemas, generated manifest, route resolver
  └─ labels: static/offline only (never claims runtime PASS)
native OMP RPC (preferred for observable end-to-end):
  omp --profile pstack-ci-<id> --mode rpc --cwd <isolated>
  ready → optional negotiate_protocol(v2)
       → id-correlated prompt(message)
       → response (admitted ≠ finished)
       → agent events / prompt_result (yield outcome)
       → get_subagents / get_subagent_messages
       → session_settled (when background work remains)
       → bounded verification + cleanup → observed_live
alternate: SDK createAgentSession with explicitly isolated settings
  subscribe events → prompt → verify child lineage/state
    → session.dispose() → observed_live
minimum CLI smoke: omp -p / --version / plugin doctor
  useful for discovery, **not** child-lifecycle proof on its own
```

OMP RPC uses newline-delimited JSON (not JSON-RPC 2.0). It has a ready handshake, protocol negotiation, command `id` correlation, `prompt_result` and `session_settled` notifications. `prompt` success only means admitted; `prompt_result` can report `sessionSettled:false`. To claim actual finished fan-out, inspect native child terminal states and eventual session settlement. Use `get_subagents`, `get_subagent_messages`, `cancel_subagent`, `steer_subagent` where supported, with bounded host deadline and subprocess cleanup. Do not incorrectly infer completion from an `agent_end` that may be retrying or from `omp plugin list`.

For SDK tests, `createAgentSession()` may auto-discover global settings/auth and persist sessions; pass isolated settings/sessionManager and an explicit AgentRegistry for multi-session tests. Call `dispose()` after observed results. An in-memory session cannot prove disk-backed cold resume.

**Protocol mode differences:** OMP RPC/ACP set protocol-specific defaults affecting task isolation/execution, async jobs and other settings; always collect effective settings, not just user config. OMP eval's `agent()` resolves `model` through named agent/frontmatter or OMP `modelRoles`, **not** via a per-call `model` option. Its handles are process-local; job submission, wait, cancellation and cold resume are distinct capabilities. WorkPool's default reuse requires independent-context controls; `eval.workpool.freshAgents=true` is an option to test, not automatic proof of an isolated review.

## Current OMP packaging defect and host-root safety

The present `scripts/package-lifecycle.py::install_plugin('omp')` copies `skills/` and, since #299, `agents/`, and it writes a pstack-generated `plugin.json`. OMP's plugin manager refuses to link or install a tree without a `package.json`, and once linked, the `omp-plugins` provider loads `skills/` bundled next to the package. The generated `plugin.json` is therefore compatibility metadata rather than a demonstrated loader contract. #298 must test installed origin/namespace and #290 must generate an OMP-discoverable package from the single portable descriptor.

**Testing environment is not just a `--profile` flag:** OMP's plugin manager uses a profile-sensitive plugins data root (normally `~/.omp/plugins`, optionally XDG-initialized). Native npm/git/link operations are user-scoped and can overwrite a matching `node_modules/<package>` symlink. Before a plugin lifecycle test, resolve the *effective* data/plugin path, force it into a disposable isolated HOME/XDG/profile root, and assert that no link/install/uninstall target is outside that root. Never assume `--cwd` or `--scope project` safely contains npm/link installations. Preserve all unexpected files and symlink targets.

## Packaging Arena
Candidate A (minimum): first-class native `.omp/skills/` plus `.omp/agents/` projection. Pro: direct discovery. Con: per-project copying, scope/ownership risk.
Candidate B (preferred for reusable distribution): root `package.json` with valid `omp` field and conventional `skills/` + `agents/`; `omp plugin link <path>` for local proof and native install/upgrade for distributable package. Extension entry point is optional and omitted for skill-only behavior only if the loader admits it; verify with `omp plugin doctor/list`, explicit loaded skill/agent invocation.
Candidate C: custom TypeScript `ExtensionAPI` router. Rejected for the baseline: duplicates host behavior and adds executable/trust surface. Revisit only with failed proof that skills + agents cannot expose required command routing.

**Decision:** test A for discovery, then B as the primary package. Do not assume a package with an empty or missing `omp` entry loads; establish minimal valid manifest experimentally. The existing `.omp-plugin/plugin.json` may be retained only as legacy internal projection metadata, never sole evidence of installability.

### Security and lifecycle
OMP extension TS/JS runs code; `--trusted-extension` limits discovery but is not a code sandbox. Do not add hooks/extension permissions just to emulate another host. Native `omp plugin link/install/enable/disable/uninstall` needs reversible isolated-user-data tests. Installer must preserve foreign files, symlinks and project-local overrides. Test collisions and namespace routing: native project `.omp` typically outranks OMP plugins; same-named skills may have namespaced alternatives.

## Playbook recomposition
- **Swarm:** freeze independent slices, spawn distinct task agents/handles, join under deadline, classify per-worker PASS/ISSUES/BLOCKED, verify deterministic evidence. WorkPool is optional only when reuse is explicitly allowed. If replay requires cold independence, use fresh agents.
- **Arena:** freeze rubric before candidate generation; isolated independent candidates; cross-judge without reading rivals before completion; graft one artifact; run lever. Never silently apply competing isolated branches.
- **Interrogate:** independent read-only reviewers (distinct contexts, preferably model roles), no edits, structured findings with file/line/severity/evidence, dedup + disagreements, lead disposition act-on/consider/noted/dismissed. Never equate reused WorkPool context with blinded independent review.
- **Orchestrate:** map GitHub issue DAG; one owner per writable unit; no invented durable OMP scheduler; resume via issues + OMP session controls. Track canonical nested-coordinator semantics as an explicit adapted/gap dimension (see depth exception), not as verified parity.
- **Lever:** offline/static/live planes separated; test exact current head and installed package; reject stale receipts.

## SOLID / KISS / DRY / YAGNI
- Single responsibility: projection, runtime dispatch and proof collection separately.
- Dependency inversion: canonical playbooks depend on portable capabilities, never OMP tool strings.
- Interface segregation: worker brief requests only needed capabilities; reviewers do not receive writer tools.
- KISS & YAGNI: no universal runtime engine/WorkPool proxy; keep a tiny host-specific driver.
- DRY: shared capability/evidence domain from existing `profiles`, `schemas`, `scripts/drivers`.

## Arena / Interrogate outstanding decisions
- D1: Does skill-only `package.json` need `omp.extensions: []` or another valid entry? Proof via clean install and plugin list, not inference.
- D2: Which task mode (batched `task` vs eval handles) most simply supplies cancel/resume with actual evidence? Benchmark in an isolated fixture, not a speculative abstraction.
- D3: What OMP version pin/feature negotiation is stable enough to support? Gate with runtime preflight and explicit blocked capabilities.
