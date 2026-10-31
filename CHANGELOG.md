# Changelog

This ledger distinguishes **observed canonical upstream changes** from **applied, verified changes in the multi-harness port**. An upstream release number is not evidence of local parity. Historical releases remain recorded in git history and [UPSTREAM](UPSTREAM); new syncs append a dated entry, never rewrite historical claims.

## [Unreleased] — upstream 0.15.36 candidate (2026-10-31)

**Port release:** `0.15.29-preview.0` on `main` (no applied release promotion).
**Applied canonical source:** `cursor/plugins@88d47514b82e7c44f00f2b2a72ff6dd12158038c` (`pstack/` tree `34a0b817e5ea92375bb10f20b15cf750d4e8095a`).
**Observed target:** `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (`pstack/` tree `4719e1c4b4c43bac85d4206a8b41dd2899769c1c`); upstream `pstack/plugin.json` advertises `0.15.36`.
**Evidence:** [source audit PR #852](https://github.com/tommy-ca/pstack/pull/852), [epic #840](https://github.com/tommy-ca/pstack/issues/840), [frozen delta manifest](docs/research/upstream-pstack-0.15.36-delta.tsv).

### Staged portable changes

- **Candidate — Agentic Orchestrate #845:** migrated Orchestrate to single-PR agentic ownership, independent PR verification gates, host-owned task/agent state, and removal of stacker write monopoly. Retained local scripts/orch/ compatibility surfaces for caller migration audit.
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
