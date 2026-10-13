# Tasks: Formalize Harness Tool Schemas & Isolate Upstream Pstack

- [x] 1. Define `schemas/portability/tool-mapping.schema.json`
- [x] 2. Extend `schemas/portability/profile.schema.json` with `tool_mappings`
- [x] 3. Populate `tool_mappings` across all 5 profiles in `profiles/*.json`
- [x] 4. Update `scripts/portability_schema.py` with `ToolMapping` dataclass and validation
- [x] 5. Update `scripts/verify-portable.py` doctor check for tool mappings
- [x] 6. Update `openspec/specs/pstack-portability/spec.md` with structured tool mapping requirement
- [x] 7. Run `python3 scripts/verify-portable.py run --host all` and pytest suite
