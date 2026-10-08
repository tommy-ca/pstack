# Core Feature: contract-spec

## Sub-features
- OpenSpec change schema validation
- OpenSpec formal specification validation
- Formal and delta requirement parity

## How to get to it (user POV)
Inspect `openspec/specs/pstack-jev-decisions/spec.md` and `openspec/changes/pstack-jev-decision-plane/specs/pstack-jev-decisions/spec.md`.

## Driving it with Codex
Execute `openspec validate pstack-jev-decision-plane --type change --strict` and `openspec validate pstack-jev-decisions --type spec --strict`.

## Gotchas
Strict validation requires exact requirement names and scenario headings.
