## Context

Grok user-guide `16-subagents.md` defines capability modes on the agent type, not on `spawn_subagent`. `execute` is read plus shell, no writes. This port already sets that field on seven agents. The schema spec only mentions `how-explorer`. The pytest only mentions `independent-verifier`. The write bit can drift.

Two shapes were compared.

1. Heuristic. Any agent body that says "Do not edit files" must have `execute`. This would sandbox `why-*` and `reflect-*`. HARNESS.md calls those prompt posture. Rejected.
2. Closed set. A frozen list of no-write stems must have `execute`. Everyone else must omit the field. Chosen. `why-*` and `reflect-*` are named prompt posture so they are not labeled writers.

`inheritSkills: false` is a skill-catalog switch. It is not the write bit. It stays out of this change.

## Goals / Non-Goals

**Goals:**

- Encode the no-write set in one test and one spec requirement.
- Fail if a no-write agent loses `execute`.
- Fail if a writer or prompt-posture agent gains `execute`.

**Non-Goals:**

- Do not change `inheritSkills`.
- Do not change why-agent posture.
- Do not update the installed host plugin.
- Do not archive other OpenSpec changes.
- Do not add a new capability name or a new script.

## Decisions

### Closed stem set in the test

The test owns a frozenset of seven stems. The spec names the same seven. The set is the type. Scanning body text is not.

### Omit vs execute, not read-only vs all

Writers omit `capabilityMode` so grok keeps default `all`. The test does not write `all` into YAML. Pinning `all` would be a larger, unrequested rewrite.

### comment-sicko stays in the no-write set

`/no-comments` applies deletions in the parent. comment-sicko reports. `execute` matches that split.

## Risks / Tradeoffs

A new no-write role must be added to the set in the same change that adds the agent file. That is the point of a closed set.

Copy-paste of `capabilityMode: execute` onto `feature` will fail CI. That is intended.

Local `.audit/` trails mention Cursor names while describing the port. `verify-harness.py` skips `.audit` at any path depth, matching `adapt-harness.py`, so a nested decision log cannot fail the leftover-Cursor or slug gates.

## Migration Plan

No runtime migration. Static test only.

## Open Questions

None.
