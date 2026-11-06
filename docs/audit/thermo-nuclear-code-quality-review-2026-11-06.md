# Thermo-Nuclear Code Quality Review: Native Antigravity Plugin Package & Lifecycle (2026-11-06)

**Target**: Epic [#923](https://github.com/tommy-ca/pstack/issues/923) / Issue [#924](https://github.com/tommy-ca/pstack/issues/924)  
**Base Revision**: `main` (commit `5a06e40`)  
**Scope**: Whole-repo maintainability, Antigravity plugin packaging, verification tooling, worktree hygiene  
**Review Standards**: SOLID, KISS, DRY, YAGNI, Thermo-Nuclear Maintainability  

---

## 1. Executive Summary & Code Judo Opportunities

The codebase adheres strongly to architectural principles and typed contracts. However, the Antigravity integration currently incurs friction and technical debt:
1. **Packaging & Installation Friction**: Installation currently depends on a 475-line custom Python script (`scripts/sync_antigravity_plugin.py`) that performs manual tree syncing and diffing, rather than using the native `agy plugin install` and `agy plugin validate` primitives provided by the Antigravity CLI.
2. **Strict Validation Warnings**: Running `agy plugin validate . --strict` fails with 4 warnings:
   - Unknown field `agents` in `.antigravity-plugin/plugin.json` (Antigravity discovers `agents/` automatically).
   - Unknown field `commands` in `.antigravity-plugin/plugin.json` (plugins expose skills, not standalone commands).
   - Precedence conflict between `.antigravity-plugin/plugin.json` and root `plugin.json`.
   - `skills/poteto-mode/SKILL.md` body size is 24,217 bytes (exceeds the 24,000-byte Antigravity threshold by 217 bytes, triggering automatic truncation upon load).
   - Missing plugin logo (generic icon fallback).
3. **Docs Sync Divergence**: `tests/test_verify_docs_sync.py` failed due to `.grok/skills/verify-pstack/features/leftover-scanner.md` missing recent skip files (`cross-port-semantic-delta-2026-11-06.md` and `pstack-claude-forks-2026-11-06.json`).
4. **Worktree Confinement**: `python3 scripts/worktree_protocol.py check` verified 100% confinement, with 0 secondary worktree leaks.

---

## 2. SOLID, KISS, DRY, YAGNI Analysis & Code Judo Plan

### Principle 0: Be Ambitious About Structural Simplification (Code Judo)
- **Move**: Modernize `scripts/package_lifecycle.py` to directly execute native `agy plugin install` and `agy plugin validate` for Antigravity, while retaining idempotent offline fallback for environments lacking the `agy` binary.
- **Move**: Clean up `.antigravity-plugin/plugin.json` projection to emit only valid schema fields and add a clean SVG logo (`assets/logo.svg`).

### Single Responsibility (SRP) & Interface Segregation (ISP)
- `scripts/package_projection.py`: Each host generator (`generate_antigravity_manifest`, etc.) produces strictly the schema that the target host's native plugin manager accepts.
- `skills/poteto-mode/SKILL.md`: Streamline prose to bring the file from 24,217 bytes down to ~22,500 bytes. All 24 principles, 23 playbooks, and non-negotiable rules remain intact with tighter, unslopped phrasing.

### DRY & KISS
- Eliminate divergent manual copy logic: native `agy plugin install` handles file placement and component discovery directly.
- Consolidate validation so `package_lifecycle.py verify --host antigravity` runs `agy plugin validate` when `agy` is present.

### YAGNI
- Remove unused/ignored manifest keys (`agents`, `commands` in `.antigravity-plugin/plugin.json`).
- Avoid generating unused command tomls for Antigravity, as slash commands are derived from skills.

---

## 3. Worktree & Hygiene Verification

- **Confinement Check**: `python3 scripts/worktree_protocol.py check` -> `PASS`.
- **Worktree Audit**: `skills/poteto-mode/scripts/worktree-audit.sh` -> 0 secondary trees.
- **Disk Health**: 376GB used / 580GB available (40% utilization on `/dev/sdd`).
