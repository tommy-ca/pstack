## Context

Reflect on the dual-writer land. Three lenses agreed that `__GROK_INSIDE_BWRAP` is the wrong SSH gate. `grok plugin tag --push` re-sandboxes git. Host `git push origin <tag>` recovered a `TagLocalUnpushed` state the script could not. Docs already said host-shell `grok --sandbox off` around the script. The script still called grok without that flag.

Architect skipped. The organizing structure stays the release state machine. Add one transition. `TagLocalUnpushed` → `git push origin refs/tags/$tag`. No new module.

## Goals / Non-Goals

**Goals:**

- Script passes `--sandbox off` to grok and git-pushes a local-only tag.
- Specs and natives match that argv.
- Dispatcher proof is a successful tag-push run. First writer wins Release notes.

**Non-Goals:**

- Version bump or retag.
- Fail-closed Actions polling.
- Amending archived OpenSpec changes.
- Catalog sibling tags.
- Editing `cli-gh` user skills (backlog).

## Decisions

1. **Encode the SSH miss in the script.** `grok --sandbox off plugin tag --push`. On failure, if the local tag exists, `git push origin refs/tags/$tag`. Still no `--force`.
2. **Keep the bwrap refuse.** That path still cannot lock refs. It is not sufficient.
3. **Do not require Actions to author the Release.** Dual-writer first-writer-wins. Prove the trigger with `gh run list --workflow=release.yml`.
4. **Catalog pin stays origin/main after archive.** Tag SHA may be the version-bump commit. Do not pin the tag.

Reflect rejected as skill-only prose: `gh run view --json actor` (inspect help already). Backlog: `cli-gh` `--verify-tag` docs, shipping `PASS+NOTES` land rule.

## Risks / Trade-offs

- [grok --sandbox off still fails and no local tag] -> `git rev-parse` fails, script exits.
- [tag already on origin] -> grok may fail "tag exists", then `git push` is up to date, then `gh release view` no-ops.
- [Actions still only exercises view] -> accepted. Trigger is proven. Create path stays in YAML for the next silent miss.

## Migration Plan

Land script, tests, docs, spec. No new tag. Idempotent `./scripts/release.sh` should exit 0 on the current version.

## Open Questions

None. No in-force ADR needs supersession.
