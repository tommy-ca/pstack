# Design: Formalize Harness Tool Schemas & Isolate Upstream Pstack

## Architecture

Follows Hexagonal Architecture (Ports and Adapters):
- **Core Domain (Ports)**: Upstream pstack skills, principles, and playbooks. Authored once, tested behaviorally, kept minimal and intact.
- **Adapters**: Host profiles (`profiles/*.json`), projected manifests, and host tool mappings.
- **Levers**: Deterministic Python scripts (`portability_schema.py`, `verify-portable.py`, `project-package.py`) that validate and project the domain into host-native structures without manual hand-edits.

## Decisions

1. **Structured Tool Mappings in Harness Profile**:
   Rather than inventing another config file, anchor tool mappings directly in `profiles/<host>.json` under a validated `tool_mappings` object conforming to `schemas/portability/tool-mapping.schema.json`.
2. **Deterministic Fallback Hierarchy**:
   - First Choice: Native host tool matching the capability if available.
   - Second Choice: Host subagent or script shim.
   - Fallback: Graceful degradation (e.g. Sequential execution when fan-out depth is 1, CLI worktree when hard sandbox is absent, plain chat when interactive question modal is missing).
3. **Purity of Upstream Skills**:
   Upstream skills in `skills/` MUST NOT contain scattered conditionals checking for individual host environments. The host adapter profile injects or configures the execution environment.

## Verification

- `schemas/portability/tool-mapping.schema.json` validates all 5 profiles.
- `scripts/verify-portable.py doctor --host all` confirms profile and tool-mapping validity.
- `scripts/verify-portable.py run --host all` confirms 3-plane conformance across all 5 harnesses.
