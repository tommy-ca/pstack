## ADDED Requirements

### Requirement: Hygiene nested-cache apply fail-closes on error

Feature: pstack-refresh-hygiene

`--apply` MUST collect would-delete nested overlay clones first, then delete. A Guard or OSError MUST emit `action=error` and still print TSV. `main` MUST exit 2 when any `--apply` row has `action=error`. `deleted` MUST appear only when the path is gone. The primary overlay cache MUST NOT be deleted. A registered git worktree path MUST NOT be deleted. A symlink or symlink parent MUST stay `keep`.

#### Scenario: apply error still prints TSV and exits 2

- **GIVEN** a nested overlay clone that Guard refuses or `rmtree` fails
- **WHEN** `python3 skills/swarm/scripts/refresh-hygiene.py --root <repo> --apply` runs
- **THEN** stdout still contains the TSV header
- **AND** a nested-cache row has `action` `error`
- **AND** the process exit code is 2

### Requirement: Apply-skills writes only claude-shaped non-symlink dests

`--apply-skills` MUST copy git-tracked `skills/reflect/SKILL.md` only when the dest file is claude-shaped and `has_symlink_parent(dest)` is false. A symlink dest or dest parent MUST fail closed as `stale-skill eperm` without chmod. A grok-shaped dest MUST refuse as not-stale. `--host-script` MUST print `cp -- <src> <dest>` with dest equal to the overlay path, not `Path.resolve()` through a leftover symlink into `~/.agents`. Default dry-run MUST NOT write `~/.grok/skills`.

#### Scenario: host-script dest is overlay path

- **GIVEN** `--skills` pointing at a leftover overlay path
- **WHEN** `--host-script` runs
- **THEN** stdout starts with `cp --`
- **AND** dest is the overlay path, not a resolved `~/.agents` path

#### Scenario: apply-skills on symlink parent is eperm

- **GIVEN** dest parent is a symlink
- **WHEN** `--apply-skills` runs
- **THEN** a `stale-skill` row has `action` `eperm`
- **AND** dest bytes and mode are unchanged
- **AND** the process exit code is 2
