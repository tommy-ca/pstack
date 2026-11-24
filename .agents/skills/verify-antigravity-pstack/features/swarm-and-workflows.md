# Subagents, Gated Swarm, and Workflows

## Sub-features

- Default `invoke_subagent` fan-out (`pro`, `flash`, `flash_lite`, `inherit`) with policy depth `1` vs runtime limit `10`
- Explicit `/swarm` guard (`agy 1.5.13+`) for `swarm`, `post_message`, `read_board`, `swarm_wait`, `swarm_pane`, and `swarm_monitor`
- Deterministic Python pipelines via `run_workflow` (`phase`, `parallel`, `pipeline`, `trajectory`)
- `define_subagent` `EnableWriteTools=True` requirement vs read-only built-in runner roles

## How to get to it (user POV)

Verify subagent spawn, isolation modes (`branch`, `share`, `inherit`), and tool-reference invariants through `tests/test_antigravity_verification.py` and `verify_portable.py` scenarios.

## Driving it with Antigravity

Run `uv run pytest -q tests/test_antigravity_verification.py tests/test_route_resolver.py -k antigravity` and `bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive`.

## Gotchas

- `reasoning_effort` must stay in `runtime_conventions.forbidden_spawn_fields` for `invoke_subagent`.
- Built-in roles like `arena-runners` are read-only; writers spawned cleanly with `define_subagent` need `EnableWriteTools=True`.
- `skill_order` `primary_pstack` entries must resolve to existing skill or playbook files (such as `/swarm`, never nonexistent names).
