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
