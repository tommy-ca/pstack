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

## 4. Intent-driven schema and spec honesty

- [x] 4.1 Ship `openspec/schemas/intent-driven/` so `openspec status` resolves.
- [x] 4.2 Specs name prompt-enforced Slack `thread_ts` vs hook-enforced merge/force-push.
- [x] 4.3 Change `design.md` and `adr.md`. Repo ADR `adr/0001-benny-opt-in-copies-not-plugin-hooks.md`.
- [x] 4.4 `openspec validate pstack-benny-atomic-blocks --type change --strict`.
- [x] 4.5 Tests lock schema resolve, `design.md`/`adr.md`, and `fail-closed.sh` allow of non-merge commands.

## 5. Upstream reference vs live grok path

- [x] 5.1 Specs name Cursor `skills/` as **upstream reference**. Live grok files are `grok/triage.md` and `grok/repro.md`.
- [x] 5.2 Workflows read those grok files. They do not instruct following Cursor SKILL.md as the coordinator.
- [x] 5.3 ADR `adr/0002-benny-cursor-pack-is-upstream-reference.md`.

## 6. Plugin-installed sibling tree

- [x] 6.1 Move live grok Benny to `automations/benny-grok/`.
- [x] 6.2 `plugin.json` `skills` includes `./automations/benny-grok/skills/`. No `hooks` key.
- [x] 6.3 ADR `adr/0003-benny-grok-is-plugin-installed.md` supersedes 0001 copy recipe.

## 7. Audit fix

- [x] 7.1 Design.md matches plugin skills live path. No deleted `grok/triage.md`.
- [x] 7.2 ADR `adr/0004-benny-live-path-is-plugin-skills.md` supersedes 0002 live path.
