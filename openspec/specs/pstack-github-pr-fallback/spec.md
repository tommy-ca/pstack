## Purpose
When Graphite `gt` is missing or not selected, pstack resolves GitHub `gh` by default or Origin when its CLI resolves the repository. PR and stack landing stays forge-neutral and does not require Graphite.

## Requirements

### Requirement: GitHub-native PR path when Graphite is missing

Feature: pstack-github-pr-fallback

Rule: pstack PR operations must not require Graphite

`HARNESS.md` MUST document GitHub CLI (`gh`) as the default forge path and Origin as an optional path only when its CLI resolves the repository. The retained PR and stack playbooks MUST use forge-neutral `gh`/Origin operations and MUST NOT require Graphite `gt`. Stacked work MUST use an explicit parent branch. GitHub `--auto` MUST be limited to a PR targeting protected trunk; stacked children MUST be landed one at a time rather than collapsed by GitHub auto-merge. Grok playbooks MUST retain the host `monitor` and `scheduler_create` boundaries instead of invoking the Codex compatibility watcher.

#### Scenario: harness names the fallback

- **GIVEN** no Origin CLI resolves the repository and Graphite is absent
- **WHEN** an operator reads `HARNESS.md`
- **THEN** it names the GitHub `gh` path as the fallback
- **AND** it does not make Graphite a prerequisite

#### Scenario: fallback forbids collapsing a stack

- **GIVEN** a child PR depends on a parent PR
- **WHEN** the fallback creates or retargets the child
- **THEN** it uses the parent branch as the child PR base
- **AND** it does not collapse the stack with GitHub auto-merge

#### Scenario: forge selection is explicit

- **GIVEN** a pstack playbook needs PR, stack, check, thread, or merge operations
- **WHEN** the playbook starts
- **THEN** it resolves `origin` once when available
- **AND** it otherwise uses `gh`
- **AND** it does not require `gt`

#### Scenario: stacked work keeps parent branches

- **GIVEN** a child PR depends on a parent PR
- **WHEN** the child is created or retargeted
- **THEN** its branch is rebased onto the exact parent tip
- **AND** its PR base is the parent branch
- **AND** the root PR alone targets protected trunk

#### Scenario: GitHub auto-merge cannot collapse a stack

- **GIVEN** an agent would arm GitHub auto-merge
- **WHEN** the PR targets an unprotected parent branch
- **THEN** the agent does not pass `--auto`
- **AND** the PR is landed only after the parent chain is handled one PR at a time

#### Scenario: Grok uses host-native wakes

- **GIVEN** the Grok adapter watches checks or an overnight cadence
- **WHEN** the playbook arms a wake
- **THEN** event status uses `monitor`
- **AND** recurring status uses `/loop` mapped to `scheduler_create`
- **AND** the playbook does not invoke `scripts/watch-pr/watch-pr`
