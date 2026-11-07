# System design: minimal Pi extension package and truthful PStack verification

## Source architecture

~~~text
Canonical Cursor PStack semantics (applied UPSTREAM pin)
           |
    PStack skills/ + agents/ + typed PStack role policy
           |
           +---- repo checkout (.pi/settings.json loads ../skills, ../agents)
           |
           +---- proposed opt-in Pi package.json#pi.skills: ["./skills"]
                    |
                    +--> Pi core skill loader (proposed package discovery proof)
                    +--> Pi native read/write/edit/bash/MCP/session/model
                               |
                               +-- pi-subagents@0.86.0 delegate/worktree/mission (v0.87 candidate)
                               +-- pi-better-sandbox@0.14.1 OS policy [must be enabled/tested]
                               +-- pi-verdict@0.16.0 tool_call decisions [not human.gate]
                               +-- pi-ask-user@0.17.2 structured human.ask
                               +-- pi-web-access@0.47.0 research-only opt-in
                               |
                        Existing PStack VerificationReceipt
                        source tests / package preflight / observed native proof

No PStack agent runtime, scheduler, model router, QStack import or generic extension SDK
~~~

## Actual versus proposed package contracts

**Currently shipped checkout:**
- `.pi/settings.json` loads `skills: ["../skills"]`, `subagents.agentScanDirs:["../agents"]`, and `projectRootResolution:"git-root"`. Those paths resolve from trusted project settings; this is not a globally installed Pi package.
- `references/pi-essential-extensions.json` is a source-only list checked by `scripts/verify_pi_candidate.py`. It is NOT consumed by Pi. `pi list` shows installed packages, not whether package tools are active, their permission hooks enabled, or the sandbox actually enforcing OS rules.
- `skills/setup-pstack/profiles/pstack-pi.json` remains `candidate`, with exactly 17 typed static-only bindings; `human.gate` is a GAP.

**Minimal proposed Pi native package manifest** (illustrative, NOT created or installed by this PR):
~~~json
{
  "name": "pstack-pi-skills",
  "version": "0.15.29-preview.0",
  "private": true,
  "keywords": ["pi-package"],
  "pi": {
    "skills": ["./skills"]
  }
}
~~~
Use the released PStack version from `pstack.package.json` when eventually generating metadata; the example is not another version registry. Explicitly omit `pi.extensions`: PStack has no owned executable Pi extension. Do not include `.pi/skills/verify-pi-pstack` in consumer package automatically: those are repository-local verification skills invoking repository scripts, not general-purpose end-user tools.

**Native installation gate:** test `pi install git:github.com/tommy-ca/pstack@<immutable-sha>` or a local package in a *disposable* Pi home and project. Confirm `pi list`, native `/skill:poteto-mode`, `/skill:swarm`, `/skill:arena`, `/skill:interrogate`, and actual role lookup under pi-subagents. Explicit `pi.skills` loading is NOT `agentScanDirs` equivalence; absence is a package-level GAP. Detect collisions from `@zenspc/pi-pstack` without silently disabling user packages.

## Existing data and code boundaries
| Atom | Owner | Contract |
| --- | --- | --- |
| Native Pi version/session/tools | installed Pi v1.5.0 | source pin and runtime observation separate |
| Candidate host identity | `scripts/host_identity.py` + `HarnessProfile` | `pstack:pi` path-safe `pstack-pi.json`, not OMP |
| 17 capabilities | existing `Binding` schema | statuses static-only until observed receipts |
| Extension shortlist | `references/pi-essential-extensions.json` | 4 engineering + 1 optional research; **not** package manager config |
| Package resources | future Pi `package.json#pi` | `skills:["./skills"]` only; zero executable extensions |
| Project-local role discovery | `.pi/settings.json` | `../agents` via pi-subagents only with project trust |
| Tool risk adjudication | pi-verdict (external) | `allow/ask/deny` not an independent hard operator gate |
| OS confinement | pi-better-sandbox (external) | effective enabled Main/Subagents/Background OS backend proof |
| Authorization for effects | independent host enforcement | Pi `human.gate` GAP until observed |
| Source verification | `scripts/verify_pi_candidate.py` | exact 53 bounded mutation tests, not checker proof |
| Runtime preflight | `scripts/prove_pi_vertical_slice.py` | version/packages/no-tools echo, remains BLOCKED |
| Native proof later | issue #976/#977 | real child/action effects and source-linked traces, no duplicate controller |
| Four-plane evidence | existing `VerificationReceipt` | no `observed_live` derived from preflight |

## P0 code and evidence flow

~~~text
offline_slice()
  -> check_contract(candidate profile, extension manifest, project settings)
  -> check_verdict_template()
  -> bounded_negative_controls() [53 static source mutants]
  -> source/adapter/package may be PASS (offline only)
live_slice() [optional]
  -> pi --version / pi list
  -> pi -p --no-session --no-tools echo HELLO
  -> reports versions, missing/conflicts, process result
build_scenarios()
  -> runtime = BLOCKED despite healthy preflight
  -> NO observed_live child authorization/sandbox evidence
build_receipt()
  -> four planes; runtime BLOCKED; exact head, host_version "unobserved" if missing
  -> overall BLOCKED
~~~

**Future work**, not delivered here: real child driver explicitly invokes selected `subagent_launch` with installed policy and source authorization, captures child ID/model/provider/terminal state, observes denied launch as no child, tests main/child/detached OS sandbox, confirms resource cleanup and binds actual source SHA and installed extension hashes. Only then may a runtime scenario qualify for `observed_live` and PASS. Actual package and native actor execution must remain independently gated.

## Security boundary
Pi extensions execute inside the Pi process with the process's OS permissions. They may inspect files, credentials, prompts and tool arguments, so a loaded third-party extension is a trust decision. A tool_call hook cannot stop all privileged effects from another trusted extension if the process shares OS privileges; do not infer unbypassable gate. Require explicit `pi-verdict` activation and independent enforcement for privileged actions, plus sandbox effective mode and denied credential/outside-project paths. On `pi -p`, an ambiguous human ask is a DENY/BLOCKED, not a silent allow.

## Pi-subagents v0.87.0 candidate release semantic delta
The observed [2026-11-07 release](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0) adds: drain-aware stop preserving running children while forbidding new dispatch; strict `provider/id` resolution instead of provider substitution; improved multi-window wait routing, session isolation, MCP selectors, artifact cleanup and missing dependency error. Before upgrading from 0.86.0 test:
- `stop(drain:true)` creates no new child; running children settle and retain results; post-drain state not represented as ordinary PASS if operation was stopped.
- Unknown/unavailable `provider/id` errors, never borrows a same-named other-provider model; model-family independence requires observed model+provider for each lane.
- Two concurrent windows/sessions preserve ownership of notices/children; prior completed runs cannot be resumed as new accepted work.
- Native MCP selector/directTools mappings, controlled role/AGENTS context inheritance and package-dependency error fail closed.
No automatic upgrade, only source candidate until installed-version and behavior evidence.

## Verification recipe and data flow
The Pi skill `.pi/skills/verify-pi-pstack` is the existing user-facing evidence helper, with a feature map. `doctor` runs static checks only; `launch`/`drive` run preflight and block; `cleanup` blocks without an actor registry. `.pi/skills/verify-pi-pstack-formal` maintains 53 source mutations; future true formal checking requires bound, implementation relation, checker/tool digest, bad-variant counterexample, and explicit proof status. Reuse PStack's creators/maintainers, never a second verification scheme.

## Rollback and ownership
This small change updates no user or global Pi extension installations. Failed or cancelled native tests must not leave a PStack-owned extension service; any future temporary Pi home/worktree must be tracked, confined and removed with checked evidence. QStack remains a downstream consumer (`qstack-mode -> poteto-mode`), never a dependency or new generic host authority.
