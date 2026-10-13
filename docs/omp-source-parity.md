# OMP source-parity matrix

Source-anchored capability matrix for [`profiles/omp.json`](../profiles/omp.json) (#289).
It answers one question per capability: which OMP mechanism carries it, how strong that
carriage is, and what evidence — if any — actually observed it.

Nothing here is a claim by itself. A row may only read `verified` when a scenario in
`.audit/evidence/omp-receipt.json` settles it at `evidence_level: observed_live`; rows
without an observed settlement are recorded as `static-only` or `gap`. There is no
`documented` status: upstream documentation is attribution, never evidence.

## Pins

| Surface | Revision |
|---|---|
| OMP behavioral source | `can1357/oh-my-pi@0affc77e41c357bb33f8bf056c3ea3cf50fd408b` (audited head `2070e304` adds no reviewed RPC/task/skill/plugin doc change) |
| Canonical pstack | `df581122cde17e6e27686b5a448bde23e4ad4318` (`UPSTREAM`) |
| Runtime receipt | `.audit/evidence/omp-receipt.json` (`omp/18.9.1`, `overall_verdict: PASS`) |

## Matrix

| Capability | Native mechanism | Implementation | Enforcement | Verification | Source / attribution @ pin |
|---|---|---|---|---|---|
| agent.spawn | `task` subagent tool | native | hard | verified | scenario `runtime-child-spawn-omp` (observed_live); `docs/tools/task.md` @ `0affc77` |
| agent.join | `task` completion (`prompt_result` / `session_settled`) | native | hard | verified | scenario `runtime-child-spawn-omp` (observed_live); `docs/tools/task.md` @ `0affc77` |
| agent.message | `task` session continuation, `agent://<id>` peer write | native | hard | static-only | `docs/tools/task.md`, `docs/rpc.md` (`steer_subagent`) @ `0affc77` — no settling scenario |
| agent.cancel | `proc://<id>/kill`, RPC `cancel_subagent` | native | hard | static-only | `scripts/drivers/omp.py` `child_cancel`; `docs/rpc.md` @ `0affc77` — `runtime-child-cancel-omp` not promoted |
| agent.resume | `omp --resume` (cold parent), child handle revival | native | hard | static-only | cold-parent run 2026-10-12 (session sha256 `e2cad864…`); `docs/sdk.md` @ `0affc77` — no settling scenario |
| workspace.shared | parent cwd, single repository | native | hard | static-only | `docs/tools/task.md` @ `0affc77` (non-isolated spawns run in the parent cwd) — no settling scenario |
| workspace.isolated | git worktree / overlay (`task.isolation.backend`) | native | hard | verified | scenario `runtime-isolation-omp` (observed_live); `docs/tools/task.md` @ `0affc77` |
| workspace.readonly | plan-mode read-only tool set | native | advisory | static-only | `docs/tools/task.md` @ `0affc77` — no per-spawn read-only field exists |
| human.ask | `ask` tool | native | advisory | static-only | `docs/tools/ask.md` @ `0affc77` — no settling scenario |
| human.gate | `ask` blocking confirmation | native | advisory | static-only | `docs/approval-mode.md` @ `0affc77` (prompt tier before write/exec, fails closed) — no settling scenario |
| plan.update | `todo` tool | native | advisory | static-only | `docs/tools/todo.md` @ `0affc77` — no settling scenario |
| schedule | none | gap | advisory | unverified | OMP @ `0affc77` exposes no cron or scheduled-run surface, so no scenario can settle the row |
| monitor | read `proc://<id>`, RPC `get_subagents` | shim | soft | static-only | `docs/tools/task.md`, `docs/rpc.md` @ `0affc77` — non-consuming inspection only |
| session.persist | file-backed `SessionManager` (`.jsonl`) | native | hard | static-only | `docs/sdk.md` @ `0affc77` — no settling scenario |
| session.resume | `SessionManager.continueRecent` / `open` / `list`, `--resume` | native | hard | static-only | `docs/sdk.md`, `docs/session-operations-export-share-fork-resume.md` @ `0affc77` — no settling scenario |
| evidence.capture | receipts under `.audit/evidence/` | native | hard | static-only | scenario `runtime-evidence-capture-omp` (offline: durable receipt exists, no live capture observed) |
| verify | `scripts/verify-portable.py` | native | hard | static-only | scenario `doctor-profile-omp` (offline: typed profile validates through `scripts/portability_schema.py`) |

## Boundaries and open gaps

- **Depth is policy, not observed host control.** `runtime-child-spawn-omp` prompts and joins
  one child; no nested grandchild spawn or refusal probe has run, so `max_subagent_depth 1`
  remains a pstack policy claim.
- **Steering is unsupported as shipped.** The bounded `--mode rpc` session exposes no
  `steer_subagent` method even though upstream documents one; `agent.message` stays
  `static-only` and is recorded as a gap, never as a claim.
- **Cancellation is driven but unpromoted.** `runtime-child-cancel-omp` exercises
  `cancel_subagent` with the `data.cancelled: true` acceptance flag and bounded negative
  paths, yet the row stays `static-only` until the promotion gate passes.
- **Resume was observed outside the receipt.** Cold-parent resume preserved context on
  2026-10-12, but no receipt scenario settles it, so `agent.resume` stays `static-only`;
  child handle revival has never been observed.
- **Read-only is advisory.** Plan mode narrows the tool set by convention and rejects
  isolation/apply controls; no per-spawn read-only field exists, so enforcement is `advisory`.
- **Offline scenarios are not live proof.** `evidence.capture` and `verify` pin real
  scenarios, but both are `offline`; they keep the row `static-only`.
- **No hidden capability.** All 17 identifiers are the normative atomic set; every OMP
  mechanism above is a binding or composition, and `schedule` is an explicit `gap`.

## Re-verify

```sh
.venv/bin/python -m pytest tests/test_portability_schemas.py -q
.venv/bin/python scripts/verify-harness.py
PSTACK_RUN_OMP_LIVE=1 python3 scripts/verify-portable.py run --host omp   # regenerates the receipt
```
