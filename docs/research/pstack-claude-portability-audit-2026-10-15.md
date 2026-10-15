# Cross-port portability audit — 2026-10-15

## Audit snapshots (pin before implementation)

- Canonical: `cursor/plugins/pstack`; target `UPSTREAM` pin `1dcc2bacde73ddd284803b7af28164d0436198fc`, target version `0.15.21-grokbuild.0`.
- Target: `tommy-ca/pstack` main `7700faa158558e47260565a71e7d0b6cdc95679a`.
- Comparator: `michael-denyer/pstack-claude` main `94f5ce95abe8a9dec976967d79941f631cf477cd`; `tools/forks.json` is an explicit fork ledger.
- Domain consumer: `tommy-ca/qstack` `skills/quant-domain/SKILL.md` (generic host router precedes quant overlay).

## Parity/gap matrix

| Concern | Target baseline | Reference pattern | Judgment |
| --- | --- | --- | --- |
| Canonical semantics | `UPSTREAM` + `openspec/specs/pstack-portability` | tracks upstream + `tools/forks.json` | Retain target upstream ownership; import provenance ledger |
| Cross-host primitive mapping | `schemas/portability/binding.schema.json`, `profiles/*.json`, receipts | human-readable per-host reference mapping | Keep typed target, supplement tested equivalence table |
| Model roles | `pstack.package.json` roles, per-host projected models, Grok `defaults.toml` | `plugins/pstack/models.json` generator; per-role effort setup | Stable typed role IDs + generated mappings and live discovery |
| Claude Code | `.claude-plugin/plugin.json`, shared provider guide, no `profiles/claude.json` | native plugin, SessionStart hook, setup sheet, agents | New candidate profile, native validation proof required |
| Copilot | no `copilot` host in binding/profile/package enum | Copilot CLI + app manifest/hooks and smoke docs | Add only after package, permission and runtime probes |
| Codex | `.codex-plugin/models.json`, `profiles/codex.json`, receipt | native plugin + hook and per-skill prompt stubs | Analyze stubs/hook for conflict; avoid duplicating native behavior |
| Pi vs OMP | OMP RPC driver, plugin, measured cancel; steering gap recorded | Pi extension implements spawn/message/stop/session/worktree | Separate adapters; never infer OMP steer from Pi tests |
| Routing hooks | several host packages, per-host references | startup/resume/clear/compact hook and opt-out | Add host-native idempotency/opt-out parity checks |
| Generator consistency | `project-package.py --check` | `tools/generate.mjs --check` derives docs/prompts/roles | Extend existing projector; no second generator source |
| Lifecycle/evidence | staged support & append-only receipts | mechanism-by-mechanism Pi equivalence, offline/live markers | Adopt granularity and negative cases; preserve evidence levels |
| Orchestration state | host-owned per ADR 0006 | Claude/Pi local state conventions | Do not adopt a pstack-local competing store (#402) |
| Qstack overlay | host router first, quant invariants second | not a quant-domain system | No domain router duplication |

## Swarm-style static source coverage

- Lane A: target role/profile/schema/package review — exact paths above.
- Lane B: reference `tools/generate.mjs`, `tools/runtimes.mjs`, `plugins/pstack/models.json`, `plugins/pstack/hooks/hooks.json`.
- Lane C: Pi extension, `docs/pi-equivalence.md` and target OMP `profiles/omp.json` gaps.
- Lane D: upstream canonical playbook semantics and qstack `quant-domain` separation.

These are source-review partitions, **not executed independent swarm agents**. Real multi-agent runs are implementation acceptance tasks.

## Acceptance rubric (use for Arena and Interrogate)

1. Canonical semantics preserved, with named policy divergences.
2. Minimal state and code duplication (SOLID, KISS, DRY, YAGNI).
3. Exact native model, effort, hook and tool-contract behavior.
4. Honest per-host verification strength and evidence freshness.
5. Recoverable config/setup and no silent user-file overwrite.
6. Harness onboarding can be completed with one adapter mapping, not a router fork.

## Existing history, not reopened

Recent upstream refresh #377, OMP steering gap #389, cancellation receipt #381/#387, project-model drift #410/#411, and pstack-claude orchestration-store scope #402 were already closed by 2026-10-15. New work must link rather than duplicate them.

## Direct inventory comparison against checked GitHub main branches

Observed on 2026-10-15 from the `skills/*/SKILL.md` paths (not historical file counts):

| Source | Total skill directories | Difference to target |
| --- | ---: | --- |
| `cursor/plugins/pstack` current `main` | 54 | `in-your-own-words`, `make-bot-ui`, `sharpen` are on current canonical main, absent in target |
| `tommy-ca/pstack` target `main` | 59 | 22 role-agent definition files `agents/*.md` |
| `michael-denyer/pstack-claude` reference `main` | 61 | all 59 target skill names plus `thermo-nuclear-review` and `thermos` |

The target/reference both have eight skill names not present in **current** canonical main: `babysit`, `deslop`, `fix-ci`, `fix-merge-conflicts`, `get-pr-comments`, `make-pr-easy-to-review`, `thermo-nuclear-code-quality-review`, `what-did-i-get-done`. These are candidates for `preserve/adapt/exclude/policy-fork` classification, NOT automatically defects.

**Pin-vs-HEAD caution:** this is a **current-main inventory only**. The target's normative canonical pin is `1dcc2bacde73ddd284803b7af28164d0436198fc`, recorded on 2026-10-12; changes appearing later on canonical `main` belong to an upstream freshness delta, not automatically a pin-conformance failure. #434 must classify whether the three missing live-main skills predate or postdate that pin. Do not auto-copy them. `make-bot-ui` may be an intentional domain/packaging exclusion; verify rather than presume.

### Comparator declared fork ledger

The reference port's `tools/forks.json` currently declares **47 deliberate pstack file differences: 39 `policy` and 8 `port-feature`**. This is a necessary provenance gate, not evidence that any difference should be imported. High-risk examples include `autopilot-full` merge authority, `orchestrate` / `multi-phase-plan` local `~/.claude/orchestrate` state, and native session hooks. A reference feature must be assessed against canonical intent, target's existing host-owned state policy (ADR-0006), and native host proofs.

### Static audit dispositions (not implemented host behavior)

- **Keep** target's typed capability/profile model, package projection, receipt system, 22 role/agent registry and qstack routing precedence.
- **Borrow pattern** from comparator's generated model-role defaults, host-specific hook lifecycle, per-mechanism Pi equivalence matrix and declared policy-fork ledger.
- **Gate** Claude Code/Copilot additions on per-host native install/spawn/join/permissions; **do not transplant** comparator's Pi process manager to OMP.
- **Review separately** comparator's `thermo-nuclear-review` and `thermos` before adding new skills; avoid duplicated review playbooks without a demonstrated user-facing gap.

## Model/role recomposition decision

The comparator's `plugins/pstack/models.json` expresses roles in mixed display groups (for example `feature, refactoring`) and alias-based models (`opus`, `fable`, `sonnet`, `haiku`). That form is appropriate for the comparator's generated skill-facing documentation but should not become pstack's canonical role ID source. The target retains `pstack.package.json#/roles` and a host-specific tier mapping. Build a pure role planning contract first; test the following exact incompatibilities before promoting any runtime: host-native tool availability, model catalog visibility, effort enum, independent seat count, family diversity, hook permissions, persistent agent identity, worktree ownership, cancellation and resume. A host-neutral model resolver cannot solve native spawn/security boundaries by itself.

The original draft's `arena-runners.minimum_independent_workers=2` and `interrogate-reviewers.minimum_independent_workers=2` over-constrained the existing canonical fallback, which intentionally permits one runner/reviewer. The revised sample uses one as the minimum and permits optional per-role `seats` fan-out. This is a **portability parity correction**, not an attempt to reduce the verification demands for explicitly multi-model review requests.
