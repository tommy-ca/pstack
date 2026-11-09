# Proposal: consolidate setup-pstack without a second setup router

## Outcome
Preserve upstream Cursor PStack setup intent with **one public `/setup-pstack` skill** and native setup instructions under `skills/setup-pstack/references/`. Keep the nine typed harness profiles under `skills/setup-pstack/profiles/`; keep `poteto-mode/references/` focused on host tool/skill usage, not configuration. Delete `setup-pstack-grok` after coordinated caller migration. Agent orchestration frameworks and model-router development remain outside PStack scope.

## Baseline and audit
- Main at audit: `b356beff9c6d75b7a9cf28940c1209462e2a1b09`; existing draft PR #958 was based on `100230add` and must incorporate newer package/verification changes before implementation.
- Applied official Cursor `UPSTREAM` is [cursor/plugins@88d47514](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/setup-pstack/SKILL.md); [candidate current cursor/plugins@2776ddd](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/setup-pstack/SKILL.md) changes Arena's cross-judge wording in one sentence. Track separately from applied pin.
- The current [neutral setup entry](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack) is 6 KB; [Grok setup skill](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack-grok) is 15 KB plus four native references. Both are already implemented and currently operational paths. This PR specifies their merge, not a new setup engine.
- Existing closed [#703](https://github.com/tommy-ca/pstack/issues/703) established host-neutral setup; [#937](https://github.com/tommy-ca/pstack/issues/937) packaged the nine profiles. Reconcile, do not repeat, those projects.

## Revised design choice (KISS / YAGNI)
**Do not add `SetupProjection.reference`.** A host profile already has an exact validated filename. For `host-cli`, derive the single setup reference deterministically: `skills/setup-pstack/references/<matched-profile-filename-stem>.md` (currently `grok.md`). Validate that the file is regular, within the references directory, and not a symlink escape. Host identity is the profile's validated `host` field, NOT a name guessed from the active repository, a user-provided pathname, or a filename alias.

During the coordinated implementation wave, migrate every internal `setup.skill` consumer and remove **that field**, instead of introducing a second `reference` pointer, a second dispatcher or permanent dual-mode compatibility. External migration concerns warrant release notes and rollback proof, not an indefinitely retained second public skill. Keep `SetupProjection` with only existing `source`, `effort`, `catalog`, and `overlay`; update its current JSON Schema + typed model in place and make source-dependent shapes explicit.

## Requirements in scope
1. Preserve applied upstream steps: discover available models, read current choices, budget/per-role/panel decisions where supported, validate, host-native write/project or explicitly no-write, confirm; **offer both `create-verification-skill` and `create-formal-verification-skill` optionally**, without generating duplicates.
2. Grok-specific probes, UI option vocabularies, slugs, effort ladder/defaults, role TOML paths and native write instructions live under `setup-pstack/references/grok.md` and `references/grok/`. Shared `SKILL.md` contains no hardcoded host CLI/path/model.
3. `pstack.package.json#roles` remains the one role registry (22 roles); `scripts/model_role_resolver.py` remains the one precedence policy. Never assume Cursor's budget tokens/models are available on Grok.
4. `skills/setup-pstack/profiles/*.json` is the **single editable host-profile source**; `profiles/` remains a byte-identical generated compatibility mirror until all repo and installed package consumers can be migrated safely.
5. `host-cli`, `host-catalog`, `inherit`, `none`, absent setup, and candidate hosts produce only the declared behavior and honest evidence status. Native writes are restricted and idempotent; outside-scope user files are preserved.
6. No new host scheduler, dispatcher API, runtime model registry, second model policy, global agent lifecycle interface, QStack dependency, or LLMWiki compiler.

## Existing-spec reconciliation
Use **MODIFIED** requirements for the two existing `pstack-setup-overlays` requirements, retaining and sharpening their original Grok file-shape and host-safety assertions. Add only independent new requirements for profile authority, types, reference safety, upstream optional verification, migration and evidence. Do not leave a contradictory living requirement that still mandates dispatch to a separate setup skill.

## Prior-art/discipline crosswalk
- Official [Subtract Before You Add](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-subtract-before-you-add/SKILL.md) + [Migrate Callers Then Delete Legacy APIs](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md): remove the Grok public skill and legacy `skill` pointer in one proven implementation wave; no speculative `reference` field.
- [Boundary Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-boundary-discipline/SKILL.md) + [Type System Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-type-system-discipline/SKILL.md): validate raw JSON/host identity once, use the existing typed projection, and derive reference paths rather than add loose aliases.
- [Make Operations Idempotent](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-make-operations-idempotent/SKILL.md) + [Prove It Works](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-prove-it-works/SKILL.md): repeat safe writes, verify from fresh real-host results and publish exact SHA receipts rather than treating static setup as native proof.
- QStack [Declare Your Falsifier](https://github.com/tommy-ca/qstack/tree/main/skills/qstack-principle-declare-your-falsifier) informs negative-test discipline only; QStack is downstream `qstack-mode -> poteto-mode`, not a source of generic PStack setup authority.
- Upstream `swarm`, `arena`, `interrogate` and both Thermos skills are review *methods*, not new orchestration work in PStack. Independent execution remains NOT_RUN without real agent receipts.

## Delivery
Existing epic [#948](https://github.com/tommy-ca/pstack/issues/948) -> source audit #949 -> living capability delta #950 -> parallel code migration #951 and profile authority #952 -> exact-head review/CI gate #953. This PR is **docs/specs only**; no claim that the implementation, native host tests, formal verification or independent reviewers have been executed.
