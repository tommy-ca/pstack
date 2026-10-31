---
name: verify-llm-wiki
description: "Use when changing the PStack project-local .llm-wiki CLI, raw source capture, Markdown navigation, or source/link integrity verification."
disable-model-invocation: true
---

# Verify PStack LLM Wiki CLI

Generated from `skills/create-verification-skill/SKILL.md` and tailored to actual Python CLI entry points. This **host-native Codex skill** is not a portable shared skill or a QStack publisher. Read [the feature map](features/README.md) before a full sweep.

## Launch

No server: the application is a short-lived Python CLI. From the repository root run `bash .codex/skills/verify-llm-wiki/scripts/driver.sh launch`. A usable instance is Python 3 with pytest available, existing `.llm-wiki/config.json` and `scripts/llm_wiki.py`. Scratch drives use pytest `tmp_path` and isolated temporary wiki roots. No shared service, port or provider credentials are required.

## Doctor

`bash .codex/skills/verify-llm-wiki/scripts/driver.sh doctor` checks Python, pytest and the real `scripts/llm_wiki.py check --wiki-dir .llm-wiki`. Doctor is read-only relative to the tracked project wiki, and **cannot** assert typed schema validation, external references, generated-index byte equality, or semantic correctness.

## Drive

`bash .codex/skills/verify-llm-wiki/scripts/driver.sh drive` first runs Doctor, then the actual CLI and pytest contracts in isolated scratch directories: `tests/test_llm_wiki.py`, `tests/test_llm_wiki_safety.py`, `tests/test_llm_wiki_bounded_model.py`, and `scripts/verify_llm_wiki_model.py`. This is a real production-Python-code negative control, not an LLM provider/model or full model-checker execution.

## Proof bar

- Clean tracked wiki passes the structural CLI check; broken/local out-of-root links fail.
- The first source revision is stored once; conflicting same-basename bytes are refused without altering accepted bytes. Exact replay is idempotent.
- A symlinked raw directory or capture target cannot redirect the trusted file write in the tested setup.
- The model verifier exhaustively explores 39 serial traces (length 1–3 over three predefined inputs) through production `ingest_file` and detects a deliberate overwrite mutation.
- Tests exercise a real CLI nonzero on collision. **No proof** of malicious concurrent directory swaps, all Markdown syntax, arbitrary run-time interleavings, TLA+ results, crash-safe source+log commit, or cross-repository QStack publisher authority.
- Reduce negative results by FAIL > BLOCKED > UNTESTED > PASS; a skipped optional checker is not a proof.

## Evidence

Record the exact git HEAD, command, Python/pytest version, exit code, 39-trace count, failing-mutant evidence, and affected files. Terminal/CI logs are `offline` evidence. For durable local transcripts, invoke driver with `LLM_WIKI_EVIDENCE_DIR` set to an **owned unique directory**; the driver saves a per-run transcript without overwriting an existing receipt. Never label these results `observed_live` host-native/model execution. Keep stdout/stderr of a broken control as proof, not as a PASS of the broken code.

## Cleanup

No process is launched. Tests use their own pytest scratch roots, and bounded-model checks use `TemporaryDirectory`; both clean their own scratch data. `driver.sh cleanup` prints the owned-resource state and never kills another user's process or deletes durable evidence.

## Helpers

```sh
bash .codex/skills/verify-llm-wiki/scripts/driver.sh {launch|doctor|drive|cleanup}
python3 scripts/verify_llm_wiki_model.py
python3 scripts/scaffold_verification_skill.py --check --target-dir .codex/skills/verify-llm-wiki
```

The helper uses GNU `timeout` and refuses to run unbounded if it is missing. Every subprocess is bounded to 60 seconds. The companion [formal skill](../verify-llm-wiki-formal/SKILL.md) describes what remains unproved.
