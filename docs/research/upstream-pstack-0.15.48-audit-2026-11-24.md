# Repository Audit (Graphicle, SOLID/KISS/DRY/YAGNI) and Upstream 0.15.48 Delta

**Date.** 2026-11-24
**Scope.** Worktree and live plugin hygiene, Graphicle structural analysis, and Cursor PStack `0.15.43` to `0.15.48` reconciliation.
**Linked Issue.** Epic #1436, Unit 1 (#1437).

## Worktree and Live Plugin Audit

- `uv run python scripts/worktree_protocol.py check` passed with a single primary checkout `/home/tommyk/projects/pstack` on `main`.
- `skills/swarm/scripts/refresh_hygiene.py` retained `.worktrees/upstream-cursor-plugins` as the `primary overlay cache` and flagged one external stale skill at `/home/tommyk/.grok/skills/reflect/SKILL.md` (`claude-shaped`).
- `uv run python scripts/verify_portable.py prune-ephemeral --keep-last 5` pruned 31 stale ephemeral run directories and kept 30 recent runs (`0.2 MB` freed).
- `uv run python scripts/sync_antigravity_plugin.py --check` and `uv run python scripts/package_lifecycle.py verify --host all` detected drift on `skills/technical-writing/SKILL.md` in installed live plugin directories after PR #1432, and `~/.gemini/config/plugins/pstack` carried an obsolete `.antigravity-plugin/plugin.json` (`0.15.29-preview.0`) shadowing root `plugin.json`.

## Graphicle Analysis and SOLID, KISS, DRY, YAGNI Findings

Code graph extraction via `mise x -- graphicle graph extract . --code-only` indexed 396 code files into 5,162 nodes, 13,916 edges, and 243 communities with zero unverified code nodes and zero missing-endpoint edges.

- **File Size Discipline (SRP).** All Python modules in `scripts/` and `scripts/drivers/` remain under 850 lines (`prove_omp_vertical_slice.py` 844, `eval_blinded_pstack.py` 830, `portability_types.py` 813, `drivers/omp.py` 798). No file exceeds the 1,000-line boundary.
- **Architectural Hubs (DIP / ISP).** Graphicle `god-nodes` identifies `resolve_profiles_dir()` (106 edges), `resolve_skill_order()` (77 edges), `resolve_skill_order_with_shadow()` (71 edges), `DriverScenarioResult` (66 edges), `ProviderObservation` (65 edges), `VerificationReceipt` (61 edges), and `compute_surface_revisions()` (57 edges) as the canonical dependency hubs.
- **DRY Violation in Antigravity Rules Projection.** Both `scripts/package_install_staging.py` and `scripts/prove_antigravity_native_package.py` independently hardcode slightly different `rules/AGENTS.md` text containing the typo `levereable`. Unifying this behind `generate_antigravity_rules()` in `scripts/package_projection.py` eliminates duplication and drift.
- **Boundary Separation (DIP / OCP).** `AntigravityDriver` (`scripts/drivers/antigravity.py`) and `scripts/harness_scenarios.py` depend on `profiles/antigravity.json`, so updating `antigravity.json` and `antigravity-tools.md` automatically propagates capability checks without rewriting host-neutral verifier logic.

## Upstream Cursor PStack 0.15.43 to 0.15.48 Delta

Comparing `UPSTREAM` pin `2f87c854fe3e2fcda44ca86b46ede35aad3c46b7` (`0.15.43`) against upstream `origin/main` at `ca782ed8b3c2c521cead8e1720d55c3a5dbf2347` (`9e278fe`, `0.15.48`) yields 5 upstream commits touching `pstack/`.

1. `#1283` (`e58dd04`) and `#1284` (`dd24b67`). Route the upstream Gemini panel seat from `gemini-4-carbon-high` to `gemini-4-neon-xhigh` across `poteto-mode`, `arena`, `setup-pstack`, and `README.md`. In Portable PStack, shared `skills/` remain host-neutral (`scan_host_boundary.py`), so Gemini 4 Neon model routing is reconciled in Antigravity's model catalog and tool references in Unit 2.
2. `#1292` (`0b46ec3`). Adds native Windows execution and CRLF `\r\n` TLC output parsing to `/statechart` (`skills/statechart/SKILL.md`, `scripts/frontends/dot.ts`, `scripts/janitor.ts`, `scripts/kill.ts`, `scripts/run.ts`, `scripts/statechart.ts`, `scripts/test/cli.test.ts`, `scripts/test/messages.test.ts`). All runtime fixes and `messages.test.ts` port directly; `cli.test.ts` stays excluded under `EXCLUSIONS["skills/statechart/scripts/test"]` in `scripts/canonical_index.py`.
3. `#1324` (`2dd5c0c`) and `#1326` (`9e278fe`). Adds the host-neutral `/reframe` skill (`skills/reframe/SKILL.md`) with ambiguous-problem disambiguation and integrates it into `skills/poteto-help/SKILL.md`, `docs/guide/02-poteto-mode.md`, and `README.md`.
