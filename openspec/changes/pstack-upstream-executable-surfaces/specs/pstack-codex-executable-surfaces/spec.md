## ADDED Requirements

### Requirement: Codex compatibility tools have an explicit bounded surface

Feature: pstack-codex-executable-surfaces

The repository MUST retain and identify the following executable compatibility surfaces: `skills/poteto-mode/scripts/orch/orch.ts`, `skills/poteto-mode/scripts/orch/store.ts`, their tests, `skills/poteto-mode/scripts/watch-pr/watch-pr` and its TypeScript implementation/tests, `skills/poteto-mode/scripts/check-plan.mjs`, and `skills/poteto-mode/scripts/worktree-audit.sh`. `skills/poteto-mode/references/codex-tools.md` MUST identify them as Codex compatibility utilities. Grok durable orchestration MUST use canonical host task, agent, monitoring, and scheduler state instead of invoking `scripts/orch` or `scripts/watch-pr`, and MUST NOT create a repository-local orchestration store. Mapped read-only validation and cleanup playbooks MAY invoke `check-plan.mjs` and `worktree-audit.sh`; those utilities MUST NOT own durable host state.

#### Scenario: executable inventory has a testable entrypoint

- **GIVEN** the pstack checkout
- **WHEN** an operator inspects `skills/poteto-mode/scripts/package.json`
- **THEN** the package test command covers `orch` and `watch-pr`
- **AND** the strict typecheck covers `watch-pr`
- **AND** the listed executable files and their focused tests exist

#### Scenario: Grok does not acquire Codex local orchestration state

- **GIVEN** a Grok playbook needs durable units, agent status, a wake, or a frontier
- **WHEN** the playbook performs that operation
- **THEN** it uses the host-native primitive mapped in `HARNESS.md`
- **AND** it does not invoke `scripts/orch`, `scripts/watch-pr`, or create a repository-local orchestration store

### Requirement: watch-pr reports missing command dependencies as typed query failures

Feature: pstack-codex-executable-surfaces

The real `watch-pr` GitHub reader MUST convert a missing `gh` executable into `WatcherQueryError` with a retryable `command-error` failure and a bounded diagnostic. The error MUST pass through the existing CLI error/reporting path rather than escaping as an untyped process error.

#### Scenario: missing gh is retryable and bounded

- **GIVEN** `watch-pr` starts with no executable named `gh`
- **WHEN** the GitHub reader runs its first command
- **THEN** it rejects with `WatcherQueryError`
- **AND** the failure kind is `command-error`
- **AND** the failure is retryable
- **AND** the diagnostic names `gh` without dumping an unbounded process object

### Requirement: worktree audit preserves evidence conservatively across hosts

Feature: pstack-codex-executable-surfaces

`worktree-audit.sh` MUST preserve worktree paths containing spaces, use GNU or BSD `stat` when available, and accept `PSTACK_TRANSCRIPTS_DIR` as the transcript root. If the best-effort fetch does not produce `origin/main`, the audit MUST report merge status as `unknown` rather than `no`. The script remains a Codex/GitHub compatibility utility and MUST NOT pretend that missing forge or transcript data proves safety.

#### Scenario: path-safe audit on Linux

- **GIVEN** a repository whose worktree path contains spaces and whose host provides GNU `stat`
- **WHEN** `worktree-audit.sh` runs
- **THEN** it emits the complete path
- **AND** it does not drop the worktree from its report because of field splitting

#### Scenario: missing base is not a negative merge result

- **GIVEN** `git fetch origin main` cannot establish `refs/remotes/origin/main`
- **WHEN** `worktree-audit.sh` classifies a worktree
- **THEN** its merge field is `unknown`
- **AND** it does not label the worktree `no` solely because the ref is unavailable

#### Scenario: closed PR does not prove a merge

- **GIVEN** `origin/main` is unavailable and the forge reports a `CLOSED` PR
- **WHEN** `worktree-audit.sh` classifies a clean worktree
- **THEN** its bucket is `review`
- **AND** it does not label the worktree safe without a merge proof

#### Scenario: transcript root is explicit

- **GIVEN** `PSTACK_TRANSCRIPTS_DIR` points to a readable transcript tree
- **WHEN** `worktree-audit.sh` searches for recent chat evidence
- **THEN** it searches that tree
- **AND** it does not require a Cursor-specific default path
