# Core feature: CLI and wiki navigation

## Sub-features
Structural config, index membership, links, bad CLI input, nested page indexing.

## How to get to it (user POV)
Run `python3 scripts/llm_wiki.py check --wiki-dir .llm-wiki` and `python3 scripts/llm_wiki.py index --wiki-dir .llm-wiki`.

## Driving it with Codex
Use `bash .codex/skills/verify-llm-wiki/scripts/driver.sh drive`; pytest creates all negative fixtures under isolated `tmp_path`.

## Gotchas
A structural pass is not typed schema validation, semantic citation verification, or a promise of Markdown-parser completeness.
