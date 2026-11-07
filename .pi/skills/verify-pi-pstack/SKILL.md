---
name: verify-pi-pstack
description: "Verify the standalone Pi candidate's host bindings, minimal extension policy, and explicit runtime proof boundary; preflight is not a native child or security proof."
disable-model-invocation: true
---

# Verify Pi PStack candidate

This existing project-local skill verifies PStack semantics on **standalone Pi**, distinct from OMP. It does not enroll a seventh shipped host or launch a second orchestration runtime. Read [core feature](features/core.md) and [extension-package feature map](features/extension-package.md) before claiming any result.

## Launch

`bash .pi/skills/verify-pi-pstack/scripts/driver.sh launch` runs `scripts/prove_pi_vertical_slice.py --live`. This observes the Pi binary and version. It parses `pi list`. It attempts `pi -p --no-session --no-tools`. That probe cannot spawn, join, cancel, authorize, or sandbox a child. The runtime plane must remain BLOCKED until a real actor driver records the required actions. Never upgrade a package-presence check to observed_live.

## Doctor

`bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor` runs `verify_pi_candidate.py check` and `model` checks. A source-level PASS covers the current 17-capability profile and 59 bounded mutations. The tiered minimum and documented Pi package role export require separate native verification. It does not mean any extension is installed, enabled, or secure at runtime.

## Drive

`bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive` requests the same Pi preflight pending future native actor-test integration. It exits 2 or BLOCKED without real child IDs, provider-qualified model selections, terminal states, and negative effects. A completed `echo HELLO` is neither a child launch nor an independent model review.

## Proof bar

Observe **both allowed and denied** child launch through the actual `pi-subagents` extension; also verify all 22 canonical roles resolve through the proposed native `pi.subagents.agents` resource, `effort` is explicitly mapped to Pi `thinking` when required, fresh children actually receive the selected PStack skills, and an `independent-verifier` child has a native denied write/bash path rather than prompt-only no-edit advice.  record child IDs, `subagent_launch` authorization, join/cancel/timeout, role/model identity, worktree cleanup and intended scopes. Confirm **pi-verdict** is enabled and deterministic deny floor works even if the model votes allow, `ask` in headless mode denies, custom/MCP tools cannot bypass policy, and `pi-ask-user` is not a hard `human.gate`. Verify the actual **pi-better-sandbox** OS backend on parent, foreground child and detached/background actor; stored credentials and outside-project writes are denied. An extension running in the trusted Pi process is NOT automatically isolated.

Version policy: the existing approved candidate pins `pi-subagents@0.86.0`; observed `v0.87.0` is a **candidate upgrade**, requiring drain, strict `provider/id`, and multi-session regression proofs before changing the pin. The other four package versions remain the current source manifest. No Pi/npm package installation happens through this skill.

## Evidence

Use the existing `VerificationReceipt` and source revision conventions. Static PASS may coexist with runtime BLOCKED. Missing native Pi -> BLOCKED. No receipt for absent effects may be fabricated. Reuse `create-verification-skill` and `maintain-verification-skill` procedures, not another verification registry.

## Cleanup

Actual verifier child processes, outside files or worktrees are untracked by today's preflight; `cleanup` therefore reports **BLOCKED / NOT_VERIFIED** (exit 2), never unconditional PASS. A future native verifier must track spawned actor identities and remove/check their artifacts under timeout and cancellation before claiming cleanup.

## Helpers

```sh
bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor
bash .pi/skills/verify-pi-pstack/scripts/driver.sh launch
bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive
bash .pi/skills/verify-pi-pstack/scripts/driver.sh evidence
bash .pi/skills/verify-pi-pstack/scripts/driver.sh cleanup
```

`launch`, `drive` and `cleanup` are *not* evidence of native child conformance while the actor driver remains unimplemented.
