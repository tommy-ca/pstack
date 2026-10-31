---
name: verify-llm-wiki-formal
description: "Use when changing PStack wiki raw-source write semantics, replay/collision handling, or proof claims requiring source-to-code alignment and bounded or TLA+ state verification."
disable-model-invocation: true
---

# Formally analyze wiki source immutability (bounded)

Derived from `skills/create-formal-verification-skill/SKILL.md`. This does **not** claim a completed external TLA+ check. The current executed-in-CI target is an exhaustive **bounded real-code state exploration**; a separate TLA+ specification is included for optional independent TLC validation.

## Coverage and sync record

- **Covered production commit:** `bed363e12c5bb31459b263b4d6d9da409a15db80` (the wiki safety implementation in `scripts/llm_wiki.py`; confirm the diff to the current head before using).
- **Target code:** `scripts/llm_wiki.py::ingest_file` (`dest.open("xb")`, conflict refusal, exact replay), `check_wiki` path checks and `main` CLI. Only `ingest_file` is modeled by the bounded checker.
- **Safety property:** Once a basename has captured bytes in a wiki root, later ingests under the bounded event alphabet cannot change them; identical replay must not fail.
- **Bound:** all ordered traces of length 1, 2 and 3 over `{shared.md:A, shared.md:B, other.md:C}` = **39** histories, serialized calls through production Python, isolated temp roots. This is not proof of all byte strings, arbitrary process interleavings, race-free directory ancestry, crash durability, or source→log transactional atomicity.
- **Code-alignment rule:** after changing any listed ingest path or source destination, inspect `git diff bed363e..HEAD -- scripts/llm_wiki.py`, reason about linearization, update this skill's sync commit only after the tests and negative mutant still agree with the new implementation.

## Model and checker choice

`scripts/verify_llm_wiki_model.py` is a small finite-state exhaustive test harness that calls real production code for each trace and asserts immutability and replay semantics. The explicit mutant `broken_overwrite` must trigger a counterexample. This bounds the **real code path**, unlike a standalone state model.

Optional `model/WikiRawImmutability.tla` and `.cfg` express a smaller abstract `raw/original` transition invariant for TLC. Run TLC **only with independently installed, pinned Java + TLC jar** and record the version, state count and exact command. Missing TLC/Java means `BLOCKED`, not PASS. TLC results would apply to the abstract model, not prove actual Python concurrency.

## Launch

No live service. Python 3.10+ and pytest for bounded code-level checks. TLC is optional. Use the Codex [functional verifier](../verify-llm-wiki/SKILL.md) for CLI user paths.

## Doctor

`python3 -m pytest -q tests/test_llm_wiki_bounded_model.py`. Report only bounded coverage. For TLC, check `java -version` and the pinned jar and report UNTESTED if not available.

## Drive

```sh
python3 scripts/verify_llm_wiki_model.py
python3 -m pytest -q tests/test_llm_wiki_bounded_model.py
# OPTIONAL, only when a known, verified TLC jar is installed:
# java -cp "$TLC_JAR" tlc2.TLC -config .codex/skills/verify-llm-wiki-formal/model/WikiRawImmutability.cfg .codex/skills/verify-llm-wiki-formal/model/WikiRawImmutability.tla
```

## Proof bar

The 39 real-code traces pass; an intentionally overwritten raw source causes `broken_overwrite` to fail a reachable trace; a changing real-code implementation triggers requalification. A missing tool, stale sync commit, unexecuted model, or a mutant that no longer fails is NOT a proof. Any failed actual code invariant is a finding, not something to weaken away.

## Evidence

Capture git commit, coverage bounds, command/output, touched code/functions, actual negative counterexample and model assumptions. Separate `offline` finite trace proof from `formal-TLC` (UNTESTED unless TLC really runs) and from host-live observation. Do not promote a code sync record merely because tests pass on an unchanged model.

## Cleanup

Trace explorer uses unique `TemporaryDirectory` directories and cleans them. Preserve negative control receipts elsewhere. No server, process PID or shared filesystem fixture is owned persistently.

## Helpers

`python3 scripts/verify_llm_wiki_model.py` and `python3 -m pytest -q tests/test_llm_wiki_bounded_model.py`. Use `/maintain-formal-verification-skill` whenever covered code changes without a corresponding recheck.
