# ADR 0016: Codex Models and Roles Mapping and GPT-5.6 Terra Elimination

## Context

Codex host configuration and portability profile previously lacked a formal models projection and used stale model generations (`gpt-5.6-sol`, `gpt-5.6-luna`), and intermediate generation mid-tier model `gpt-5.6-terra` lingered in candidate sets. Live environment inspection of the Codex models cache (`~/.codex/models_cache.json`) confirms the current frontier generation:

- `gpt-6.1-sol`: Primary workhorse and deep reasoning model (priority 1).
- `gpt-6-astra`: Balanced frontier panelist and cross-judge (priority 2).
- `gpt-6-luna`: High-throughput volume and fast execution model (priority 4).

The legacy model `gpt-5.6-terra` is obsolete and must be eliminated from all active roles and candidate panels.

The evaluated options:

- **Keep ad-hoc text overrides without package projection:** rejected. Lacks drift detection, automated validation, and multi-harness parity.
- **Mirror the Antigravity projection model by projecting `.codex-plugin/models.json` from canonical definitions:** selected. Provides zero-drift verification via `scripts/project-package.py --check` and clean harness symmetry.

## Decision

1. Update `profiles/codex.json` to declare `default_model: "gpt-6.1-sol"`, complete tool mappings, and formalize the 3-tier skill order table.
2. Update `skills/poteto-mode/references/codex-tools.md` with symmetrical tool actions, full skill order table, and comprehensive models documentation.
3. Update `skills/poteto-mode/references/provider-dispatch.md` stock routes for Codex.
4. Extend `scripts/project-package.py` to project `.codex-plugin/models.json` with three-tier models (`gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna`) and strictly eliminate `gpt-5.6-terra`.
5. Update `~/.codex/pstack-models.md` to map roles to the latest generation.
6. Regenerate 5-harness verification receipts to reflect the updated skills tree hash and profile revisions.

## Status

Accepted, 2026-10-07. Complements `ADR-0012` (package projection) and `ADR-0015` (symmetric host reference mappings).
