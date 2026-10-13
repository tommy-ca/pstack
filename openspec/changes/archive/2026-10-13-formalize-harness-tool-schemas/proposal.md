# Change Proposal: Formalize Harness Tool Schemas & Isolate Upstream Pstack

## Why

Upstream pstack skills (`skills/`) are authored against Cursor native primitives. Adapting pstack to other agent harnesses (Grok Build, Codex, OMP, OpenCode, Antigravity) by mutating upstream skills in-place creates severe divergence and merge debt on every upstream release. Tool mappings currently live in unvalidated Markdown reference tables. Formalizing these tool mappings into structured JSON schemas allows host adapters to cleanly overlay and fallback to host-native primitives while keeping upstream pstack skills intact.

## What Changes

1. **Structured Tool Mapping Schema**: Define `schemas/portability/tool-mapping.schema.json` capturing primitives for file I/O, shell execution, web operations, subagent lifecycle, background tasks, MCP tools, plan tracking, and human interaction.
2. **Profile Schema Extension**: Extend `schemas/portability/profile.schema.json` with a validated `tool_mappings` property.
3. **Structured Host Profiles**: Populate typed `tool_mappings` in `profiles/antigravity.json`, `profiles/codex.json`, `profiles/omp.json`, `profiles/opencode.json`, and `profiles/grok.json`.
4. **Domain Model Validation**: Upgrade `scripts/portability_schema.py` and `scripts/verify-portable.py` to validate tool mapping contracts in CI and doctor checks.
5. **Upstream Pstack Isolation**: Document the host discovery and progressive fallback protocol so canonical `skills/` remains pristine with zero unneeded modifications.

## Impact

- Canonical skills in `skills/` track upstream Cursor releases cleanly with minimal to no diff.
- Harness profiles provide machine-readable, testable tool declarations for runtime projection and prompt generation.
- Doctor and lever verification (`scripts/verify-portable.py`) prove schema and runtime conformance.
