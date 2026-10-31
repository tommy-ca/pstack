# Core feature: source-immutability

## Sub-features
Atomic exclusive create, basename collision refusal, idempotent exact replay, symlink rejection, write-safe read path.

## How to get to it (user POV)
Run `python3 scripts/llm_wiki.py ingest /tmp/some-file --wiki-dir /tmp/owned-scratch-wiki` with an isolated disposable destination, then repeat with different bytes using the same filename.

## Driving it with Codex
`python3 -m pytest -q tests/test_llm_wiki_safety.py` operates on scratch wiki copies.

## Gotchas
The source write and `log.md` append are **not one atomic transaction**; a process crash between them can yield a source without a corresponding log entry. The symlink preflight is not an adversarial OS sandbox or proof against concurrent ancestor replacement.
