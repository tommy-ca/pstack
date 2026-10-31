# Core feature: bounded real-code invariants

## Sub-features
39 exhaustive ordered input traces through production `ingest_file` and deliberate overwrite-mutant rejection.

## How to get to it (user POV)
Run `python3 scripts/verify_llm_wiki_model.py` to read PASS/FAIL with the bound and negative control.

## Driving it with Codex
`python3 -m pytest -q tests/test_llm_wiki_bounded_model.py` checks both real code and mutant.

## Gotchas
This is bounded serial state-space exploration of real Python, not TLC output, an unbounded theorem, or general concurrent write proof. See `verify-llm-wiki-formal` for the proposed TLA+ model.
