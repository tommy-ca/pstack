# Core Feature: canonical-routing

## Sub-features
- Upstream commit and tree binding
- Full 23-playbook canonical inventory coverage
- Closed decision classes without unclassified gaps

## How to get to it (user POV)
Inspect `references/decision-routing.json` and `references/decision-routing.md`.

## Driving it with Codex
Execute `python3 scripts/verify-decision-contract.py --root . --upstream-commit <commit.json> --upstream-tree <tree.json>`.

## Gotchas
Requires clean worktree when `--require-clean` is passed.
