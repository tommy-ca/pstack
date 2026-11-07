# Feature: minimal Pi package integration and honest security boundaries

## Owner map
| Operation | Required owner | Status in this repository |
| --- | --- | --- |
| Pi native tools/MCP/models/sessions | Pi v1.5.0 | documented; package runtime NOT_RUN |
| Canonical PStack skills/playbook semantics | `skills/` + `poteto-mode` | checkout-discovered, source-level |
| Named role templates | `agents/` via pi-subagents `agentScanDirs` | project settings source only |
| Child spawn/join/cancel/mission | pi-subagents@0.86.0 | static-only, v0.87.0 proposed candidate |
| OS main/subagent/background sandbox | pi-better-sandbox@0.14.1 | requires enabled/observed policy, NOT_RUN |
| Pre-tool-call adjudication | pi-verdict@0.16.0 | classifier `allow` not hard human.gate |
| Structured human input | pi-ask-user@0.17.2 | `human.ask` only |
| Web access | pi-web-access@0.47.0 | optional research profile |
| Repo-local PStack tests | existing two Pi verify skills | bounded source PASS possible |
| Pi package `package.json#pi.skills` | proposal #975 | NOT_YET_SHIPPED |

## Essential list
Four engineering extension owners, plus one optional research extension. `@zenspc/pi-pstack` transitional only; never use alongside a duplicate PStack skills router. Do not add second scheduler, subagent engine, permission-modes owner, model gateway, plan DB, or default web search.

## Feature tests (GIVEN / WHEN / THEN)
**PI-14 preflight:** GIVEN Pi binary + exact pinned packages and `--no-tools` echo returns zero, WHEN `build_scenarios` produces receipt, THEN runtime BLOCKED with no `observed_live` scenario, because no child or sandbox action occurred.

**PI-15 cleanup:** GIVEN only preflight, WHEN shell `cleanup` is called, THEN exit 2/BLOCKED and never print PASS for resource absence.

**PI-02 package:** GIVEN explicit `pi.skills` package with no bundled extension, WHEN native Pi in disposable trusted project installs and lists it, THEN skills must resolve via native Pi; agent roles must separately resolve via pi-subagents, else PACKAGE GAP.

**PI-04 provider:** GIVEN unavailable `provider/id`, WHEN v0.87.0 candidate spawns, THEN refuse the launch, not fall back to same-named alternate provider.

**PI-05 denied child:** GIVEN child launch policy deny, WHEN attempted, THEN no child process/ID appears and a reasoned BLOCKED receipt is produced.

**PI-10 OS:** GIVEN sandbox installed but disabled or trusted extension bypass possible, WHEN sensitive outside-project/credential action attempted, THEN hard OS confinement is UNVERIFIED unless native denied effect observed.

**PI-13 source mutation:** GIVEN 53 fixed invalid configurations, WHEN existing Python checker runs, THEN rejects all and calls the result source-contract PASS; never calls that full runtime formal proof.

## How to run offline
```sh
bash .pi/skills/verify-pi-pstack/scripts/driver.sh doctor
python3 -m pytest -q tests/test_pi_candidate_profile.py tests/test_pi_authorization_contracts.py
```

Use `launch` and `drive` only for preflight (runtime remains BLOCKED). Use `cleanup` only to report absence of proof (BLOCKED until a tracked actor driver exists). Keep actual runtime, package and independent reviewer statuses separately in the existing PStack receipt model.

## Sources
[Official Pi v1.5.0](https://github.com/earendil-works/pi/releases/tag/v1.5.0), [Pi native packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md), [Pi extensions trust](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md), [pi-subagents v0.87.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0), [PStack candidate pin manifest](../../../../references/pi-essential-extensions.json). Source citations do not imply those packages are installed.
