# ADR: Keep upstream refresh explicit and operator-owned

- **Status:** Accepted (retrospective archive repair)
- **Date:** 2026-08-31

## Decision

Expose upstream refresh information through `scripts/sync-from-upstream.py`: local pin and recipe output by default, with network-backed commit inspection only behind `--log`. Do not copy or merge upstream content automatically.

## Rationale

The port needs a repeatable refresh starting point, but automatic copying would overwrite intentional Grok adaptations. Reading the single `UPSTREAM` pin avoids duplicated metadata, while an explicit network flag makes credentials and network effects visible.

## Consequences

- Operators can inspect the refresh plan without network access.
- `--log` remains subject to repository access and host authentication.
- The port retains ownership of the final copy/review step.

## Evidence

The archived proposal, specs, and completed tasks establish this contract. This is a retrospective record, not a new claim about network execution.
