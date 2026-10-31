# Statechart Compiler Qualification Analysis

## Overview
Upstream commit #977 added `skills/statechart`, featuring a TypeScript CLI that compiles statecharts, checks TLA+ invariants with TLC, and renders Mermaid diagrams.

## Qualification Criteria and Findings

1. **Runtime Requirements:**
   - Requires Node 22.18+ / Bun 1.1.5+ / Deno 2.0+, plus Java and TLC for formal model checking.
   - Most lightweight agent sandboxes lack Java/TLC pre-installed.
2. **Failure and Exit Codes:**
   - 0: Successful compilation / invariant verification.
   - 1: Model counterexample found.
   - 2: Tool/runtime/refusal failure.
   - Missing Java/TLC/network must return code 2 (BLOCKED/UNTESTED), never code 0 (PASS).
3. **Security and Boundary Testing:**
   - Output paths must not allow directory traversal or symlink escape out of temporary working areas.
   - Command injection via state/action labels must be strictly prohibited.
4. **Corpus Size:**
   - Upstream added 356 static fixture files. Importing all fixtures blindly adds repository bloat without adding multi-harness portability.
5. **Port Packaging Policy:**
   - Statechart compiler is designated an **OPTIONAL** feature.
   - When Java/TLC is unavailable on a host, formal verification procedures run the underlying logic or report GAP rather than faking visualization.
