## Why

Grok `MAX_SUBAGENT_DEPTH` is 1. Autopilot-full and autopilot-stack spawn writer children that then invoke `/no-comments`, which spawns `pstack:comment-sicko`. That is depth 2 and fails. They also arm `/goal`, which `pstack-grok-natives` skipped. Production-ready overnight on grok is parent-fanout plus `/loop`, not those two as written.

## What Changes

- Spec `pstack-depth-1-overnight`.
- Autopilot playbooks: parent owns every spawn including `pstack:comment-sicko`. No `/goal`.
- Overnight guide names the depth-1 rule.

## Capabilities

### New Capabilities

- `pstack-depth-1-overnight`: queue playbooks parent-fanout. Writers do not spawn. No `/goal` arm.

### Modified Capabilities

None.

## Impact

`skills/poteto-mode/playbooks/autopilot-full.md`, `autopilot-stack.md`, `docs/guide/07-overnight.md`.
