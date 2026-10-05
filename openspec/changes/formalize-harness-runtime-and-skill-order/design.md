# Design: Formalize Harness Runtime Conventions and Skill Order

## Architecture

Follows Clean/Hexagonal Architecture (Ports and Adapters):
- **Core Domain (Ports)**: Upstream pstack skills, principles, and playbooks. Authored once, tested behaviorally, kept minimal and intact.
- **Adapters**: Host profiles (`profiles/*.json`), projected manifests, tool mappings, runtime conventions, and skill orders.
- **Levers**: Deterministic Python scripts (`portability_schema.py`, `verify-portable.py`, `project-package.py`) that validate and project the domain into host-native structures without manual hand-edits.

## Decisions

1. **Structured Skill Order Matrix**:
   Skill resolution is modeled as an ordered 3-tier fallback list per need:
   - Primary: pstack skill or playbook (e.g. `/tdd`, `/interrogate`).
   - Secondary: user-level skill overlay when primary is not installed.
   - Fallback: host bundled or builtin command.
2. **Structured Runtime Conventions**:
   Host execution constraints are codified in `runtime_conventions`:
   - `max_subagent_depth`: 1 for parent-owned dispatch.
   - `supported_isolation_modes`: host-supported isolation options.
   - `allowed_spawn_fields` and `forbidden_spawn_fields`: strictly validated fields to prevent dispatch rejection.
   - `wire_aliases`: deterministic mapping from wire identifiers to TUI primitives.
3. **Extraction of HARNESS.md**:
   The structured data within `HARNESS.md` is preserved in `profiles/grok.json`. A companion reference `skills/poteto-mode/references/grok-tools.md` is added to match the layout of sibling harnesses (`antigravity-tools.md`, `codex-tools.md`, `omp-tools.md`, `opencode-tools.md`). `HARNESS.md` at root points to these structured assets.

## Verification

- `schemas/portability/skill-order.schema.json` and `runtime-conventions.schema.json` validate across all five profiles.
- `scripts/verify-portable.py doctor --host all` confirms profile, skill order, and runtime convention validity.
- Full pytest test suite and 3-plane verifier runs pass.
