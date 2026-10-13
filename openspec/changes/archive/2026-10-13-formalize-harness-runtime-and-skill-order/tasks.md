# Tasks: Formalize Harness Runtime Conventions and Skill Order

- [x] 1. Define `schemas/portability/skill-order.schema.json`
- [x] 2. Define `schemas/portability/runtime-conventions.schema.json`
- [x] 3. Extend `schemas/portability/profile.schema.json` with `skill_order` and `runtime_conventions`
- [x] 4. Update `openspec/specs/pstack-portability/spec.md` with structured runtime and skill order requirements
- [x] 5. Extract `HARNESS.md` structured content to `profiles/grok.json` and create `grok-tools.md`
- [x] 6. Populate `skill_order` and `runtime_conventions` across `antigravity.json`, `codex.json`, `omp.json`, `opencode.json`
- [x] 7. Update `scripts/portability_schema.py` and `scripts/verify-portable.py` with domain models and doctor checks
- [x] 8. Add schema tests in `tests/test_portability_schemas.py` and verify all tests pass
