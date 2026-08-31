## Context

`v0.14.5-grokbuild.3` is a lightweight tag at `536fcd6`. GitHub Release exists. Workflow `release.yml` has zero runs. The first workflow and the first tag landed in the same second. `gh release create --verify-tag` on the laptop hid the miss. Nested grok cannot lock `.git/refs/tags`. Repo default `GITHUB_TOKEN` is read. YAML already asks for `contents: write`. Catalog pin is a later SHA, not this script.

Two architect sketches were compared. Dual-writer idempotent is the base. Actions-only fail-closed was rejected.

## Goals / Non-Goals

**Goals:**

- One command `./scripts/release.sh` converges to origin tag plus GitHub Release.
- Actions on `v*` still publishes when the dispatcher fires.
- File tests catch a missing `gh release view` fallback.
- Next tag happens after `release.yml` is already on `origin/main`.
- Host shell is required for tagging.

**Non-Goals:**

- Retag or `--force` `v0.14.5-grokbuild.3`.
- `workflow_dispatch`.
- grok on the Actions runner.
- Catalog sibling tags.
- Polling `gh run watch` inside the script.
- PATH-stub fake GitHub in unit tests.
- Leftover OpenSpec changes already on main.
- Cursor playbooks.

## Decisions

1. **Domain is a three-state machine, not two booleans.** `TagMissing` → `ReleaseMissing` → `Released`. Construct the tag name as `v` + `plugin.json` version. A GitHub Release without a tag is not a local state we create (`--verify-tag`).

2. **Dual writer on the Release, single writer on the tag.** Local `grok plugin tag --push` is the only tagger. Local script and Actions both `gh release view` then `gh release create --verify-tag --generate-notes`. First writer wins notes. HTTP 422 then view is success.

3. **Fail closed on missing `gh` after a successful tag, not on a silent Actions run.** If `gh` is missing, the script dies. If Actions never starts, the local writer still creates the Release. The parent session proves Actions with `gh run list` after the next tag. That is the live surface. It is not encoded as a poller.

4. **Refuse nested grok.** If `__GROK_INSIDE_BWRAP` is set, exit before `grok plugin tag` and name `grok --sandbox off`.

5. **Bump after the script is on main.** Version `0.14.5-grokbuild.4` is a later commit on `origin/main`, then `scripts/release.sh`. Do not tag the same commit that first adds the workflow again.

6. **Tests stay file-text plus one live proof.** Grep both writers for `gh release view`, `gh release create`, `--verify-tag`, no `--force`, no `workflow_dispatch`, no grok in YAML. Do not add hermetic `PATH` stubs. The TDD cheap path is the grep. The expensive path is the real tag.

**Alternatives considered.** Actions-only fail-closed would refuse a human-created Release and poll `gh run watch`. That proves the dispatcher and blocks the operator when GitHub is silent. Dual-writer fills the operator gap and still lets the parent watch the next run. Split scripts (`tag.sh` then `publish.sh`) leak the machine. Installing grok in Actions is forbidden.

## Risks / Trade-offs

- [Actions stays at zero on the next tag] -> Local writer still publishes. Parent reports the miss. Do not `--force`.
- [Race between laptop and Actions] -> `gh release view || gh release create`. Create 422 then view is success.
- [Default token is read] -> YAML `contents: write` is the request. A 403 on a real run is a new defect, not this miss.
- [Tag equals HEAD at invoke time] -> Run the script from `origin/main` after the version bump lands.

## Migration Plan

Land the script and workflow on `main`. Bump `plugin.json` to `0.14.5-grokbuild.4`. From a host shell run `./scripts/release.sh`. Confirm `gh run list --workflow=release.yml` is non-empty. Pin `grok-build-plugins` marketplace sha to that HEAD. Update the installed plugin with `grok --sandbox off plugin update pstack`.

## Open Questions

None. No in-force ADR needs supersession for this change. ADR-0008 stays about host adapter scope, not tagging.
