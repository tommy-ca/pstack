# Standalone Pi 1.5.0 → PStack: source-grounded candidate audit

Status: **DESIGN / STATIC-ONLY**, not a packaged seventh host or a live conformance receipt. Audit date: 2026-11-05. Owner: #894; tasks #895–#900.

## Source pins and authority

- PStack target snapshot: tommy-ca/pstack main at 61fea890441f17675459386bf6fef2dd224e6613; its applied UPSTREAM pin is cursor/plugins@88d47514b82e7c44f00f2b2a72ff6dd12158038c, version 0.15.29. Cursor upstream 0.15.36 was evaluated in completed #840 but is **not** applied by this audit.
- Official Pi release: 1.5.0, 2026-11-02: https://pi.dev/changelog/releases/1.5.0
- Pi native tools and extensions: https://pi.dev/docs/latest/cli and https://pi.dev/docs/latest/extensions
- Pi MCP / codemode: https://pi.dev/docs/latest/mcp and https://pi.dev/docs/latest/codemode
- pi-subagents 0.85.0 (2026-11-05): https://pi.dev/packages/pi-subagents
- pi-better-sandbox 0.14.1 (2026-11-04): https://pi.dev/packages/pi-better-sandbox
- pi-ask-user 0.17.2 (2026-11-01): https://pi.dev/packages/pi-ask-user
- pi-web-access 0.47.0 (2026-11-05): https://pi.dev/packages/pi-web-access
- pi-subagents v0.85.0 exact release notes: https://github.com/nicobailon/pi-subagents/releases/tag/v0.85.0
- Installed user inventory supplied in conversation lists 17 packages (versions fixed by that inventory). **No local Pi binary, installed copy, extension source checkout, or child agent was executed in this audit.** Versions in the published package catalog are independent of the user's installed versions.

Canonical workflow/principle intent is at https://github.com/cursor/plugins/tree/main/pstack. The user's tommy-ca/pstack is a portable reference port. Cross-harness behavioral comparisons: https://github.com/openai/codex; https://code.claude.com/docs/en/overview; https://opencode.ai/docs/agents/; https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md. These are reference patterns, not code-dependencies.

## Correction to earlier blanket recommendations

Pi now ships MCP, codemode and tool_search natively. Do **not** add pi-mcp-adapter, another tool router, script-to-tools gateway, a new skill catalog, or a second role registry by default. Pi explicitly does not bundle subagents, approval popups, plan mode or a TODO system. Behavioral parity does not mean cloning every host's UI and state machine.

The prior 4-package recommendation should be interpreted as **three generic runtime capabilities plus one policy package candidate**, not four universally required packages:

1. pi-subagents: **single** child-agent engine. Prefer over dynamic-workflows when adapting current PStack; if later replaced, supply a host-specific adapter and repeat proof gates. Version/agent transport and cancellation are host/package-owned.
2. pi-better-sandbox: candidate parent/child/background restrictions. All fresh sandbox columns default **OFF**; a package installation is not hard enforcement. Its trusted extension tools run outside guarded file rules; OS kernel backing differs by platform. Native Pi extensions are trusted code and local confinement does not govern remote SSH effects.
3. pi-ask-user: structured `human.ask` in interactive sessions, enabled when genuine product/operator decisions require a tool-level question. This is not itself hard approval enforcement, and must be tested in non-interactive/headless mode.
4. pi-web-access: research profile only. Explicitly admit web tools in child profiles when research/auditing needs them. Never equate tool availability with network isolation.
5. @zenspc/pi-pstack: currently installed integration candidate; **not** the normative source for tommy-ca/pstack. Review licensing, supplied skills and role mapping before reusing. Prefer a projection from this repository if parity is incomplete.

Minimal **PStack interactive coding** profile: Pi core + pi-subagents + explicitly configured pi-better-sandbox + pi-ask-user (3 external runtime extensions). **Research** profile adds pi-web-access (4 extensions). Headless CI may omit pi-ask-user only if the operator gate is supplied by a proven explicit noninteractive policy that fails closed; no silent approval. PStack source projection is separate from runtime extension count. During migration @zenspc/pi-pstack is a fifth, **transitional policy package**, not an alternative orchestration engine. PStack policy can be projected as skills/agents without an extra runtime extension when host packaging supports that.

## Current 17-extension dedup inventory

| Supplied package | Proposed disposition | Semantic reason |
| --- | --- | --- |
| pi-ask-user | keep in interactive PStack profile | structured `ask_user` tool for `human.ask`; cancellation/fallback tested, does **not** alone enforce `human.gate` |
| pi-skillful | remove default | native Pi skill discovery; preserve only if ancestor lookup/visibility is a measured need |
| @zigai/pi-mention-skill | remove default | editor invocation convenience |
| @narumitw/pi-goal | task-scoped | autonomous goals; avoid competing mission state |
| @narumitw/pi-btw | remove default | Pi session branching/context |
| pi-context-usage | remove default | Pi context accounting |
| pi-simplify | absorb intent into skills | PStack quality/unslop review overlap |
| pi-web-access | keep research profile | source retrieval |
| @ff-labs/pi-fff | benchmark | optional fuzzy file ranking, native grep/find/ls baseline |
| @quintinshaw/pi-dynamic-workflows | remove default | competes with pi-subagents and PStack's delegated workflow vocabulary |
| @dietrichgebert/ponytail | absorb into PStack skills | competing quality policy |
| @narumitw/pi-lsp | project-scoped | targeted language diagnostics, prefer native compiler/lint/test as acceptance |
| pi-interactive-shell | project-scoped | PTY/process control only if required |
| pi-autoresearch | task-scoped | experimental loop, not globally required |
| pi-manage-todo-list | remove default | project tasks/issues plus text plan; no second task ledger |
| pi-memory-md | project-scoped | persistent memory only with a real need, not parallel LLMWiki state |
| @zenspc/pi-pstack | transitional evaluation | policy bundle; align to canonical PStack, avoid duplicate skill registration |

Proposed additional packages: pi-subagents (delegation) and pi-better-sandbox (candidate security controls). Keep **one** subagent engine and **one** permissions/isolation policy path.

## Seventeen PStack semantic capabilities → Pi candidate bindings

Statuses below are **source-inferred mapping candidates**, not typed profile entries or observed proof. “native” applies to standalone Pi only; “extension” names an external dependency and MUST NOT be promoted to native. “shim” means a script or workflow adaptation must be designed and driven.

| Capability | Candidate Pi primitive / owner | Candidate class | Evidence needed |
| --- | --- | --- | --- |
| agent.spawn | pi-subagents subagent | extension | real child identity, timeout, tool set |
| agent.join | pi-subagents completion / bg_wait | extension | joined exact spawned child, proof result |
| agent.message | subagent FleetView steering / intercom | extension, limited | live steering with bounded response; inspect actual wire fields |
| agent.cancel | pi-subagents stop/abort | extension | cancelled in-flight child, not completed |
| agent.resume | Pi session resume + subagent mission recovery | partial | cold child restoration separately, no inference from parent |
| workspace.shared | Pi cwd | native | same-repo observation and scope |
| workspace.isolated | subagent worktree workflow / git | extension/shim | real separate worktree, no leaked mutations |
| workspace.readonly | enabled sandbox read policy or restricted tools | conditional hard | denied edit/bash/extension bypass; no prompt-only promotion |
| human.ask | pi-ask-user `ask_user` | extension | structured selection, cancelled response, non-interactive fallback |
| human.gate | explicit operator decision + enforced permission gate | composition, unverified | `ask_user` answer is not authorization by itself; deny/allow-once and no-interactive failure must be tested |
| plan.update | repo plan/TODO.md via native write | shim | durable plan change and visible rollback |
| schedule | pi-subagents 0.85 durable `schedule.*` | extension/version-gated | one-shot/recurring fires, restoration, overlap/catch-up, pause and cancellation; no separate scheduler in PStack |
| monitor | pi-subagents FleetView/bg_wait | extension | bounded nonblocking progress and terminal state |
| session.persist | Pi session manager JSONL | native | exact session path and restart |
| session.resume | Pi session resume | native | cold restart preserving relevant context |
| evidence.capture | existing PStack receipt/CI lever | shim | command, stdout, exit, exact SHA and artifact |
| verify | existing PStack deterministic verify tools | shim | negative controls and fail-closed result |

All rows start **static-only or unverified**. Numeric concurrency limits, recursion depths and model IDs must come from the installed package/config, not generic assumptions. A worktree is not an OS security sandbox. A text plan is not a built-in task board. A separate child LLM run is not automatically an independent *model family*.

## Feature contracts from other harnesses

| Reference pattern | Reuse in Pi/PStack | Avoid |
| --- | --- | --- |
| Codex sandbox + approvals, isolated tasks, review gates | enabled/verified sandbox, dedicated read-only reviewer, explicit evidence | copying Codex process/state manager |
| Claude Code skills, hooks, subagents and permission scopes | native skills, event hooks, one subagent engine | second permission engine and hidden role forks |
| OpenCode agent roles, allow/ask/deny, MCP, LSP | typed role/tool permissions and native MCP; project-scoped LSP | declaring tool permission equal to OS isolation |
| DeepSeek Harness capability seams and durable event contracts | classify native/adapted/gap and durable evidence ownership | importing Cordis, agent-loop or runtime DB |

## Source and data flow

1. PStack canonical skill/playbook intent → frozen role IDs and acceptance predicates.
2. Host adapter resolves actual Pi version, installed extensions, model catalog and allowed tools; fails closed on absence.
3. Parent Pi session → optional pi-subagents delegate or a single direct job.
4. Sandbox admission and platform confinement happen **before** work. Parent/foreground child/detached child and trusted extension tools must be tested independently.
5. Child gets bounded brief, exact source revision, tools and permission ceiling. Worktree writers are isolated; reviewers remain nonwriting.
6. Join/cancel/monitor uses child IDs and observed terminal status; rejected/cancelled/dropout is never PASS.
7. PStack existing verification lever captures executable evidence and exact-head receipt. Existing wiki ingests source captures, not untrusted executable instructions.

## Security findings: fail-closed requirements

- pi-better-sandbox 0.14.1 starts Main, Subagents and Background tasks inactive in fresh settings. Test that profiles are enabled and persist when intended. Critically, **Subagents Stored credentials defaults to Write & delete, and Outside project to Write**, when configured without narrowing those rows; set stored credentials **Off** and outside-project **Off or Read** unless an explicitly approved task needs more. Validate actual effective policy per child.
- Trusted subagent extension tools can run outside the sandbox's guarded file rules. The package describes this explicitly; allowlists cannot be a substitute for container/VM isolation.
- Local sandbox cannot restrict remote SSH side effects; tokens inherited in environment variables and OS secret vault services require separate containment.
- On Windows the documented sandbox has no backend and confined launches fail closed. Linux requires a usable Bubblewrap setup; macOS uses Seatbelt. Test actual platform and backend.
- Check that native MCP and codemode tool calls are mediated by the intended permission hooks, and that extension-level calls do not bypass the parent policy.
- Worktree cleanup and branch conflict handling require negative testing, including interrupts and malicious symlink paths.

## Verification using existing machinery

- Tier 1 (offline): schemas, skill registration, link/index checks, branch/source pins, candidate map validation, negative test fixtures.
- Tier 2 (host smoke): installed-version command, package discovery, project trust, tool list, child model catalog, sandbox backend.
- Tier 3 (observed live): spawn/join/cancel/steer, bounded child web/MCP, independent arena model seats, isolated edit and integration, refusal/escape tests, crash recovery. Four-plane receipts pin canonical/adapter/package/runtime revisions.
- Formal: choose one high-risk invariant (e.g., no child reaches a stronger capability than its parent or no cancelled child is counted PASS), check a bounded model against code, and prove the checker fails on a deliberate mutant. A TLA+ source file by itself does not establish formal verification.

Reuse skills/create-verification-skill, skills/maintain-verification-skill, skills/create-formal-verification-skill and skills/maintain-formal-verification-skill, plus scripts/scaffold_verification_skill.py and scripts/verify_portable.py. Do **not** teach them a seventh verified host until a real Pi driver and host-native skill directory are installed and exercised.

## Review / promotion controls

- Swarm: actual independent lanes for native contracts, sandbox and trusted-tool threats, package/projection, verification and wiki.
- Arena: compare two choices using measured simplicity, cost, correctness and feature coverage. Do not auto-recommend pi-subagents over alternatives without compatibility/regression results.
- Interrogate: adversarial cases for cancellation, stale receipts, source-prompt injection, workspace escape, model identity spoofing.
- Thermo-Nuclear security/correctness and code-quality review of **the actual diff** with few high-confidence findings; no reviewer claim without a separate run transcript.
- Candidate → packaged → verified promotion requires executable native fixtures, exact-head receipts, no unresolved P0, and documented source revisions. This audit is only the first candidate specification.

Related issues: epic #894 and #895–#900; historical completed #429, #443, #259, #305, #840, #874; draft PRs #502 and #540 remain separate.

## Latest-release correction: minimal PStack extension profiles (2026-11-05)

The earlier three/four-package answers did not distinguish *human.ask* from a human approval gate, and incorrectly left durable scheduling as a generic gap. These are the source-audited, not runtime-certified, profiles:

| Profile | Native Pi | Third-party runtime extensions | PStack payload |
| --- | --- | --- | --- |
| Interactive engineering | Pi 1.5.0 | `pi-subagents@0.85.0`, `pi-better-sandbox@0.14.1`, `pi-ask-user@0.17.2` | canonical skills/roles projected from `tommy-ca/pstack` |
| Research engineering | above | add `pi-web-access@0.47.0` | researcher and evidence-auditor with explicit child tool grant |
| Headless verified CI | Pi plus one delegate and enforced isolation | `pi-ask-user` omitted **only** if a tested fail-closed policy handles blocked human decisions; research extension optional | deterministic verification scripts and receipts |
| Transitional existing setup | interactive/research profile above | temporarily keep installed `@zenspc/pi-pstack@0.6.0` until canonical projection matches | **do not load both policy copies** |

Published catalog shows `@zenspc/pi-pstack@0.6.0` (2026-09-09), while `@whamp/pi-pstack@0.11.0` (2026-10-24) is a **different independently maintained integration** using BB workers, not a drop-in update for this plan. Do not infer 0.9.0 or install both. The supplied user's Pi web access `0.26.0` and ask-user `0.14.0` are behind the published versions. Pin compatible versions after source and runtime review, not through blind global upgrades.

**0.85.0 delegation upgrade hazards:** the release adds the nested `subagent_launch` permission hook for every workflow child; permission extensions may now block a previously allowed fanout. Older background runs from before this release **cannot be resumed or auto-resumed**; relaunch using supported `reuseFrom` where appropriate. Structured output validation is stricter. Tests must cover these as security/correctness migration cases. Source: https://github.com/nicobailon/pi-subagents/releases/tag/v0.85.0 .

**Durability without a PStack scheduler:** pi-subagents documents `mission.*` state, review/acceptance receipts, one-shot and recurring `schedule.*`, and run supervision. Map PStack `schedule` and `monitor` to **extension-owned, version-gated capabilities**; verify real replay and restart before promotion. These host-owned mission records do not authorize adding a parallel PStack task database. Source: https://github.com/nicobailon/pi-subagents/blob/v0.85.0/docs/missions.md .

**Security:** a model's `ask_user` response is a decision capture, not hard permissions. A verified `human.gate` needs independent tool policy enforcement and approval provenance; in `pi -p` (noninteractive) the unsafe operation must refuse rather than auto-approve. Verify `subagent_launch` authorization, explicit sandbox switches, read-only reviewer, child credentials defaults, trusted-tool allowances, Linux/macOS backend and Windows fail-closed semantics. Running extensions are trusted process code, so use process/container confinement for untrusted repositories.

## Swarm / Arena / Interrogate: source-level decision, not executed agents

The upstream [swarm](https://github.com/cursor/plugins/tree/main/pstack/skills/swarm), [arena](https://github.com/cursor/plugins/tree/main/pstack/skills/arena) and [interrogate](https://github.com/cursor/plugins/tree/main/pstack/skills/interrogate) skills describe *execution* contracts. No actual separate-model work was run for this branch; the following is a source-derived trade study and adversarial checklist, not a multi-agent verdict.

**Swarm decomposition proposed**: (1) current Pi and extension source/version mapping, (2) sandbox + human approval + nested child threat model, (3) PStack 17-semantic profile/projection consistency, (4) verified real driver and evidence, (5) wiki provenance/digest. Independent child IDs and model families must be captured before declaring a swarm run.

**Arena alternatives for the one permission/isolation owner**:

| Candidate | Upside | Risk / evidence gap | Current decision |
| --- | --- | --- | --- |
| `pi-better-sandbox@0.14.1` | Explicit Main/Subagents/Background policies, OS-backed local containment | No demonstrated on-demand allow/ask/deny for each operation; trusted extension and unsafe child defaults | **Provisional** protected-child route; hard human.gate remains GAP |
| `pi-permission-modes@2.7.2` **instead of** pi-better-sandbox | One package combines OS sandbox + allow/ask/deny + plan/build modes; can eliminate a separate approval extension | Docs do not establish equivalent confinement/approval propagation through pi-subagents 0.85 foreground/detached child processes, or `subagent_launch`. Windows alpha degrades to prompts before setup | **Evaluate separately** under same child/escape tests; do not stack both |
| `pi-better-sandbox` + `pi-guard@1.6.0` | Explicit tool-time allow/ask/deny including headless denial, alongside child sandbox | Adds another security/control extension, layered policy conflicts; OS isolation still depends on sandbox's actual backend | Only if the first route lacks required live approval behavior and child gates are proven together |
| `@gotgenes/pi-permission-system@42.0.0` | Rich allow/ask/deny with child prompt forwarding | Documents native integration with its own `@gotgenes/pi-subagents` fork, not necessarily the selected `pi-subagents` package | Not default; extra compatibility fork violates one delegate engine |

Sources: https://pi.dev/packages/pi-permission-modes , https://pi.dev/packages/pi-guard , https://pi.dev/packages/%40gotgenes/pi-permission-system . **Do not conflate a separate `ask_user` decision tool with policy authorization.** If per-action hard gate is mandatory, treat it as OPEN until a single candidate passes a negative runtime test; extension-count minimization must not weaken authorization.

**Interrogate/adversarial obligations**: Child denied `subagent_launch` but still starts; sandbox toggles saved OFF after a restart; subagent credential read permitted by default; symlink/worktree git hook writes outside scope; trusted extension tool bypass; headless `ask_user` auto-approval; pre-0.85 child resume unexpectedly accepted; schedule restores twice or runs after pause. Each must produce an observed denial/failure and a source-linked receipt before a high-confidence claim.

The two [Thermo-Nuclear](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-review) review lenses are distinct: security/correctness follows actual changed diff + breaking behavior, while [code-quality review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-code-quality-review) rejects duplicate orchestration engines, giant adaptor wrappers, reimplemented core APIs, and invented model schemas. Both remain NOT_EXECUTED for the live runtime implementation.

## Canonical-vs-convenience dedup check

- `@narumitw/pi-goal` and `pi-manage-todo-list` are not globally necessary: use PStack plans and the single delegate engine's missions/acceptance, not two ledgers.
- `pi-memory-md` is optional project knowledge; Pi sessions plus PStack `.llm-wiki` are not a replacement for all memory use cases, but adding another memory store requires a concrete missing retrieval need.
- `pi-skillful`, `pi-mention-skill`, `pi-simplify`, `ponytail`, `pi-context-usage`, `pi-btw` are enhancements, not required for PStack role/skill execution.
- `pi-autoresearch`, `pi-interactive-shell`, `pi-lsp`, `pi-fff` are specialized opt-ins, not core.
- `pi-dynamic-workflows` must not run alongside the designated `pi-subagents` delegation owner in the minimal profile.

The acceptance bar remains source-level until Pi and child sessions actually run. Green static CI proves only offline contract validation, **not** safe live execution.

## Implemented candidate slice (follow-up to source audit)

Draft [PR #901](https://github.com/tommy-ca/pstack/pull/901) now implements a namespaced candidate `pstack:pi` in the Windows-safe path `profiles/pstack-pi.json`, preserving the six built-in hosts. `.pi/settings.json` configures Pi's native skills to read `../skills` and pi-subagents' `agentScanDirs` to read `../agents` under `git-root`, with no automatic third-party package installation or copied PStack skills/agents.

A lean `references/pi-essential-extensions.json` records exactly the 3 engineering and 1 research package candidates; its enforcement settings are **required policy expectations**, not proof that Pi has applied them. The existing PStack typed `HarnessProfile` validators are used in `scripts/verify_pi_candidate.py` to check all 17 capabilities, prevent evidence promotion and reject 43 bounded invalid mutations. Pi-native `verify-pi-pstack` and `verify-pi-pstack-formal` skills wrap those checks; the live `drive` action deliberately exits 2 (BLOCKED) until #897 supplies native child/session/worktree/sandbox proof. CI includes those Tier 1 checks.

**Not delivered:** a real native Pi driver, live `pi-subagents` child lifecycle receipts, platform-specific confinement, verified `human.gate`, automated installed-extension compatibility checks, or a full TLC model of actual runtime concurrency. Formal negative controls here cover only the stated PStack *source validator* domain. Raw source ingestion and source hash ledger publication remain #899 work.

Source for native skill paths: https://pi.dev/docs/latest/settings and https://pi.dev/docs/latest/skills. Source for reusing canonical agent definitions without copying: https://github.com/nicobailon/pi-subagents/blob/v0.85.0/docs/agents.md and configuration paths in https://github.com/nicobailon/pi-subagents/blob/v0.85.0/docs/configuration.md .

## 2026-11-05 latest reconciliation: pi-verdict and subagents 0.86.0

This section supersedes the earlier 0.85.0 / three-engineering-package **historical snapshots**, without implying the user's local packages were upgraded. Pi official changelog: [1.5.0](https://pi.dev/changelog/releases/1.5.0) (Nov 2); pi-subagents [0.86.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.86.0) (Nov 5 at 20:33Z), fixing compaction/reload tool availability and typed checks. pi-verdict [0.16.0](https://github.com/jesset/pi-verdict/releases/tag/v0.16.0) (Oct 30) includes ten security audit fixes, but remains a fallible permission-adjudication extension, not a mandatory OS reference monitor.

**New essential profile:** engineering = `pi-subagents@0.86.0` + `pi-better-sandbox@0.14.1` + `pi-verdict@0.16.0` + `pi-ask-user@0.17.2` (**four**); research adds `pi-web-access@0.47.0` (**five**). The existing @zenspc integration is only transitional policy distribution, not canonical PStack. Avoid pi-dynamic-workflows and a second guard. The approved list is source-only and is not installed by this PR.

`pi-verdict` implements a `tool_call` pre-execution handler with self-protection, deterministic denies, configured user rules and model `allow|ask|deny`; an interactive `ask` invokes Pi native `ctx.ui.confirm`. `pi-ask-user` separately exposes structured `ask_user` questions with sequential execution. These differ from PStack's independent mandatory `human.gate`, and no classifier `allow` can substitute for hard authorization. The pi-verdict switch can be turned off, Pi can be started without extensions, custom `ignoreTools` exemptions exist, safety floor can be disabled in the user's config, and fallback model behavior may allow after the primary classifier fails. A parent `tool_call` hook alone does not prove child `subagent_launch` restrictions or detached process isolation. See [security principles](https://github.com/jesset/pi-verdict/blob/main/docs/security-principles.md).

The candidate `references/pi-verdict-pstack.example.json` is manual-only, and `references/pi-essential-extensions.json` states required restrictions but cannot configure the user's actual Pi runtime. The typed model runs **53 bounded failing mutations** after adding ten gate-policy negative controls; the 17 PStack capabilities remain source-classified and `human.gate` is still GAP. Actual installed-version, per-actor authorization and sandbox proof, formal runtime safety and real independent Swarm/Arena/Interrogate / Thermo-Nuclear reviews remain #897–#900.
