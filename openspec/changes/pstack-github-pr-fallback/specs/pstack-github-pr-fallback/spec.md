## ADDED Requirements

### Requirement: GitHub-native PR path when Graphite is missing

Feature: pstack-github-pr-fallback
Rule: do not invent `gt` when it is not on PATH

`HARNESS.md` MUST point at `skills/poteto-mode/references/github-pr-fallback.md`. That file MUST map Graphite call sites to `gh pr create`, `gh pr view`, `gh pr checks`, and `gh pr merge`. It MUST forbid `gh pr merge --auto` on a PR whose base is not protected trunk. It MUST say stacked work without `gt` uses `gh pr create --base <parent-branch>`. Official `playbooks/*.md` MUST stay Graphite-first and MUST NOT be rewritten in this change.

#### Scenario: harness names the fallback

- **GIVEN** `HARNESS.md`
- **WHEN** Graphite `gt` is not on PATH
- **THEN** the Graphite row names `github-pr-fallback.md`
- **AND** it names `gh pr`

#### Scenario: fallback forbids collapsing a stack

- **GIVEN** `skills/poteto-mode/references/github-pr-fallback.md`
- **WHEN** an agent would arm GitHub auto-merge
- **THEN** the page says not to use `--auto` unless the PR targets protected trunk

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
