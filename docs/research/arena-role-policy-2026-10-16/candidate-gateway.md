# Candidate D2 — Provider-independent runtime gateway (faithful steelman, then verdict)

Scope: `/tmp/arena-design/brief.md` asks for the *minimal seam*. D2 does not answer that question; it answers a different one — "is the seam cheaper if one process owns routing, spawn and workflow state?" This brief argues D2 at full strength, names every boundary it crosses, and records the condition that would flip the rejection. It is deliberately the candidate the frozen rubric and the change proposal both name and reject (design.md Arena row C: "provider-independent agent runtime and persistent workflow DB … Reject"; proposal.md Non-goals: "No new workflow engine, scheduler, database, provider proxy … or new gateway").

## (a) Data shape

One resident gateway process per user; harnesses talk to it over a narrow RPC instead of planning model choice themselves.

```jsonc
// 1. route: the one place role -> model/effort is decided
{ "role": "interrogate-reviewers",        // canonical ID, unchanged
  "host": "omp",                          // observation venue
  "selection": "panel", "seats": 3,
  "models": [{"provider":"anthropic","model":"claude-sonnet-4-5","family":"anthropic","effort":"high"},
             {"provider":"openai","model":"gpt-5-codex","family":"openai","effort":"high"},
             {"provider":"google","model":"gemini-2.5-pro","family":"google","effort":"high"}],
  "source": "gateway-registry", "evidence_level": "gateway-observed",
  "catalog_seen_at": "2026-10-16T02:09:00Z" }

// 2. spawn: lifecycle owned by the gateway, not the host
{ "handle": "gw-7f3c", "role": "...", "seat": 0, "harness": "omp",
  "native_ref": "task:UpperHorse", "state": "running", "isolated": "worktree:/tmp/gw-7f3c",
  "receipt": "gateway://receipts/gw-7f3c.json" }

// 3. workflow store: durable, gateway-owned
{ "run_id": "arena-436", "nodes": [{"id":"cand-a","state":"done","handle":"gw-7f3c","artifact":"/tmp/..."}],
  "edges": [["cand-a","judge-1"]], "resume_token": "arena-436@7", "host_state": "shadow" }
```

Canonical role IDs are read from `pstack.package.json#/roles` (22 roles, six tiers) and copied into the gateway registry at first start — the copy is the point: it is what makes the gateway the single described resolver instead of a per-host planner.

## (b) Boundary / ownership table

| Concern | Today (host-owner) | D2 owner | Boundary crossed |
| --- | --- | --- | --- |
| Role IDs / tiers | `pstack.package.json#/roles` | gateway copy at boot | **Second authority for role IDs** — drift is undetectable until a boot-time hash check exists (rubric C1). |
| Model availability | host session at dispatch | gateway catalog probe | **Invented availability.** In-repo catalog is static inventory, never dispatch authorization (design.md; `scripts/model_role_resolver.py` docstring). Only the host can observe `resolvedModelIdentity`. |
| Explicit user model choice | host argparse/config | gateway route table | User intent is parsed twice and can diverge from the host's own parser. |
| Spawn / join / cancel | `task`, `spawn_agent`, `spawn_subagent`, `invoke_subagent`, `session message` … | gateway `handle` | Reimplements five primitives per host; must translate per host on **every** release because the field names above already differ per host (see evidence below). |
| Isolation | host worktree/sandbox flags | gateway-managed worktree | Duplicate isolation semantics; "hard" vs "soft" enforcement levels already differ per host and are receipt-verified per host, not centrally. |
| Workflow state | host-owned session/task state | gateway SQLite/JSON store | **Explicitly forbidden durable store** (design.md "#402": do not import `~/.claude/orchestrate`; proposal non-goals). |
| Receipts | per-host receipt bound to host binary+version+scenario | gateway receipt | A gateway receipt proves the *gateway* dispatched; it is one hop removed from `evidence_level: observed_live` unless the host round-trip is also captured. |
| qstack overlay | post-router quant invariants | gateway rule hook | qstack becomes a second router instead of an overlay — rejected in design.md authority clause. |

Evidence for the adapter cost (all from `profiles/<host>.json`, 7 profiles):

| capability | codex | omp | opencode | grok | antigravity |
| --- | --- | --- | --- | --- | --- |
| agent.spawn | `spawn_agent` | `task` | `task` | `spawn_subagent` | `invoke_subagent` |
| agent.join | `wait_agent` | `task (completion/wait)` | `task` | `get_command_or_subagent_output` | `manage_subagents` |
| agent.message | `send_message` | **gap** | `session message` | `spawn_subagent (resume)` | `send_message` |
| agent.cancel | **gap** | `proc://<id>/kill` | `task cancel` | `kill_command_or_subagent` | `manage_subagents (kill)` |
| agent.resume | `resume_agent` | `omp --resume` | `opencode --continue` | `spawn_subagent (resume_from)` | `send_message / reactive resume` |

No two hosts agree on a name; two cells are already declared **gap** (codex.cancel, omp.message). A gateway that claims provider-independence must model those gaps as first-class states anyway — i.e. it inherits the N-adapter matrix it was meant to erase, and additionally owns the risk of silently papering over a gap as a no-op.

## (c) The honest case for D2 — and why it is not enough

Strongest argument: (1) the seam matrix is N×5 and genuinely growing — `droid` is `candidate` with all five bindings absent, `claude`/`copilot` are named but unprofiled, so the per-host adapter count is going *up*; (2) model identifiers are volatile and re-discovered per host per session, so N hosts means N copies of the discovery+validation+fallback ladder — one process removes that duplication; (3) cross-host workflow continuation (start in omp, resume in codex) is impossible with host-owned state.

Rebuttal, in order: (1) a gateway does not reduce the adapter count, it renames it — the host still owns the only real spawn primitive and the host still knows its own model catalog; a gateway only centralizes the *policy*, which the description explicitly keeps host-owned; (2) the fallback ladder is 40 lines (`scripts/model_role_resolver.py`) and is already pure, testable and shared; duplicating it into a daemon trades a function for a process; (3) cross-host continuation is not a requirement in the brief, and satisfying it requires the durable store that is banned. The gateway's real product — "one place that knows your models" — is exactly what `profiles/<host>.json` + the typed planner already deliver at zero new failure modes. Score against the frozen rubric: C1 weak (second authority), C2 weak (second control plane + store), C3 weak (availability inferred, auth/isolation imitated), C4 moderate (uniform receipts, but one hop from live evidence), C5 weak (hidden durable store; qstack hook re-router). Estimated 1/1/2/2/1 — dominated by any surviving variant of B.

## (d) What D2 rejects, and what would change the verdict

D2 rejects the minimal seam itself: it rejects host-owned availability facts, host-owned lifecycle, host-owned workflow state, and the single-source role registry. Each rejection is a rubric violation, not a tradeoff.

Alternatives considered and rejected:
- **A — Copy the comparator port wholesale.** Cheaper adapters now, but 48 declared policy forks (47 pstack + 1 thermos-group at pin `94f5ce95…`) enter the repo and become a competing router and store. Rejected on C1/C5.
- **B — Typed descriptor + pure planner + thin native adapters.** Canonical roles stay in one place, host catalogs stay evidence-backed, no second runtime. Selected; this is the seam the brief asks for.
- **D — Prose-only mappings.** Zero cost, but model drift becomes untestable; retained only for non-executable guidance.
- **D2-a — Gateway *without* the store** (stateless route+receipt broker). The honest residual: it still needs host round-trips to observe availability, so it degrades to a network hop in front of the planner already in `scripts/`. Rejected as YAGNI with a real latency and failure-mode cost.
- **D2-b — Gateway owning only spawn lifecycle.** Rejected: the five primitives differ per host by name and by enforcement level ("hard" vs "soft") and are already receipt-verified individually; centralizing them removes the host-native proof the rubric's C3/C4 depend on.

**Flip condition (recorded, not speculative):** adopt a bounded broker only if, after ≥3 hosts are `verified` with live receipts, evidence shows (i) the planner duplicated ≥3× with *divergent* fallback behavior, or (ii) a required cross-host resume becomes a real product requirement. Even then the broker MUST NOT own model policy, role IDs, or durable state — it may only fan out typed plans and normalize receipts. As of this assessment (7 profiles, 2 declared capability gaps, 0 cross-host resume requirement) the condition is not met, so D2 is rejected on all three explicit fences of the brief: second control plane, second workflow runtime, hidden durable store.

Evidence used: `pstack.package.json#/roles` (22 roles), `profiles/{antigravity,codex,droid,grok,omp,opencode}.json`, `scripts/model_role_resolver.py` (planning-only, `evidence_level=static-planning-only`), `openspec/changes/2026-10-15-harness-neutral-role-policy/{design,proposal}.md`, repo head `ae06ef1`. No file in the repository was modified.
