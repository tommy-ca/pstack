## 1. Specs and design

- [x] 1.1 Inventory Benny pack vs grok primitives (hooks, workflows, scheduler_create).
- [x] 1.2 OpenSpec capabilities: pack, triage, repro, safety, grok remap.
- [x] 1.3 Design doc: data flow and Cursor vs grok table.
- [x] 1.4 `python3 tests/test_verify_harness.py` includes `test_benny_is_source_and_has_grok_remap`.

## 2. Grok remap (opt-in copies)

- [x] 2.1 `automations/benny/grok/README.md` copy recipe. No `/automate`. No `.cursor/automations`.
- [x] 2.2 `hooks/hooks.json` plus `bin/fail-closed.sh` deny merge and force-push.
- [x] 2.3 `workflows/benny-triage.rhai` and `benny-repro.rhai`. `validate_only` one path each.
- [x] 2.4 HARNESS Benny row names `automations/benny/grok`. plugin.json still has no `hooks`.

## 3. Review

- [x] 3.1 Independent verifier: tests PASS, plugin.json has no hooks, workflows exist.
