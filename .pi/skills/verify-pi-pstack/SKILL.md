---
name: verify-pi-pstack
description: "Verify standalone Pi candidate skills, 17 PStack capability bindings, and essential extension guardrails. Source checks are not native runtime proof."
disable-model-invocation: true
---

# Verify Pi PStack candidate

Project-local Pi verification skill. The six-host verifier remains canonical; this does not enroll a seventh shipped host.

## Launch

Run `bash .pi/skills/verify-pi-pstack/scripts/driver.sh launch` to probe the installed Pi binary. A missing binary is BLOCKED; an available binary is still UNTESTED until native child and permission behavior are observed.

## Doctor

Run `bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor` to validate the typed profile, source-locked extension list and 53 failing mutation cases. This is source-level proof, not a successful runtime Pi deployment.

## Drive

Run `bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive`. Until the Pi actor driver and receipts are implemented in #897, the command **fails closed with exit 2**. Never promote an offline result into observed_live.

## Proof bar

Require a pinned Pi binary, package and model catalog, distinct child identities and terminal states; test pi-verdict rule denies vs model allows, classifier failure, headless ask, gate disablement, custom/MCP tool bypasses, denied `subagent_launch`, cancellation, workspace isolation/cleanup, sandbox enforcement for parent/child/detached tasks, and credential/outside-repository denial. An `ask_user` answer is not a hard authorization gate. Apply FAIL > BLOCKED > UNTESTED > PASS.

## Evidence

The source-only driver emits no live Pi receipt. Native evidence must capture source SHA, adapter revision, extension versions, real model identities, subprocess exits, worktree effects and independent negative-control denials. Do not reuse OMP RPC receipts.

## Cleanup

The candidate offline driver creates no long-lived process, session or worktree. A future native driver must clean up under timeout and cancellation and prove no residue.

## Helpers

Commands:
- `bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor`
- `bash .pi/skills/verify-pi-pstack/scripts/driver.sh launch`
- `bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive`
- `bash .pi/skills/verify-pi-pstack/scripts/driver.sh cleanup`
