# ADR: Standalone Pi 1.5.0 Candidate Adapter and Minimal Extension Set

**Status:** ACCEPTED (Epic #894, PR #901, PR #903). Standalone Pi remains a namespaced candidate host (`pstack:pi`).

## Context

Pi 1.5.0 is an extensible coding agent CLI with an npm-based extension ecosystem. Integrating Pi into PStack requires mapping PStack's 17 portable capabilities without introducing host lock-in, duplicate orchestration engines, or unauthorized runtime security bypasses. Three architectural approaches were evaluated: Option A (Candidate Minimal: native Pi tools + 4 engineering + 1 research extensions), Option B (Monolithic Multi-Engine: `pi-dynamic-workflows` + `pi-goal` + `todo-list`), and Option C (Legacy Fork: `@zenspc/pi-pstack`).

## Decision

Adopt Option A (Candidate Minimal).
1. Declare candidate host identity as `pstack:pi` in `profiles/pstack-pi.json` mapping all 17 capabilities to native tools or version-gated extensions.
2. Pin minimal essential extensions in `references/pi-essential-extensions.json`: `pi-subagents@0.86.0` (delegation), `pi-better-sandbox@0.14.1` (OS policy), `pi-verdict@0.16.0` (pre-tool-call authorization), and `pi-ask-user@0.17.2` (structured interaction).
3. Discover canonical PStack skills from `../skills` and agents from `../agents` via `.pi/settings.json` with zero automatic package installations.
4. Enforce fail-closed verification via `scripts/prove_pi_vertical_slice.py` emitting four-plane receipts (`canonical: PASS`, `adapter: PASS`, `package: PASS`, `runtime: BLOCKED`), rejecting unobserved runtime claims.
5. Standalone Pi is not enrolled as a 7th shipped host until live hardware execution is certified with real extension receipts.

## Consequences

**Positive:**
- Zero token overhead from duplicate system prompts or conflicting mission managers.
- Zero state machine drift by relying on git-tracked repository files.
- Strict security boundary with `pi-verdict` denial floor (`builtinDenyFloor: true`, secret path denials) and `pi-better-sandbox`.
- Complete reuse of canonical PStack skills without maintainer divergence.

**Tradeoffs:**
- Runtime execution requires manual user installation of pinned extensions; PStack policy strictly forbids automatic npm installations.
- Live child execution, detached worktrees, and OS sandbox enforcement remain documented as `GAP/BLOCKED/UNTESTED` until verified on live certified hardware.
