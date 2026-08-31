# Require design and ADR artifacts before archive

- Status: accepted
- Date: 2026-08-31

## Context

OpenSpec's intent-driven workflow orders proposal, specs, design, ADR review, and tasks, but strict validation of existing archived directories does not by itself reject historical changes missing `design.md` or `adr.md`. A task-complete active change can therefore look ready to archive while its durable rationale is absent.

## Decision

The PStack repository harness MUST check active task-complete OpenSpec changes for both `design.md` and `adr.md` before archive. Incomplete planning changes and `openspec/changes/archive/` remain outside this guard; OpenSpec's normal artifact validation handles their other lifecycle requirements.

## Consequences

Future task-complete changes cannot pass the repository's static verification gate without a design and ADR review manifest. Historical archives are preserved as-is, so the guard prevents new omissions without rewriting history. A malformed or missing task list remains an OpenSpec validation concern rather than an archive-readiness claim.
