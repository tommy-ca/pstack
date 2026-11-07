# Feature: minimal Pi extension package and truthful security boundaries

## Sub-features

| Capability | Owner | Current support |
| --- | --- | --- |
| Native tools/MCP/models/sessions | Pi v1.5.0 | source-documented |
| PStack canonical engineering semantics | `skills/` and `poteto-mode` | project-discovered |
| Named role templates | `agents/` via checkout `agentScanDirs` or packaged `pi.subagents.agents` | package API source-backed; native install NOT_RUN |
| Child spawn/join/cancel/schedule | pi-subagents@0.86.0 | static-only; v0.87.0 unverified |
| OS sandbox | pi-better-sandbox@0.14.1 | effective enabled mode NOT_RUN |
| Pre-tool-call adjudication | pi-verdict@0.16.0 | not mandatory human.gate |
| Structured human.ask | pi-ask-user@0.17.2 | selection, not authorization |
| Web access | pi-web-access@0.47.0 | optional research-only |
| Native Pi package `pi.skills` | proposed #975 | NOT_SHIPPED |

**Capability-minimal core:** zero third-party extensions for single-agent Pi PStack; **only pi-subagents@0.86.0 is essential for delegated Swarm/Arena/Interrogate**. The existing 4-engineering source list describes a *guarded interactive candidate*, not mandatory dependencies of every PStack skill: pi-ask-user supports optional structured questions, while pi-verdict+pi-better-sandbox provide optional separately configured policy and confinement (neither alone proves mandatory human.gate). pi-web-access remains research-only. `@zenspc/pi-pstack` is transitional, not a second PStack policy source. No second delegation engine, scheduler, permission-modes owner or model gateway.

## How to get to it (user POV)

Use an already trusted PStack checkout to run Pi with project settings; no third-party packages are installed by these verification skills. A future thin Pi native skills package must separately prove actual `pi install`, `pi list`, native skill discovery and role-template resolution in a disposable project before it can be recommended for distribution.

## Driving it with Pi

**PI-14 preflight:** GIVEN Pi binary + pinned packages + zero-exit `--no-tools` echo, WHEN `build_scenarios` reduces receipt, THEN runtime BLOCKED and no `observed_live` child or sandbox scenario.

**PI-15 cleanup:** GIVEN only preflight with no child/artifact ledger, WHEN `driver.sh cleanup` runs, THEN exit 2/BLOCKED, never PASS.

**PI-02 package:** GIVEN a proposed native Pi `pi.skills:["./skills"]` + `pi.subagents.agents:["./agents"]` manifest, WHEN installed into a disposable project with separately installed pi-subagents, THEN `/skill:poteto-mode` plus **all 22** canonical role identities MUST resolve without copying them, or PACKAGE GAP.

**PI-20 role effort:** GIVEN `effort:xhigh` on a PStack role, WHEN Pi loads it, THEN do not claim native `thinking:xhigh` without observed mapping/override.

**PI-21 hard readonly:** GIVEN `independent-verifier` says "do not edit" but does not declare `tools`, WHEN launched under Pi, THEN hard readonly is NOT_VERIFIED until an explicit native allowlist + OS-denied write/bash/child-spawn effects are proven.

**PI-22 skills inheritance:** GIVEN a Pi child that should follow PStack principles, WHEN spawned fresh, THEN verify `inheritSkills` or explicit native skill selection; do not claim skill context from the role prompt alone.

**PI-04 provider:** GIVEN unavailable `provider/id`, WHEN upgraded pi-subagents candidate is run, THEN native launch MUST refuse, not silently switch to another provider.

**PI-05 denied child:** GIVEN a denied `subagent_launch`, WHEN requested, THEN no child starts and BLOCKED reason is recorded.

**PI-10 sandbox:** GIVEN installed-but-disabled sandbox or trusted-tool bypass, WHEN denied credential/outside-project effect attempted, THEN hard confinement remains UNVERIFIED until native denial is observed.

**PI-13 source mutations:** GIVEN 53 invalid source configurations, WHEN existing `model` checker runs, THEN all are rejected and marked bounded contract PASS only; not native formal proof.

Commands:
```sh
bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor
python3 -m pytest -q tests/test_pi_candidate_profile.py tests/test_pi_authorization_contracts.py
```

## Gotchas

A package list does not prove loaded hooks or enabled sandbox. Pi extensions execute in the trusted Pi process with its OS permissions. A classifier `allow` or `ask_user` answer cannot authorize mandatory human.gate. PStack's reference manifest is not consumed by Pi. Keep pi-subagents 0.86.0 as the pin until [v0.87.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0) receives source/install/runtime compatibility evidence. No native actor, model-checker or independent reviewer has been run by this source-only PR. See the [source manifest](../../../../references/pi-essential-extensions.json) and [official Pi package docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md).
