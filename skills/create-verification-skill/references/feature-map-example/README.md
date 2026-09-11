# Notes verification map

This directory is the maintained source for verifying the user-facing behavior of Notes. Read the index before driving the app, then use the matching feature file as the recipe.

This file is the generator seed. Generated skills copy the shape to skill-root `features/`, next to `SKILL.md`. Do not nest the generated map under `references/features/`. Do not put it in OpenSpec.

## Why not a wiki

A wiki is for humans. Agents pay for every token they reread. Open one feature file for the change under test, not the whole corpus. Each file answers the same four questions: what exists, how a user reaches it, how to drive it with the harness, what usually lies. The README is the sweep order. Drift is fixed in the same PR as the product change, or by `/maintain-verification-skill`.

## Baseline preconditions

- Launch Notes at `http://127.0.0.1:4173` with a disposable data directory.
- Set `NOTES_DATA_DIR=/tmp/notes-verify-$RUN_ID` so concurrent runs do not share state.
- Seed notes titled `Quarterly plan` and `Grocery list`.
- Put `control-notes` and the `notes` CLI on `PATH`.
- Run `control-notes doctor` and require the expected URL, data directory, and build revision.
- Never drive an instance that was not started by this verification run. Refuse to double-drive a shared Notes instance.
- Isolation is `NOTES_DATA_DIR` plus `$RUN_ID`. Do not emit `--checkout` unless the app is a long-lived desktop driven over CDP from a git checkout.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run browser actions through `control-notes browser`.
- Run terminal actions through `control-notes cli -- <command>`.
- Restore seeded data after a mutation. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

Do not submit "look, it opens." A window that loaded is not proof.

- Exercise every reachable entry point, mode, gated variant, and the success, cancel, error, empty, and persistence paths the change can affect.
- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot and a screenshot with the app identity visible.
- CLI proof includes the command, stdout, stderr, and exit code.
- Mutation proof includes a read-only second view of the stored value.
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with <harness>` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Full sweep

Walk this map top to bottom for a broad regression. Order is create-note, then search. Driving one convenient entry point is not a sweep. This Notes sample has no cross-feature journeys file. Add one only when the app has paths that span feature files.

## Features

- [Create a note](./create-note.md) covers browser and CLI creation, cancellation, persistence, and cleanup.
- [Search notes](./search.md) covers toolbar, keyboard, and CLI search with matching, empty, and clear states.
