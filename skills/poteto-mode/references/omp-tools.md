# OMP tool mapping for pstack

This document maps portable pstack capabilities (defined in [`pstack-portability`](../../../openspec/specs/pstack-portability/spec.md)) directly to Oh-My-Pi (OMP) native primitives and execution conventions.

## Tool actions

| Portable Capability | OMP Primitive | Claude Code Equivalent | Grok Reference |
| --- | --- | --- | --- |
| Read / edit / shell / search | `read`, `edit`, `write`, `bash`, `grep`, `glob` | Read / Edit / Bash | `run_command`, `write_to_file` |
| Fetch a URL | `read`, `web_search` | WebFetch / Bash | `read_url_content` |
| Invoke a skill | Skills load natively via plugin manifest | Skills load natively | Skills load natively |
| `agent.spawn` | `task` | `Agent` | `spawn_subagent` |
| `agent.fan_out` | N `task` concurrent calls | N `Agent` in one turn | N `spawn_subagent` in one turn |
| `agent.join` | `task` completion / handle | wait on Agent handles | `get_command_or_subagent_output` |
| `plan.update` | `todo` / `todo.md` | todolist | `todo_write` |
| `human.ask` | `ask` | `AskUserQuestion` | `ask_user_question` |

## Subagent policy

- Subagent dispatch uses native OMP concurrency limits (`task.maxConcurrency`, `async.maxJobs`); the keep-alive `workpool()` is a reuse optimization, never an independence guarantee.
- Writers isolate with git worktrees (`workspace.isolated`).
- Depth is capped at 1; parent owns every spawn.
- File pointers are passed instead of inlined dumps.

## Compositional dispatch (swarm, arena, interrogate)

Two native dispatch routes satisfy `agent.spawn` / `agent.join`. They are separate
host paths, not interchangeable, so a run records which route it used.

Only the `task` route is **driven**, and only for the single-child lane: the driver
starts one RPC session, prompts a single `task` child, reduces that child's
settlement and cancels it through the RPC `cancel_subagent` call
(`scripts/drivers/omp.py:323` spawn/settlement, `scripts/drivers/omp.py:503`
cancel, `scripts/drivers/omp_rpc.py:348`). The eval `agent()` route is
**undriven** — no `agent()`, `handle.cancel()` or handle-join path exists in the
driver — so it is recorded here as documented aspiration, not as behavior a run
can observe. Within the `task` column, cells and fragments marked **undriven**
name a mechanism outside that lane, which no driver path exercises: the lane the
driver does exercise is the spawn, isolation, settlement and RPC cancel of one
child.

| Step | `task` route | eval `agent()` route (undriven) |
| --- | --- | --- |
| Fan-out | one call with a `tasks[]` batch (`task.batch`, default on) — **undriven**: the driver prompts a single child, there is no batch path; `context` carries the shared brief — **undriven**: the driver passes no shared context | one `agent(prompt, {...})` per lane, handles collected in one cell |
| Isolation | `isolated: true` per item (`task.isolation.enabled`); plan mode off | `isolated: true` per call; plan mode off |
| Join | background-job completion, or the `wait` tool — **undriven**: the driver reduces the prompt settlement (`wait_settled`), it never waits on a background job or a handle | `wait(handles, timeout)`; `raise_errors=False` returns a failed or cancelled handle in its slot |
| Cancel | `write proc://<id>/kill` (job id or agent id) — **undriven**: the driver cancels via RPC `cancel_subagent` | `handle.cancel()` |
| Inspect | `agent://<id>` / `history://<id>` — **undriven**: the driver reduces the session frame log, it never reads an agent or history URL | `handle.output()` / `history://<id>` |

Rules both routes share:

- **Frozen briefs.** A lane's brief is fixed before dispatch and is the brief it
  reports against. A rewritten brief is a new lane; follow-up work is a fresh
  spawn, never a resume with different scope. A child session starts without the
  parent's conversation history, so the brief carries the context the lane needs.
- **One writer per target.** Writers run `isolated` with one target each; the
  backend may be a worktree, an overlay or a copy. Two lanes never share a
  writable path.
- **Bounded join.** The join deadline is named before spawn. A lane still running
  at the deadline is a dropout: `wait(handles, timeout)` raises `TimeoutError`
  there, and a cancelled lane settles as `cancelled` in the typed settlement.
  Aborting a wait cancels the handles it was waiting on and waits for them to
  settle, so aborting is not a nudge. A timeout leaves that lane running, so a
  lane past the deadline is cancelled explicitly rather than assumed ended. A
  dropout is never a pass.
- **Keep-alive reuse is not independence.** `workpool()` keeps workers alive and
  hands the next item to the idle worker with the lowest context usage, so a
  reused worker carries the previous item's context. It MUST NOT be presented as
  a blinded independent context unless `eval.workpool.freshAgents=true` was
  observed in the run's effective settings, which instead gives every item a
  fresh agent and no follow-up batching. Absent that observation the run reports
  reused contexts as an adaptation or a gap. `task` items and `agent()` handles
  are unaffected: each child gets its own session and never inherits the parent's
  eval kernel state. Explicitly passed kernel-defined `tools` are the one bridge
  back into the parent kernel, and they run there.
