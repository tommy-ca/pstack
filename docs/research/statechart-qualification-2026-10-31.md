# Statechart Compiler Qualification and Portability Policy (2026-10-31)

## Executive Summary
Upstream Cursor PStack 0.15.36 introduced `skills/statechart`, which wraps a TypeScript CLI requiring Node 22.18+ (or Bun 1.1.5+ / Deno 2.0+), TLC (TLA+ model checker), Java 11+, and Mermaid diagram generation.

This document formally qualifies the statechart toolchain across PStack's six declared host environments (`grok`, `codex`, `omp`, `opencode`, `antigravity`, `droid`). Per PStack's core principles (`principle-prove-it-works`, `principle-boundary-discipline`, `principle-subtract-before-you-add`), statechart is classified as an **optional capability** with explicit `GAP`/`UNTESTED` semantics when prerequisites are absent, rather than bundling heavy third-party runtimes or executing unauthorized auto-installation.

---

## 1. Toolchain Prerequisites and Dependency Matrix

| Component | Minimum Version | Upstream Bootstrap | Multi-Harness Reality | Qualified Status |
|-----------|-----------------|-------------------|-----------------------|------------------|
| Runtime | Node >=22.18, Bun >=1.1.5, Deno >=2.0 | `mise install` or global | Varies widely across host runners | Optional / Host-provided |
| Checker | TLC (TLA+ Tools) | Java jar download | Absent on minimal agent sandboxes | Optional / Host-provided |
| JRE | OpenJDK 11+ | System package | Not bundled in lightweight runners | Optional / Host-provided |
| CLI Bundle | `statechart` binary/script | Pre-compiled TS bundle | 1,000+ line TS corpus + test fixtures | Excluded from generic core |

---

## 2. Process Lifecycle and Exit Code Semantics

The statechart process contract MUST strictly distinguish between model outcomes and infrastructure/tooling failures:

- **Exit Code `0` (PASS / Invariant Holds):** The model checker traversed all reachable states within the configured bound; no invariant was violated.
- **Exit Code `1` (FAIL / Counterexample Discovered):** The model checker found a valid state trace violating an invariant; a shortest counterexample path was produced. This is a functional outcome, NOT an error.
- **Exit Code `2` (TOOL_ERROR / Refusal / Misconfiguration):** Syntax error in TLA+ specification, missing runtime, missing Java/TLC binary, network timeout during remote check, or invalid invocation arguments.
- **Signal Death (`128 + N`, e.g., SIGKILL / 137, SIGSEGV / 139):** OOM or kill signal. Under NO circumstances may signal death be treated as `PASS` or `0`. It MUST be treated as an unrecoverable failure and labeled `BLOCKED`/`ERROR`.

---

## 3. Sandboxing, Security, and File Safety Boundaries

When an agent or host invokes statechart or TLC, the following security constraints are enforced:

1. **No Output Path Traversal:** Output artifact paths must resolve strictly within the designated temporary directory or target workspace. Paths containing `../` or pointing outside the workspace boundary are rejected with an explicit refusal (Exit Code `2`).
2. **Symlink Escape Protection:** Symlinks resolving outside the repository root or temporary sandbox must not be followed for reading models or writing generated Mermaid diagrams.
3. **No Unsanitized Shell Evaluation:** Parameters passed to TLC or Java must be passed as argv arrays, never concatenated into shell strings that could permit command injection.
4. **No Silent Auto-Installation:** Tools like `mise`, `apt`, `brew`, or `npm install -g` must NEVER be run automatically by a skill or driver without explicit user authorization and host policy grant.
5. **Deterministic Cleanup:** Scratch models, CFG files, and TLC state directories created in `/tmp` or workspace temporary directories must be cleanly unlinked in `finally` blocks, even upon failure or timeout.

---

## 4. Host Capability Resolution and Fallback Architecture

In `skills/create-formal-verification-skill/SKILL.md` and related verification workflows:

1. **Probe First:** The verification coordinator queries the active host's installed capability profile (`profiles/<host>.json`) and path environment for `statechart` and `tlc`.
2. **Direct TLC Fallback:** If `statechart` is missing but `tlc` and `java` are available, formal model checking runs directly using raw TLC with pinned `.tla` and `.cfg` files. Visualization is marked `GAP`.
3. **Missing Tooling Gate:** If Java or TLC is completely absent from the environment, the verification step MUST report `BLOCKED` or `UNTESTED`. It is strictly forbidden to claim model checking passed when the checker could not execute.

---

## 5. Downstream Integration Contract

- **`create-formal-verification-skill`**: References `statechart` as an optional counterexample visualizer, falling back to direct TLC execution without failing closed on visualization absence.
- **OpenSpec Sync Contract**: Confirms `pstack-sync-from-upstream` requirement that Statechart remains optional, preserving offline verification purity.
