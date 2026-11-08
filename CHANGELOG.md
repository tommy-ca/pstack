# Changelog

This ledger distinguishes **observed canonical upstream changes** from **applied, verified changes in the multi-harness port**. An upstream release number is not evidence of local parity. Historical releases remain recorded in git history and [UPSTREAM](UPSTREAM); new syncs append a dated entry, never rewrite historical claims.

## [0.15.36-preview.0] — 2026-11-07

**Port release:** `0.15.36-preview.0` on `main`.
**Applied canonical source:** `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (`pstack/` tree `4719e1c4b4c43bac85d4206a8b41dd2899769c1c`).
**Applied changes:**
- Ported agentic orchestrate and cleaned up legacy orchestrate scripts (#981).
- Ingested statechart and ketchup-video skills with lean compiler and zero static fixture bloat (#982).
- Upgraded formal verification skills and scaffolding with `/statechart` visualization integration (#983).
- Promoted UPSTREAM pin to 0.15.36 and projected canonical manifests to all six host adapters (#984).
- Projected opt-in Pi native package exposing canonical skills and agents without executable extensions (#1010).
- Extended verification skills and scaffolders with candidate host support and truthful proof tiers (#1011).
- Hardened candidate verifier with 59 bounded negative mutants and multi-harness conformance (#1012, #1013).
- Decomposed package lifecycle staging into scripts/package_install_staging.py keeping modules under 550 lines (#1021).
- Hardened verification skills scaffolder with structured JSON reporting on audit, list, and check commands (#1022).
- Ported canonical thermos and thermo-nuclear-review skills from cursor/plugins (#1032).
- Projected thermos and thermo-nuclear-review commands across all six host manifests (#1033).
- Added root bunfig.toml test timeout and converted check-plan shebang to bun (#1043).
- Hardened verification skills scaffolder and drivers with reproducible uv run and bun runtime resolution (#1044).
- Added setup-bun and reproducible uv run steps to GitHub Actions offline workflow (#1045).
- Extracted Droid role projection from scripts/package_projection.py into dedicated module scripts/droid_role_projection.py (#1055).
- Added formal verification driver to .codex/skills/verify-llm-wiki-formal and hardened scaffolder executable driver checks (#1056).
- Scaffolded and tailored verify-antigravity-pstack verification skill in .agents/skills/ (#1057).
- Updated CI offline workflow with formal driver, Antigravity driver, and harness audit checks (#1058).
- Added comprehensive mise tasks and driver contracts enforcing native uv and bun commands (#1073, #1075).
- Scaffolded and tailored verify-omp-pstack verification skill in .omp/skills/ (#1074, #1076).
- Curated portable DeepSeek skills and reconciled 22-source OpenSpec without DSH-specific workflows (#1049, #1061, #1062).
- Hardened make-pr-easy-to-review verification claims against unrun and stale evidence (#1065, #1063, #1064).
- Scaffolded and tailored verify-opencode-pstack verification skill in .opencode/skills/ (#1079, #1083).
- Scaffolded and tailored verify-droid-pstack verification skill in .factory/skills/ (#1080, #1084).
- Wired OMP, OpenCode, and Droid verification drivers into portability-offline CI workflow and updated tests (#1081, #1085).
- Completed multi-harness verification gate across all six declared hosts and closed Epic #1078 (#1082).
- Extracted Antigravity command projection into dedicated module scripts/antigravity_command_projection.py (#1088, #1092).
- Added reproducible driver.sh to verify-pstack and required driver in scaffolder (#1089, #1093).
- Wired Grok verification driver into portability-offline CI workflow and updated tests (#1090, #1094).
- Qualified 6-harness verification gate across all 10 verification skills and closed Epic #1087 (#1091).
- Extracted verification skill templates into dedicated module scripts/verification_skill_templates.py (#1097, #1101).
- Fixed OpenSpec strict validation warnings, unified Pi candidate verification driver, and added ephemeral prune (#1098, #1102).
- Wired Pi verification drivers and projection tests into portability-offline CI workflow (#1099, #1103).
- Qualified 6-harness verification gate across all 10 verification skills and closed Epic #1096 (#1100).
- Restored fail-closed cleanup exit code 2 contract in Pi verification drivers (#1106, #1111).
- Cleansed style violations in thermo-nuclear-code-quality-review and added frontmatter tests (#1107, #1112).
- Pruned obsolete workspace clutter and non-evidence ephemeral scratch files (#1108, #1113).
- Wired 11 hermetic safety tests into portability-offline CI workflow and updated select-checks (#1109, #1114).
- Qualified 6-harness verification gate across all 10 verification skills and closed Epic #1105 (#1110).
- Flattened schemas directory hierarchy by moving schemas/portability directly to schemas (#1117, #1121).
- Pruned obsolete workspace cache clutter in .atl/ and reinforced style rules (#1118, #1122).
- Audited all 10 verification skill drivers and updated templates for flattened schemas (#1119, #1123).
- Qualified 6-harness verification gate across all 10 verification skills and closed Epic #1116 (#1120).

## [Unreleased] — upstream 0.15.36 candidate (2026-10-31)

**Port release:** `0.15.29-preview.0` on `main` (no applied release promotion).
**Applied canonical source:** `cursor/plugins@88d47514b82e7c44f00f2b2a72ff6dd12158038c` (`pstack/` tree `34a0b817e5ea92375bb10f20b15cf750d4e8095a`).
**Observed target:** `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (`pstack/` tree `4719e1c4b4c43bac85d4206a8b41dd2899769c1c`); upstream `pstack/plugin.json` advertises `0.15.36`.
**Evidence:** [source audit PR #852](https://github.com/tommy-ca/pstack/pull/852), [epic #840](https://github.com/tommy-ca/pstack/issues/840), [frozen delta manifest](docs/research/upstream-pstack-0.15.36-delta.tsv).

### Staged portable changes

- **Candidate — Agentic Orchestrate #845:** migrated Orchestrate to single-PR agentic ownership, independent PR verification gates, host-owned task/agent state, and removal of stacker write monopoly. Retained local scripts/orch/ compatibility surfaces for caller migration audit.
- **Candidate — PStack router #846:** restate the user's goal in kickoff/PR/final, and favor fresh subagents for new work rather than trusting resumed context.
- **Candidate — Explain-the-Number #846:** source-identical upstream principle now pre-registers the measurement decision and noise floor before a run.
- **Candidate — Arena #846:** cross-judge must be a confirmed different family from the *coordinator*, not merely a candidate; skip judge when no independent family is runnable and disclose the omission.
- **Candidate — Interrogate #846/#854:** reproducible findings only, with bounded command, observed and expected results, and lead rerun at a frozen revision. Unexecuted hypotheses are not confirmed findings.
- **Candidate — Verification #854:** preserved six-harness scaffold and resource-isolation contract; source-revision identities, negative controls, bounded formal checks, and conditional Statechart integration when available.
- **Candidate — Sync documentation #849:** update snake_case script names and migration recipe while keeping the applied pin frozen.

### Upstream changes not yet applied

- **Optional/blocked #847:** `statechart` TypeScript/TLC/Java compiler and its substantial fixture corpus; native execution and security proof not yet performed. No unconditional `/statechart` call in a port where the skill is absent.
- **Excluded pending host case:** Cursor-only package assets and `make-bot-ui`; no blind copy into the generic portability layer.
- **Pending #850/#851:** six-host native conformance, exact-head CI, candidate-to-applied pin promotion and release.

### Verification and release policy

Each change must link to a specific source commit, changed files, executable checks (including negative controls), exact local head SHA and honest evidence tier: `SOURCE_REVIEWED`, `STATIC`, `OFFLINE`, `OBSERVED_LIVE`, `BLOCKED` or `UNTESTED`. Do not treat a passing fixture, model-only check, or GitHub metadata as `OBSERVED_LIVE`. An absent tool blocks only its dependent gate. Failed tests are not downgraded to blocked.

**Release status: NOT SHIPPED.** Do not update `UPSTREAM`, `pstack.package.json#upstream_pin`, `plugin.json`, generated host versions or evidence receipts until the gates in [#850](https://github.com/tommy-ca/pstack/issues/850) and [#851](https://github.com/tommy-ca/pstack/issues/851) pass. Reverify and append a Released entry only after merge.
