# Source-pinned Pi package/extension matrix (2026-11-07)

This matrix reconciles **published upstream versions**, PStack's existing **static candidate pins**, and **unobserved local installation**. It does not alter current user Pi settings or silently promote `pstack:pi`.

| Component | Existing pin | Latest source observation | Status/decision |
| --- | --- | --- | --- |
| Pi CLI | 1.5.0 | [official release v1.5.0 2026-11-02](https://github.com/earendil-works/pi/releases/tag/v1.5.0) | pin retained; installed version NOT_RUN |
| pi-subagents | 0.86.0 | [v0.87.0 2026-11-07 07:34Z](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0) | upgrade candidate, NOT applied |
| pi-better-sandbox | 0.14.1 | [published package](https://pi.dev/packages/pi-better-sandbox) | current source pin, effective OS mode NOT_RUN |
| pi-verdict | 0.16.0 | [release v0.16.0 security fixes](https://github.com/jesset/pi-verdict/releases/tag/v0.16.0) | tool_call owner only; mandatory human.gate GAP |
| pi-ask-user | 0.17.2 | [published package](https://pi.dev/packages/pi-ask-user) | structured human.ask; not authorization |
| pi-web-access | 0.47.0 | [published package](https://pi.dev/packages/pi-web-access) | optional research profile, no base install |
| @zenspc/pi-pstack | 0.6.0 | existing transitional inventory | collision risk; remove only after native discovery proof |

## Source of actual Pi package semantics
Official [Pi package documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md): explicit `package.json#pi` supports `skills`, `extensions`, `prompts`, `themes`; `pi install git:...` installs a package (project-local with `-l`) and `pi list` enumerates declared packages. A package install or name listing does **not** prove activated extension hooks or role discovery. Pi [extension documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) states extensions execute inside Pi with process-level OS permissions and can inspect credentials, prompts and tools. Threat-model all installed packages.

## Essential composition and exclusions
**Minimal coding**: pi-subagents + pi-better-sandbox + pi-verdict + pi-ask-user. Research profile additionally opts into pi-web-access. Runtime host already has read/edit/write/bash, sessions, MCP and model selection. The extension roles do not license the PStack project to own an executor or scheduler. PStack `references/pi-essential-extensions.json` is the candidate's pinned **policy document**, not a native `package.json`; avoid name confusion.

Do not install the overlapping engines listed in `references/pi-essential-extensions.json#conflicts`. Do not keep @zenspc/pi-pstack as a concurrent policy router after native skill discovery works. No global installs or edits to ~/.pi/agent done in this PR.

## Candidate v0.87.0 semantic test cases
- Strict `provider/id` launch: unavailable provider fails, never uses cross-provider match.
- `stop` with `drain:true`: no new child starts; running children finish and preserve receipts.
- Two sessions/windows: wait notice and running child ownership are session-correct.
- MCP selectors, version dependencies: missing capability errors before child acceptance; no false authorized launch.
- Background and worktree cleanup: no abandoned artifacts; do not assume release notes prove this.

## Version mismatch classification
If actual `pi list` reports 0.87.0 while the current manifest pins 0.86.0, the current verifier SHOULD report VERSION_MISMATCH/BLOCKED and request a compatibility audit; it MUST NOT silently allow or auto-downgrade. Future source pin upgrade should change `references/pi-essential-extensions.json`, profile tool-mapping strings, Pi tools reference, negative tests and proof receipts in one bounded reviewed PR. Source release timestamps are not native evidence.

## Package trust/installation split
`skills/poteto-mode/references/pi-tools.md` and `.pi/settings.json` currently describe *repository-local* trust and resources. An installable, portable `package.json#pi.skills` is a proposed separate deliverable (#975). Verify actual native install role discovery and package resource collision before releasing it. Current PStack has no executable Pi extension to publish.

## Boundary from QStack
QStack consumes `poteto-mode` and supplies quant-only semantics. It cannot register Pi tools or substitute PStack's host authority. PStack remains fully operational without QStack; use QStack's test-falsifier discipline as a review method only.


## Upstream principle and playbook crosswalk

PStack's applied `UPSTREAM` source is the immutable official [Cursor pstack@88d47514](https://github.com/cursor/plugins/tree/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack) (verified in this repository's `UPSTREAM` file). Its skill/playbook **intent** is canonical; Pi and third-party extension API examples are local implementation bindings, not new PStack principles.

| Applied canonical principle / method | Specific Pi decision it changes |
| --- | --- |
| [Subtract Before You Add](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-subtract-before-you-add/SKILL.md) | No new PStack scheduler, model catalog or Pi-native executor wrapper; use Pi+one delegate owner |
| [Boundary Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-boundary-discipline/SKILL.md) | Keep explicit separation among candidate profile contract, actual installed extensions and observable child/OS effects |
| [Type System Discipline](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-type-system-discipline/SKILL.md) | Reuse existing 17 `Binding` rows and `VerificationReceipt`; no duplicate Pi extension capability data model |
| [Migrate Callers Then Delete Legacy APIs](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Retire transitional `@zenspc/pi-pstack` policy *only after* native PStack skills and agent templates are proven discoverable |
| [Make Operations Idempotent](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-make-operations-idempotent/SKILL.md) | Future Pi package installation/rollback uses disposable roots and confirms exact effect/cleanup state |
| [Prove It Works](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/principle-prove-it-works/SKILL.md) | P0 fix: a zero-exit `--no-tools` process check can never prove child authorization or hard sandbox |

Canonical `/swarm`, `/arena` and `/interrogate` are **review compositions using independently verified host primitives**, not Pi extension packages. The source-bearing official [swarm](https://github.com/cursor/plugins/tree/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/swarm), [arena](https://github.com/cursor/plugins/tree/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/arena) and [interrogate](https://github.com/cursor/plugins/tree/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/interrogate) specify framing, independent model/child lanes, synthesis and verification; Pi must substantiate actual model and child IDs before reporting them as EXECUTED. [Thermo Nuclear Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-review) audits changed-diff correctness and security; [Thermo Nuclear Code Quality Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-code-quality-review) challenges duplicate adapters, giant files and uncontrolled conditionals. These are **review lenses**, not source evidence that a reviewer ran. All independent panels remain NOT_RUN here.

[QStack's compose-with-poteto](https://github.com/tommy-ca/qstack/blob/main/skills/qstack-mode/guides/compose-with-poteto.md) confirms one-way downstream `qstack-mode -> poteto-mode`. QStack's quant-domain falsification and runtime gates can *consume* a tested Pi-PStack host binding, but PStack cannot import QStack, duplicate its quant task graph or become its orchestration runtime.

## Source correction: minimum Pi package and native agent registration (2026-11-07)

The candidate's `engineering[4]` records a reviewed **guarded interactive profile**, not four necessarily essential packages. The minimum is **zero** for sequential PStack skills on Pi native, or **one (`pi-subagents@0.86.0`)** for actual Swarm/Arena/Interrogate delegation. Optional `pi-ask-user` adds structured human.ask; optional `pi-verdict` plus `pi-better-sandbox` add separately configured and verified tool/OS controls (still no standalone hard human.gate); `pi-web-access` is research-only. Do not change current source manifest pins without compatibility work.

**Native package integration:** [pi-subagents v0.86.0 docs/agents.md](https://github.com/nicobailon/pi-subagents/blob/v0.86.0/docs/agents.md) documents package-level `pi.subagents.agents: ["./agents"]`; [Pi v1.5.0 docs/packages.md](https://github.com/earendil-works/pi/blob/v1.5.0/packages/coding-agent/docs/packages.md) documents `pi.skills: ["./skills"]`. Derive a single source-backed manifest from PStack's 22 registered roles; do not duplicate the agent files or add an executable Pi extension to export them. The actual installed Pi package/role lookup is **NOT_RUN**, not PROVEN.

**False-semantic-parity negative control:** [pi-subagents v0.86.0 agent reference](https://github.com/nicobailon/pi-subagents/blob/v0.86.0/docs/agents.md#frontmatter-reference) names `thinking`, `tools`, `inheritSkills`, `systemPromptMode`; canonical [PStack independent-verifier role](https://github.com/tommy-ca/pstack/blob/main/agents/independent-verifier.md) uses `effort` and natural-language no-edit instructions but lacks a strict `tools` allowlist. Pi's default built-in tools include `bash/edit/write` ([Pi v1.5.0 settings docs](https://github.com/earendil-works/pi/blob/v1.5.0/packages/coding-agent/docs/settings.md)). Those foreign fields and prompts MUST NOT be equated to Pi-native tool restrictions; an actual Pi child role projection or host settings override may be required. Fresh children do not implicitly inherit all Pi project/skill context. Keep claimed role-thinking, independent model identities and hard readonly as unverified until observed.

**No new engine:** Pi native `package.json#pi.subagents.agents` is the role discovery API in the *one* existing chosen extension; PStack adds data projection, not a dedicated Pi runtime, scheduler, model router or package registry.
