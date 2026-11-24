# Epic 1447: Antigravity Packaging Idempotency, Foreign Directory Purging, and Driver Verification Integrity

Feature specification and verification log for Epic #1447 hardening under SOLID, KISS, DRY, and YAGNI.
Tracks Units 1 through 4 across stacked pull requests with multi-model verification gates.

## Specs

S1. Eliminate self-circular import in `scripts/package_install_staging.py`, stage native Antigravity skills, add `try...finally` restore guard to `stage_antigravity_native_install`, and fix `driver.sh` path resolution.
S2. Unify `STRAY_PLUGIN_DIRS` constant across `sync_antigravity_plugin.py` and `package_install_staging.py`, purge foreign directories (`.codex-plugin`, `.claude-plugin`, `.antigravity-plugin`) during `sync_live_plugin()`, remove retired `hooks.json` from `profiles/antigravity.json`, and expand sync tests.
S3. Harden `AntigravityDriver.isolation()` with `is_available()` check and `BLOCKED` fallback, validate supported isolation modes, expand `tests/test_antigravity_verification.py`, and parametrize `tests/test_project_package.py` role catalogs over Antigravity.
S4. Execute Arena, Swarm, Interrogate, and Thermos review gates across all changed surfaces, refresh 6-harness static receipts, open stacked PRs, land bottom-up into `main`, and sync live plugins.

## Tasks

- [x] T1 (linked: S1, route: inline, commit: 7334ff2) Stage Antigravity commands, add try-finally restore guard, and fix driver.sh pathing
- [x] T2 (linked: S2, route: inline, commit: a91f6d8) Unify STRAY_PLUGIN_DIRS, purge foreign directories on sync, and expand sync test coverage
- [x] T3 (linked: S3, route: inline, commit: b6c2fb4) Harden AntigravityDriver.isolation() and expand driver/role catalog test suites
- [x] T4 (linked: S4, route: inline, commit: cb6d6dc) Execute multi-model gates, refresh static receipts, and ship stacked PRs to main

## Log

L1. /goal /pstack:poteto-mode clean up worktrees, deep review, audit the above, analyze repo with graphicle, with SOLID, KISS, DRY and YAGNI, with thermos, recursive plan and update epics/issues graph, with swarm, arena, interrogate, new stacked prs, ship the stack then
