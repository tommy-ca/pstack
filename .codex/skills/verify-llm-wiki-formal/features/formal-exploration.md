# Formal Feature: Formal state exploration

## Sub-features
- 39 exhaustive serial execution traces through production ingest_file
- Deliberate overwrite mutant rejection in bounded state space
- Abstract TLA+ specification for TLC model checking

## How to get to it (user POV)
Run `python3 scripts/verify_llm_wiki_model.py` to observe trace state verification.

## Driving it with Codex
Execute `python3 -m pytest -q tests/test_llm_wiki_bounded_model.py` to drive bounded state exploration.

## Gotchas
TLC jar and runtime are optional; missing TLC tools report BLOCKED rather than PASS.
