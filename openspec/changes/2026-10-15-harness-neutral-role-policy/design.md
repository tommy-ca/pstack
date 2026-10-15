# Harness-neutral model/role mapping and pstack-claude pattern audit

Status: Proposed · 2026-10-15. Implementation requires issue graph and runtime receipts.

## Authority and provenance

1. `cursor/plugins/pstack` at `UPSTREAM` is the normative source for canonical principles, role intent, skills, router and playbooks. In this port, `pstack.package.json#/roles` is the unique local role ID/description/default-model-tier registry; host policy augments it without copying the role array.
2. `tommy-ca/pstack` is the portability implementation, not the canonical source.
3. `michael-denyer/pstack-claude` at a recorded commit is a reference port; `tools/forks.json` explicitly declares policy forks. Adopt a pattern only after a behavior and license/provenance review.
4. `tommy-ca/qstack` supplies quant-domain invariants after the host router; it MUST NOT own a pstack router or model namespace.

At audit time: target main `7700faa158558e47260565a71e7d0b6cdc95679a`; reference main `94f5ce95abe8a9dec976967d79941f631cf477cd`; canonical target pin `1dcc2bacde73ddd284803b7af28164d0436198fc`. Refresh and record those pins in evidence before implementing.

## Reusable atomic blocks (ownership / interfaces)

| Block | Owns | Must not own |
| --- | --- | --- |
| Canonical inventory | role/skill/playbook IDs and pinned source provenance | host defaults |
| Intent resolver | task -> canonical playbook and role intent | model/provider calls |
| Role policy | canonical role ID -> existing descriptor tier, spawn topology, minimal capabilities | redefining role IDs/tiers or model catalog discovery |
| Host catalog | observed models, provider/family, effort enum and evidence | global policy |
| Role resolver | input + constraints + catalog -> typed choice or explicit gap | spawning |
| Capability adapter | semantic spawn/join/cancel/resume/isolated/read-only to native primitives | playbook decisions |
| Package projector | core descriptor -> manifest/hooks/stubs/reference paths | runtime workflow store |
| Hook adapter | startup/resume/compact injection (idempotent, opt-out, trusted) | permanent session ownership |
| Receipt verifier | versioned static/live proof and model-resolution trace | suppressing gaps |
| Domain overlay | post-routing qstack quant invariants | replacement router |

### Role resolver data flow

```text
canonical role registry + playbook task
  -> required capabilities + topology + tier
  -> host profile + observed runtime model catalog
  -> constraints (security/approval/allowlists/host abilities)
  -> explicit invocation > project override > user override > host defaults > parent inheritance
  -> validate requested model IDs / family diversity / effort against observed host support
  -> {selected models, effort, reason, evidence refs} OR {gap, fallback reason}
  -> adapter translates to host-native spawn fields
  -> host-native settlement + immutable evidence receipt
```

Explicit user choices never bypass policy/approval constraints. An unavailable explicit model yields an actionable error, NOT a silent substitution. `auto` / `inherit-parent` means omit model on the spawn call; it is not a model slug. Host-detected effort sets control acceptance: unsupported tokens do not become valid by appearing in documentation. Never infer live availability from a checked-in `models.json`.

For single roles require one resolved model or documented inherit behavior. For a panel, each entry is an independently spawned seat. For a cross-judge, prefer a model family different from the candidate/parent; if independence or required diversity is impossible, mark `DEGRADED` or `BLOCKED`, never claim multi-model proof.

### Tool/control flow

```text
parent poteto-mode router
  -> call semantic capability / role request
  -> resolve against profiles/<host>.json + role policy
  -> host-native dispatch (depth-1 parent fan-out policy unless separately proven)
  -> join/settlement and verify app/test behavior
  -> evidence receipt (host binary/version, model catalog source, family, SHA, scenario)
```

No child may silently become the coordinator. Hard read-only isolation and advisory no-write prompts are different enforcement levels. Persistent task state remains host-owned. Do not import `pstack-claude`'s `~/.claude/orchestrate` store (cf. closed #402). Pi and OMP are separate adapters; an observed Pi extension feature proves nothing about OMP. Host gaps are explicit.

### Projection contract

`pstack.package.json` remains package authority; `scripts/project-package.py` remains the single projector. The new schema declares `role_source: pstack.package.json#/roles`, optional per-role constraints and per-host tiers; it must reuse exactly the existing tier values (`fast-worker`, `fast-verifier`, `strong-judgment`, `strongest`, `panel`, `adversarial-panel`). It does not redeclare canonical roles. This can initially be checked as an example. The implementation phase may incorporate it as an optional field in `pstack.package.json` or a single adjacent `model-role-policy.json`, but MUST NOT create competing role registries or separately hand-maintained host manifests. Add only a minimal resolver/validator; keep host-specific hooks/extensions in host packages.

Before accepting a Copilot or Claude host entry: implement profile, manifest, hook policy, runtime scope, identity/permission checks and a package install/uninstall smoke test. `candidate` and `mapped` do not equal `supported`. Discovered skills do not prove independent agents, hooks, or model assignment.

### Arena (architecture choice, design review only)

| Candidate | Tradeoff | Decision |
| --- | --- | --- |
| A. Copy pstack-claude wholesale | Pi/runtime features arrive quickly; forks, divergent state model and duplicated sources | Reject |
| B. Extend existing schema/profile/receipt architecture using proven patterns | Maintains canonical authority and incremental proof, minimal behavioral delta | **Select** |
| C. Build a generic agent-runtime gateway/DSL | Apparent consistency but adds a second control plane | Reject (YAGNI) |
| D. Keep prose-only mappings | No immediate cost, but model drift is untestable | Reject for model policy; retain for non-executable host guidance |

### Interrogate: pre-implementation failure hypotheses

- Role ID strings in reference `models.json` combine roles (e.g. `feature, refactoring`); do not make those compound labels canonical stable IDs.
- Host/source model IDs are volatile; a model catalog entry without live probe is static, not dispatch authorization.
- Single-family `arena` should not be documented as independent cross-model validation.
- Nested subagent and isolation semantics differ between Claude Code, Codex, Pi and OMP; verify per host/per version.
- Routing hooks may duplicate injected instructions at resume/compact, fail when trust/permissions are absent, or conflict with other plugins.
- A green generator is not a live capability receipt.
- Installing Copilot/Claude manifests could accidentally copy upstream policy forks, paths, or external state.
- Avoid replacing `qstack`'s generic-vs-quant overlay with a second decision router.

## Verification / acceptance

- Static: JSON Schema draft 2020-12, unique role IDs, resolvable skill refs, projections `--check`, portable doctor, no forbidden primitives in shared content.
- Model fixtures: unknown model, unavailable provider, stale catalog, effort mismatch, panel diversity, cross-judge independence, missing privilege, `inherit-parent`, override precedence, malformed sheet.
- Hook fixtures: on/off, no duplicate install, startup/resume/compact, absent trust, opt-out and upgrade.
- Live gates: each host install + skill discovery + role dispatch + join + cancel/resume where claimed + read-only & isolation checks + receipt-bound version evidence.
- Swarm: independent host/source slices; Arena: same design brief with no-change baseline; Interrogate: independent model-family reviewers on an exact diff. This document is a **static synthesis only**, not evidence that those parallel agent runs occurred.

No claims of PASS for tests not executed. Candidate patterns are not promoted until verifiers settle with objective evidence.
