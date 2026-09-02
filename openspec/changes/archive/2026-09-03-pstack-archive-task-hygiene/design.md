## Context

`openspec validate --archived --strict` currently fails only two archives. Both failures are one unchecked task 3.3 in a release change. The tasks require a marketplace pin, `tests/test_marketplace.py`, and host-side `grok --sandbox off plugin update` commands. The pstack checkout does not contain that marketplace test, while the sibling `/home/tommyk/projects/grok-build-plugins` checkout does. Its marketplace entry is a separate repository surface and currently records the older pstack version and a pstack commit SHA. The installed-plugin commands are external host mutations.

The current pstack archive-chain specification also says historical task intent must remain reviewable. The hygiene change therefore needs to close the archive validator's checkbox count without rewriting the task into false execution evidence.

## Goals / Non-Goals

**Goals:**

- Make the two archived task records explicit about their external work being deferred.
- Preserve the original marketplace/update intent, the reason it was not run, and the follow-up surface.
- Make `openspec validate --archived --strict` pass without editing the sibling repository or installed Grok state.
- Update the durable archive-chain rule so this outcome format is intentional and repeatable.

**Non-Goals:**

- Do not edit, commit, push, or tag `/home/tommyk/projects/grok-build-plugins`.
- Do not run `grok plugin update`, marketplace updates, or any other installed-plugin mutation.
- Do not invent `tests/test_marketplace.py` in pstack; the relevant test belongs to the marketplace repository.
- Do not delete the archived tasks or claim the external pin was changed.
- Do not add a new dependency, script, repository, or durable architecture ADR.

## Decisions

### Use a checked outcome annotation, not a false completion claim

Rewrite only the two unchecked task lines to retain their original action in an `Original action` clause, then append `Outcome: deferred`, the exact scope reason, and a follow-up path. The checkbox closes the archival record review. It does not claim that the marketplace pin or host update ran. The archive-chain spec makes this distinction explicit.

### Keep the external boundary read-only

The sibling marketplace checkout is evidence for where the follow-up belongs, not an edit target. The pstack change may name its path and stale entry, but it must not modify that checkout or the installed host. Any future execution of the marketplace task needs its own scope and authority.

### Validate the same guard that exposed the defect

After the two annotations, run `openspec validate --archived --strict` and confirm no unchecked archived tasks remain. Also run the pstack harness checks and inspect the two task lines to ensure they include `deferred`, a reason, and a follow-up while retaining the original external action.

## Risks / Trade-offs

- A checked deferred outcome differs from the CLI's usual execution-oriented checkbox semantics. The explicit wording and durable spec prevent it from being mistaken for runtime proof.
- Strict validation will pass while external marketplace synchronization remains undone. The archive text must keep that gap visible, and the follow-up must remain actionable.
- Historical files are being amended. This is narrowly limited to two transparent outcome annotations under the approved hygiene change; proposals, specs, designs, ADRs, and other task intent remain untouched.

## Migration Plan

1. Create and validate this intent-driven change.
2. Amend only task 3.3 in `2026-08-31-pstack-release-actions-proof/tasks.md` and `2026-08-31-pstack-release-tag-host-push/tasks.md`.
3. Run strict archived validation, pstack harness tests, and a focused text check for the deferred annotations.
4. Review the diff and confirm the sibling marketplace checkout and installed host state are unchanged.
5. Commit the validated local hygiene/spec changes as semantic atomic OpenSpec delivery. Leave release actions, external marketplace updates or host mutations, remote pushes, and archive actions to separately authorized operators.

Rollback is a normal revert of the two task-line amendments and the durable spec sync; no runtime or remote state changes occur.

## Open Questions

None. The external follow-up remains intentionally unexecuted and clearly identified; no new durable ADR is needed.
