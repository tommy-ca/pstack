# Pi extension package: reconcile opt-in distribution and verification evidence

## Motivation
The already-merged Pi candidate epic [#894](https://github.com/tommy-ca/pstack/issues/894) added a 17-binding `pstack:pi` profile, a 4+1 source-pinned extension shortlist, a native project `.pi/settings.json`, a functional verifier, a bounded mutation verifier and Pi host reference. Its delivery was correctly classified as SOURCE/STATIC. It did not add an installable Pi package or observe effective child/tool/sandbox security.

A deep audit on 2026-11-07 found a P0 proof defect: `scripts/prove_pi_vertical_slice.py` can label runtime PASS after Pi/package version detection and `pi -p --no-session --no-tools`. A no-tools echo establishes **no** child/permission/OS confinement. `.pi/skills/verify-pi-pstack/scripts/driver.sh cleanup` likewise claims PASS for no leaked resources without tracking any native actors. The two existing verification skills can fix and document this without another verification framework.

## Goal and owner split
- Official Cursor PStack semantics at the applied local `UPSTREAM` pin are authoritative. This repo's Pi adaptation is a thin optional **skill/package projection**, not an orchestration runtime, provider layer or copied PStack fork.
- Pi core owns its native model catalog, sessions, skills, tools and MCP. Pi-subagents owns delegation/worktree/schedules (not PStack). Pi-better-sandbox owns optional OS confinement. Pi-verdict is advisory/deterministic *tool-call adjudication* only, not an independently enforced human.gate or trusted extension confinement. Pi-ask-user owns structured human.ask. Pi-web-access is a research-only opt-in.
- Existing `references/pi-essential-extensions.json` remains a reviewed **reference manifest**, NOT a native Pi package install/config enforcement. No third-party extensions auto-install or become trusted solely by inclusion.
- Investigate a **thin native Pi package.json** with `pi.skills` referencing canonical PStack `./skills`; declare *no bundled executable extensions*. Candidate project `.pi/settings.json` can still opt into `../agents` through pi-subagents, but a package `pi.skills` declaration alone does not install subagent role definitions or prove native role dispatch.
- Keep `pstack:pi` **candidate**, 17 static-only bindings, `human.gate` GAP, and no automatic seventh host enrollment.

## Minimal extension set and release drift
| Source-pinned candidate | Existing pin | Owner | Decision |
| --- | --- | --- | --- |
| [Pi v1.5.0](https://github.com/earendil-works/pi/releases/tag/v1.5.0) | 1.5.0 | host core | keep until native proof |
| [pi-subagents v0.86.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.86.0) | 0.86.0 | delegate/mission | retain pin for now |
| [pi-subagents v0.87.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0) | candidate (2026-11-07) | same engine, updated drain/provider/multi-session semantics | evaluate separately before pin change |
| [pi-better-sandbox](https://pi.dev/packages/pi-better-sandbox) | 0.14.1 | OS tool confinement | enabled effective actor policy must be proven |
| [pi-verdict v0.16.0](https://github.com/jesset/pi-verdict/releases/tag/v0.16.0) | 0.16.0 | tool_call classification/denies | not hard human.gate |
| [pi-ask-user](https://pi.dev/packages/pi-ask-user) | 0.17.2 | structured human.ask | not action authorization |
| [pi-web-access](https://pi.dev/packages/pi-web-access) | 0.47.0 | research-only | disabled for minimal coding profile |
| @zenspc/pi-pstack 0.6.0 | transitional | old PStack policy | remove after canonical native skills discovery; never duplicate |

Pi `v1.5.0` is the latest official release observed as of this audit. Pi-subagents `v0.87.0` was published **2026-11-07 07:34Z**, after the earlier source freeze, and fixes strict provider-qualified model selection plus drain and session-isolation behavior. Neither publication nor package presence proves installed capability or permission safety.

## Changes in this PR
- Fix the false runtime PASS and unconditional cleanup assertion.
- Update existing `.pi/skills/verify-pi-pstack` and `.pi/skills/verify-pi-pstack-formal` skills with accurate proof tiers and an explicit feature map, plus regression tests.
- Update existing `skills/poteto-mode/references/pi-tools.md` only for candidate Pi contract wording.
- Extend `pstack-portability` in a **single follow-on OpenSpec change** with modified existing verification and package requirements, minimal extension ownership and GWT falsifiers.
- Reconcile new follow-on epic #973 with previous **closed** #894, #895–#900, #902 and merged PRs #901/#903. Do not reopen completed source-only work.

## Non-goals
No runtime scheduler, multi-agent controller, work queue, separate model registry, new permission server, bundled unreviewed pi extension, automatic global Pi installation, promotion to `BUILTIN_HOSTS`, changes to other six shipped adapters, Pi-derived PStack semantic authority, QStack reverse dependency, or claims of actual Swarm/Arena/Interrogate/Thermos runs not executed.

## Verification tier
The new tests only prove **false-PASS rejection and static contracts**. Exact-head CI required. Standalone OpenSpec validation, real Pi package install, denied/allowed native child and OS sandbox tests, and independent review remain separate recorded gates. No installed Pi access in this GitHub-only specification work.
