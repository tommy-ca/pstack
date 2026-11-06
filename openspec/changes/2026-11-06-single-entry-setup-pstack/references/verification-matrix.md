# Verification and review contract

Status: SPECIFIED / NOT_RUN. A plan is not proof of executed independent agents or native setup.

| ID | Target | Negative control | Evidence required |
| --- | --- | --- | --- |
| V-01 | Host identity | `github:copilot` mistaken for filename `copilot` | parser rejection + existing tests |
| V-02 | Reference safety | absolute, `..`, symlink escape or missing `references/grok.md` | unit test refuse and zero native writes |
| V-03 | Single dispatch | both legacy `skill` and new `reference` set | schema/type reject; no ambiguous path |
| V-04 | Cross-host write | Codex/candidate attempts Grok TOML write | path-sandbox negative test |
| V-05 | Availability | missing slug/invalid effort after host detection | explicit BLOCKED/no persisted value |
| V-06 | Default aliases | `auto` or `inherit-parent` configured | model omitted, no fake identity; effort described precisely |
| V-06b | Grok effort alias | overlay removed but plugin agent frontmatter effort remains | report frontmatter fallback, not false parent effort inheritance |
| V-07 | Panel semantics | arena candidates/seat or judge missing | coverage/independence GAP, no synthetic success |
| V-08 | Idempotent user config | second setup call same choices and unrelated files present | no new write outside managed names |
| V-09 | Profile authority | packaged and root copies disagree | deterministic FAIL and no stale root preference |
| V-10 | Package integrity | remove old skill before readers migrate | failed existing caller/reference/manifest test |
| V-11 | Honest tiers | offline profile success without live host | offline PASS permitted; native stays NOT_RUN/BLOCKED |

## Review composition
- **Swarm**: distinct source/caller inventory, host-boundary test review, packaging/profile authority lanes. Require actual runner IDs, path coverage, dropouts; NOT_RUN otherwise.
- **Arena**: same frozen brief and 3–6 rubric criteria compare smallest implementation options; distinct outputs; true cross-family judge only when observed, else skipped.
- **Interrogate**: reproduce failures on the actual diff; speculative issues excluded; report command, output and target expected behavior.
- **Thermo Nuclear Review**: changed-diff security/correctness, wrong-host writes, unsafe overwrite, missing migration, model leaks and developer experience.
- **Thermo Nuclear Code Quality**: simplify by deleting the second public setup skill; no new generic host SDK, duplicate registry, growing 1k-line modules, or host-specific branches in shared code.

## Suggested executable gates (to be confirmed by #953)
- `openspec validate --changes --strict` when available; otherwise NOT_RUN.
- Targeted `pytest`: test_setup_projection.py, test_harness_profiles_sync.py, test_scan_host_boundary.py, test_verify_harness.py, test_model_role* and packaging tests.
- `python3 scripts/verify_portable.py doctor --host all`, plus versioned package projection, DSH provenance and offline contract matrix.
- Observed native Grok setup on a clean test home, reload and corroborate model/effort only if the actual host is available and authorized. Other hosts must have evidence specific to their declared capability surface.

**Completion rule:** each claimed pass binds the exact PR head SHA and source/fixture versions. A previous green run or unobserved reviewer is not evidence at the new head.
