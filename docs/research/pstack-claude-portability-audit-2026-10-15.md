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
