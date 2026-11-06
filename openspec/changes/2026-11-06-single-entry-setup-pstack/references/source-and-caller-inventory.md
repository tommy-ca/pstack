# Source and caller inventory (main@100230add; source review, NOT execution proof)

## Canonical and existing contracts
- [Official Cursor `setup-pstack`](https://github.com/cursor/plugins/tree/main/pstack/skills/setup-pstack): model discovery, budget, role/panel mapping, validation, native rule write, confirmation and optional verification. Canonical upstream intent; specific Cursor model slugs/file paths are not portable.
- [Port neutral setup](https://github.com/tommy-ca/pstack/blob/main/skills/setup-pstack/SKILL.md): existing `SetupProjection` entry; no Grok path in shared body.
- [Port Grok setup](https://github.com/tommy-ca/pstack/blob/main/skills/setup-pstack-grok/SKILL.md): CLI model/effort detection, Grok native TOML and per-role writes, model/effort menu, default and extension references. Candidate for migration, not for wholesale inlining.
- [Port `pstack-setup-overlays`](https://github.com/tommy-ca/pstack/blob/main/openspec/specs/pstack-setup-overlays/spec.md): existing living capability. New requirements are a delta, not a second capability.
- [Role registry](https://github.com/tommy-ca/pstack/blob/main/pstack.package.json) and [resolver](https://github.com/tommy-ca/pstack/blob/main/scripts/model_role_resolver.py): existing shared ownership. [SetupProjection type](https://github.com/tommy-ca/pstack/blob/main/scripts/portability_types.py); [schema](https://github.com/tommy-ca/pstack/blob/main/schemas/portability/setup-projection.schema.json).

## Existing profile matrix
| File | Declared host | Setup source | Treatment |
| --- | --- | --- | --- |
| antigravity.json | antigravity | host-catalog | preserve native projection, no runtime write |
| claude.json | claude, candidate | absent | GAP; no new probe |
| codex.json | codex | host-catalog | preserve native projection |
| copilot.json | github:copilot, candidate | absent | GAP; no new probe |
| droid.json | droid, candidate | inherit | no-write |
| grok.json | grok | host-cli, skill=setup-pstack-grok | migrate to reference, retain native write |
| omp.json | omp | none | BLOCKED or explicit no setup |
| opencode.json | opencode | none | BLOCKED or explicit no setup |
| pstack-pi.json | pstack:pi, candidate | inherit | no-write |

## Migration callers to verify (not exhaustive until #949 completed)
- `skills/setup-pstack/SKILL.md`, `skills/setup-pstack-grok/SKILL.md`, four Grok reference files, packaged and root `grok.json`.
- `scripts/setup_pstack.py`, `scripts/portability_types.py`, `schemas/portability/setup-projection.schema.json`.
- `scripts/verify_harness.py`, `scripts/scan_host_boundary.py`, `scripts/package_lifecycle.py`, `scripts/prove_antigravity_native_package.py`, `scripts/package_projection.py`; `scripts/drivers/base.py` and profile/fixture hash consumers.
- `tests/test_setup_projection.py`, `tests/test_verify_harness.py`, `tests/test_scan_host_boundary.py`, `tests/test_harness_profiles_sync.py`.
- `skills/poteto-mode/SKILL.md`, `skills/poteto-mode/references/<host>-tools.md`, setup references inside `swarm`, `arena`, `interrogate`, `architect`, `how`, `why`.
- `README.md`, `README.zh-CN.md`, `TEST-PLAN.md`, manifests/agent projections, operational (not historical) docs, generated distribution and DSH/evidence receipts.

## Known contradictions / risks to falsify
1. `tests/test_harness_profiles_sync.py` calls packaged path `CANONICAL_PROFILES`, while `scripts/setup_pstack.py#resolve_profiles_dir` chooses `profiles/` when present. Resolve authority by design plus deterministic mirror generation.
2. `SetupProjection` requires `skill` for `host-cli`; deleting Grok skill without changing schema, parser and tests breaks dispatch.
3. Shared entry promises setup skill dispatch; moving Grok logic to references needs a path confinement test before allowing non-code instructions to select native writes.
4. Prior PR #719 split Grok setup specifically to stop cross-host writes. The merge must not reintroduce those leaks.
5. Current packaging and Antigravity proof expect two profile locations; root deletion is a separate, gated option, not a one-shot cleanup.
6. Current upstream Cursor budget naming/model variants must not be blindly pasted into Grok's live usable effort enum.

## Disposition
`poteto-mode/references` remains host tool consumption. Keep setup control data in packaged setup profiles and setup authoring steps in setup references. External QStack methods may consume PStack setup output, never override its contract. Mu/Dogsled runtime orchestration is unrelated.
