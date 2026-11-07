# System design: minimal Pi extension package and truthful PStack verification

## Source architecture

~~~text
Canonical Cursor PStack semantics (applied UPSTREAM pin)
           |
    PStack skills/ + agents/ + typed PStack role policy
           |
           +---- repo checkout (.pi/settings.json loads ../skills, ../agents)
           |
           +---- proposed opt-in Pi package.json
                    |    pi.skills: ["./skills"]          -> native Pi skill loader
                    |    pi.subagents.agents: ["./agents"] -> pi-subagents role lookup
                    |    pi.extensions: absent            -> no bundled runtime/permission code
                    |
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

**Minimal proposed Pi native package manifest** (illustrative, NOT created or installed by this PR; tested source syntax, not live loader behavior):
~~~json
{
  "name": "pstack",
  "version": "0.15.29-preview.0",
  "private": true,
  "keywords": ["pi-package"],
  "pi": {
    "skills": ["./skills"],
    "subagents": {
      "agents": ["./agents"]
    }
  }
}
~~~
This **native package projection is derived** from the existing typed `pstack.package.json` (`id`, `version`, `skills_root`, 22 `roles[].id`), not a second hand-maintained version or role catalog. Pi v1.5.0 documents `pi.skills`; pi-subagents **v0.86.0** documents `pi.subagents.agents` (both source-pinned). Pi will not install the third-party delegate extension for this package. Omit `pi.extensions` and third-party runtime dependencies, and exclude repository-only `.pi/skills/verify-pi-pstack` from consumers. No generated or user-global file is changed by this OpenSpec.

**Native installation gate:** test `pi install git:github.com/tommy-ca/pstack@<immutable-sha>` or local package in a *disposable* Pi home/project, only after the tested metadata exists. Confirm `pi list` plus native `/skill:poteto-mode`, `/skill:swarm`, `/skill:arena`, `/skill:interrogate`, and **all 22** role definitions via the installed `pi.subagents.agents` root. A loaded skill is not a successful role launch. Test project trust rejection, package removal, stale versions and collisions from `@zenspc/pi-pstack` without modifying the user's unmanaged packages. Existing checkout `agentScanDirs:["../agents"]` is a separate discovery path and must not be conflated with packaged agent roots.

## Existing data and code boundaries
| Atom | Owner | Contract |
| --- | --- | --- |
| Native Pi version/session/tools | installed Pi v1.5.0 | source pin and runtime observation separate |
| Candidate host identity | `scripts/host_identity.py` + `HarnessProfile` | `pstack:pi` path-safe `pstack-pi.json`, not OMP |
| 17 capabilities | existing `Binding` schema | statuses static-only until observed receipts |
| Extension shortlist | `references/pi-essential-extensions.json` | 4 engineering + 1 optional research; **not** package manager config |
| Package resources | future Pi `package.json#pi` | `skills:["./skills"]` only; zero executable extensions |
| Role discovery | `.pi/settings.json` checkout OR future `pi.subagents.agents` package manifest | canonical `agents/` 22 definitions; must prove discovery, model/thinking mapping and role tool ceilings |
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

## Extension profile and role-effect contracts

The **existing pinned source manifest** (`references/pi-essential-extensions.json`) lists four engineering extensions plus one optional research provider. It is not a native installer or a minimal operational dependency manifest. Source-backed capability tiers, not a new runtime configuration authority:

| Profile | Additional installed extension requirements | Capabilities | Must still remain unverified |
| --- | --- | --- | --- |
| Sequential | none | PStack native skill routing on Pi, local read/edit/bash | child execution, human.gate |
| Delegated core | pi-subagents@0.86.0 | child spawn/join; worktree/scheduling where separately configured | OS sandbox, privileged effect authorization |
| Interactive | delegated core + pi-ask-user@0.17.2 | structured human.ask | authenticated human.gate |
| Guarded | interactive + pi-verdict@0.16.0 + pi-better-sandbox@0.14.1 | discretionary tool adjudication and OS confinement **only when actually enabled and tested** | trusted Pi-process extension bypass; independent mandatory human.gate |
| Research | guarded + pi-web-access@0.47.0 | scoped source-backed web lookup | ambient child web/MCP exposure without policy |

A role with generic `effort: xhigh` is not known to get Pi's `thinking: xhigh`; a read-only instruction without `tools:` can leave default `bash/edit/write` available. The 22 PStack role files are the single semantic source, but Pi behavior must be normalized **at the host adapter layer** through reviewed `agentOverrides`, strict `tools` allowlists and `inheritSkills`/context choices, not silently copied or assumed. At minimum, independently verify `arena-cross-judge-pool`, `interrogate-reviewers`, `independent-verifier` and `swarm-workers` with actual provider-qualified model IDs, effective tools, skills and workspace rights. Tests require a denied write and child recursion attempt for a readonly verifier, and demonstrated loaded PStack principles for a real child.

**Typed data-flow mapping:** reuse existing `pstack.package.json#roles`, `schemas/portability/package-descriptor.schema.json`, `HarnessProfile`, `Binding`, and `VerificationReceipt`. A native Pi package projection only serializes `{name,version,pi:{skills,subagents:{agents}}}`. A Pi runtime proof receipt must bind `source_sha`, `installed_packages[]`, `role_name`, `resolved_provider_model`, `effective_tools[]`, `child_id`, `terminal_state`, `observed_effects[]` and `evidence_level` into existing receipt/evidence metadata or artifacts, not mint a second registry or reinterpret static evidence. The package projection itself only establishes *declared* resources; installed role resolution and effect authorization are distinct checks.

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
