# ADR 0024: Antigravity Models and Roles Mapping and GPT-OSS Elimination

## Context

Live Antigravity CLI (`agy models`) and `swarm(action="models", all=True)` inspection confirms 15 concrete slugs across five model families, while the native `invoke_subagent` schema accepts four model-tier enum values (`pro`, `flash`, `flash_lite`, `inherit`). Previously, `.antigravity-plugin/models.json` exposed only the four abstract tier slugs without recording the concrete main driver slugs, paid Pro subscription upgrades, minimal Claude escalation policy, or explicit `gpt-oss-*` exclusion, and `skills/poteto-mode/references/antigravity-tools.md` lacked a `## Models` section matching `skills/poteto-mode/references/codex-tools.md`.

Live driver policy for Antigravity:

- `gemini-4-hydrogen-*` (`gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`, 100% quota): Main reasoning and orchestration driver backing `pro`.
- `gemini-3.8-flash-*` (`gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`, 100% quota): Main fast worker and verifier driver backing `flash` and `flash_lite`.
- `gemini-4-argon-*` (`gemini-4-argon-high`, `gemini-pro-orchestrator-g1-pro`, 98% quota): Paid Pro subscription upgrade for orchestration and frontier reasoning when available.
- `claude-opus-5-5-high` (42% quota): Kept minimal strictly for `hardest-tasks` or explicit cross-family review seats.
- `gpt-oss-*` (`gpt-oss-120b-medium`): Obsolete and strictly eliminated from all `pstack` catalogs, panels, role assignments, and override templates.

The evaluated options:

- **Replace `pro`/`flash` in `singleRoleDefault` and `available` with only concrete CLI slugs:** rejected. Breaks `invoke_subagent` schema enum dispatch and violates Contract `#429` (`scripts/eval_fast_role_task_fit.py` and `scripts/harness_scenarios.py`).
- **Preserve `pro`/`flash`/`flash_lite`/`inherit` tier keys for `invoke_subagent` and formalize concrete driver metadata, catalog entries, reference docs, and user overrides alongside them (mirroring `ADR-0016`):** selected. Keeps `invoke_subagent` and benchmark gates green while pinning CLI, Swarm, and human-readable role configuration to the live Gemini 4 Hydrogen, Gemini 3.8 Flash, and paid Pro Gemini 4 Argon drivers.

## Decision

1. Update `scripts/package_projection.py` (`generate_antigravity_models`) to emit top-level `drivers` mappings and concrete driver entries (`gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`, `gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`, `gemini-4-argon-high`, `gemini-pro-orchestrator-g1-pro`, and minimal `claude-opus-5-5-high`) while preserving `singleRoleDefault: "pro"`, `panel: ["pro", "flash"]`, and tier slugs `pro`, `flash`, `flash_lite`, `inherit`.
2. Update `skills/poteto-mode/references/antigravity-tools.md` with `## Models` (`### Model tiers`, `### Role mappings`, `### Eliminated models`) and `skills/poteto-mode/references/provider-dispatch.md` with Antigravity stock routes.
3. Update `tests/test_project_package.py` to enforce driver mappings, minimal `claude-*` confinement, and strict `gpt-oss-*` exclusion.
4. Update `~/.gemini/config/pstack-models.md` with both `invoke_subagent` tier overrides and concrete CLI/Swarm driver mappings, then synchronize `~/.gemini/config/plugins/pstack/`.

## Status

Accepted, 2026-11-14. Complements `ADR-0013` (Antigravity harness architecture), `ADR-0016` (Codex models mapping), and `ADR-0022` (fast-worker role task-fit).
