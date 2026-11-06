# Verification, falsification and review matrix — SOURCE-REVIEWED; EXECUTION NOT_RUN

The PR is OpenSpec-only. Independent `swarm`, `arena`, `interrogate`, both Thermos skills, actual native Grok execution and standalone OpenSpec CLI are **NOT_RUN** until separately demonstrated. Historical green offline CI is not proof for a revised PR SHA.

## Requirement -> negative control -> owner
| ID | Contract | Negative control | Proposed executable owner |
| --- | --- | --- | --- |
| V-01 | exact host identity | `copilot` incorrectly accepted for `github:copilot` | `tests/test_setup_projection.py`, `scripts/host_identity.py` |
| V-02 | convention reference confinement | `references/grok.md` symlink escape, missing file, nonfile | new setup reference helper test |
| V-03 | no second dispatch | `SetupProjection.skill` and `reference` legacy keys accepted after migration | JSON Schema/Python negative fixtures |
| V-04 | all six legacy keys migrated | `skill:null` remains in antigravity/codex/droid/omp/opencode | per-profile closed-schema validation |
| V-05 | cross-host write confinement | Codex/candidate selects Grok reference or writes `~/.grok` | sandboxed host-path mutation test |
| V-06 | candidate protection | candidate with `host-cli` tries native probe | `test_setup_projection.py` |
| V-07 | valid model/effort | slug absent live catalog, `max` not in observed Grok effort enum | native probe contract test |
| V-08 | Grok effort fallback | model inherit/auto and effort inherit/auto accidentally equated | Grok frontmatter/role overlay test |
| V-09 | panel topology | repeated identical family marked independent panel | model-role resolver tests |
| V-10 | idempotence | repeat setup mutates unrelated user file | tmp-home managed-path before/after hash test |
| V-11 | root mirror authority | generated/root profile stale but root-first preferred | `test_harness_profiles_sync.py`; package parity |
| V-12 | root missing installed package | packaged-only installation reported GAP for valid host | install layout golden fixture |
| V-13 | package migration | manifest/verifier depends on retired `setup-pstack-grok` | `verify_harness`, package/projection tests, scanner |
| V-14 | ordinary verification offer | setup creates duplicate `verify-pstack` or overwrites project verifier | skill-invocation/no-write contract |
| V-15 | formal verification offer | upstream formal offer silently dropped or auto-creates proof with no target | optional offer/proof skill contract |
| V-16 | old living requirement contradiction | old `declared setup skill` requirement not MODIFIED | OpenSpec delta validation/semantic diff |
| V-17 | commit provenance | previous green CI asserted at new SHA | exact-head run and evidence trace |
| V-18 | no orchestrator scope creep | spec adds scheduler/task DB/model provider registry | changed-diff review + scope gate |

## Tiered proof requirements
- **L0 source inspection**: accurate source pin, baseline UPSTREAM, caller inventory. Not native evidence.
- **L1 static constraints**: valid JSON Schema Draft 2020-12 shape, typed projection tests, role-key shape, mirror hashing, branch diff, OpenSpec semantic validation. A `pytest` PASS does not prove live model acceptance.
- **L2 packaged/offline**: generated package and all six *built-in* harnesses run offline `verify_portable.py doctor --host all` and targeted tests; keep candidate hosts separate.
- **L3 observed native**: actually start the relevant installed host, exercise selected setup, inspect exact managed artifacts and a real child model/effort receipt; only available, authorized hosts can pass.
- **L4 independent review**: Swarm, Arena, Interrogate, Thermos results have actual model/agent IDs, distinct contexts, frozen prompts/rubrics and exact changed SHA. Unavailable independent reviewers -> NOT_RUN, not fabricated concurrence.

## Exact commands to run at the implementation head (not run here)
~~~bash
openspec validate 2026-11-06-single-entry-setup-pstack --type change --strict
python3 -m pytest -q tests/test_setup_projection.py tests/test_harness_profiles_sync.py tests/test_scan_host_boundary.py tests/test_verify_harness.py
python3 scripts/verify_portable.py doctor --host all
# add fresh package lifecycle and native Grok smoke tests only with authorized local host binaries
~~~
The existing CI command may use different wrappers; verify the checked-out CLI availability and invocation syntax rather than infer they ran from this text. Record exact job URL, SHA, native host version and artifact paths. Re-run after any changes affecting SKILL.md hashes or staged package projections.

## Review lanes (method references, not performed independent agents)
- **Swarm:** source-trace ownership, six-profile schema migration, package/root mirror/integrity coverage. Require distinct real agents and consolidated evidence.
- **Arena:** freeze identical brief for candidate designs (derivable reference vs explicit path), grade by source authority, fewer fields/branches, package compatibility, negative controls and maintenance cost; accept only actual independently compared candidates.
- **Interrogate:** reproducibly falsify claims with negative controls, separate true changed-diff findings from historical unrelated code.
- **Thermo Nuclear Review:** cross-host write leaks, regressions, user-owned config changes, unsafe path handling.
- **Thermo Nuclear Code Quality:** eliminate the extra skill, redundant `reference` field, duplication and unjustified compatibility shims. No thin wrapper or second provider registry.

**No runtime changes** are required to review this documentation PR, but its exact-head OpenSpec validation and independent review remain separate gates. A passed offline CI on this docs branch may be recorded without closing #953.
