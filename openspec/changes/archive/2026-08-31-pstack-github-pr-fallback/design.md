## Context

Upstream playbooks (opening-a-pr, shipping, babysit, autopilot-stack, autopilot-full, orchestrate) call `gt`. HARNESS already degrades to `gh` in one sentence. `gt` is not on this PATH. `gh` is.

User constraint: do not edit upstream pstack playbook files. Adapter-only: HARNESS plus a new reference.

## Goals / Non-Goals

**Goals:** A named GitHub-native map agents read when `command -v gt` fails.

**Non-Goals:** Rewriting `playbooks/*.md`. Editing `.worktrees/upstream-cursor-plugins`. Replacing `/poteto-mode` babysit with bundled `/pr-babysit`. Changing tommy-mode merge-to-main house style.

## Decisions

1. **New reference, not playbook edits.** Playbooks stay Graphite-first. HARNESS already says playbook steps stay and the CLI is not assumed.
2. **Detect once.** `command -v gt`. If missing, use the map for the rest of the run.
3. **Independent PRs off main.** Stacked work uses `gh pr create --base <parent-branch>`. No Graphite metadata.
4. **No GitHub auto-merge on stacked children.** Same invariant as shipping.md step 5.

## Risks / Trade-offs

- [Agents still copy `gt` from playbooks] -> HARNESS plus the reference are the rewrite column. Tests lock the pointer.

## Migration Plan

Docs only. Reinstall pstack after pin.

## Open Questions

None.
