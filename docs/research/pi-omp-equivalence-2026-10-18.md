# Pi ↔ OMP equivalence matrix (issue #443, unit U5 of program #429)

Maps every mechanism row of the reference port's Pi equivalence table onto the target's OMP
surface, so a reusable contract test can be told apart from a divergent process/state
implementation before anything is imported. No code changed, no Pi process or session store
imported.

## Revisions

| Side | Revision | Notes |
| --- | --- | --- |
| Reference | `michael-denyer/pstack-claude` `origin/main` `7bad1eb` (plugin `0.9.92`), `docs/pi-equivalence.md` | 61 mechanism rows under `T`, `A`, `H`, `F`, `S`, `C`, `X`. The program's audit lane pinned `94f5ce95`; that revision carries the same rows plus `C03` (`gt`), retired before `7bad1eb`. This matrix keys on the 61 rows live at `7bad1eb` and records `C03` as retired in that port. |
| Target adapter | trunk `main` `cd29b25` — `profiles/omp.json`, `scripts/drivers/omp_rpc.py`, `scripts/drivers/omp.py`, `scripts/verify-portable.py:870-885`, `skills/poteto-mode/references/omp-tools.md` | The typed binding, the bounded RPC v2 session, the four OMP scenarios, and the host mapping doc. |
| Target evidence | `.audit/evidence/omp-receipt.json`, run `omp-1792276078-9617b64f`, host `omp/18.11.2` | canonical / adapter / package `PASS`, runtime `UNTESTED`; the durable receipt pins only `doctor-profile-omp`. Closed receipts: #381 (cancel), #389 (message), #390 (resume). |

`omp://<path>:<line>` cites the host's own documentation shipped with the installed `omp 18.11.2`.
That is a host self-description, not a pstack receipt, and the profiles' static mappings instead
pin the source revision `can1357/oh-my-pi@0affc77` (`profiles/omp.json:33` and the other `GAP:`
notes).
Where a row would turn on the difference between the two revisions, the row says so and claims
nothing.

## Classification

- **same** — both hosts reach the same observable postcondition with no pstack code.
- **different** — OMP reaches an equivalent postcondition by another shape: field, path, process
  model or state store.
- **unproven** — the target exposes a counterpart it cannot reach as shipped (a host method the
  adapter does not drive, a mechanism no driver path exercises) and no receipt settles it, so the
  row is neither mapped nor denied. A row whose mechanism is simply absent is `different` instead:
  the absence is itself settled. A GAP row in `profiles/omp.json` stays GAP here.

The `Settlement` column is the strongest target evidence behind the row: `host-doc` (installed
host docs only), `static` (typed binding or repo artifact, `verification_status: static-only`),
`static + historical live` (a 2026-10-13 live settlement the 2026-10-17 static refresh dropped),
`offline receipt` (a doctor scenario in the durable receipt), `none`. No row is settled live at
its current revision, so `different` never means "verified on both hosts": a `host-doc` or `static`
row is a mapping, not proof, and its host behavior stays unproven until a host-version-specific
live receipt settles it. That is why no row claims parity, and why the single `unproven` row is
the steering row (T07), whose host method exists only in the host's own docs.

## T — agent tool and session surface

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| T01 | `Agent` tool dispatch | native `task` tool spawns a subagent session in-process (`omp://tools/task.md:1,43`); the adapter's second lane drives a real child over `omp --mode rpc` v2 (`skills/poteto-mode/references/omp-tools.md:12,33`; `scripts/drivers/omp.py:323`); profile `agent.spawn` native (`profiles/omp.json:10-16`) | different | static + historical live |
| T02 | `subagent_type` | `agent` per item (`omp://tools/task.md:43`); resolution order `.omp` project → user → extension roots → Claude marketplace → bundled `scout`/`reviewer`/`security-reviewer` (`omp://task-agent-discovery.md:129-135,157-177`); unknown or disabled agents fail preflight (`omp://tools/task.md:97,180`). pstack role agents are `agents/*.md` (`agents/poteto-agent.md:1-3`) | different | static |
| T03 | Per-call `model` | the `task` wire shape has no model field (`omp://tools/task.md:38-50`); the child's model resolves `task.agentModelOverrides` → agent frontmatter → role/session fallback (`omp://tools/task.md:107`). `profiles/omp.json:248-252` lists `model` among `allowed_spawn_fields` — a pstack wire convention the host shape does not carry; recorded as an open discrepancy, not promoted | different | host-doc |
| T04 | `run_in_background` | background is a session setting (`async.enabled`), not a per-call flag; each non-blocking spawn registers an async job and the call returns immediately (`omp://tools/task.md:64,99-104`); a blocked caller uses `wait` (`omp://tools/wait.md:1`) | different | static |
| T05 | `readonly` | no per-spawn read-only field; plan mode supplies the read-only tool set and rejects isolation/apply controls (`omp://tools/task.md:108`); an agent's explicit `agent.tools` can omit writers (`omp://tools/task.md:114`); profile calls `workspace.readonly` native but **advisory** (`profiles/omp.json:73-79`) | different | static |
| T06 | Worktree per writer | `isolated: true` per item, backend resolved by the isolation PAL (`overlayfs`, `btrfs`, `reflink`, copy, …) (`omp://tools/task.md:50,109-111,132-133`); workspace directories are host-owned, not `.claude/worktrees` (`omp://tools/task.md:142`); scenario `runtime-isolation-omp` checks patch capture and residue (`scripts/drivers/omp.py:619-810`); `profiles/omp.json:64-70` | different | static + historical live |
| T07 | Message an agent | the host has RPC `steer_subagent` (`omp://rpc.md:161,1039-1048`) and peer messaging `write agent://<id>` (`omp://tools/task.md:122,191`), but the runner's bounded session exposes no steer method (`scripts/drivers/omp_rpc.py:306-352`) and no scenario settles messaging — **GAP retained** (`profiles/omp.json:28-35`, #389) | unproven | none |
| T08 | Stop an agent and confirm it stopped | `cancel_subagent` over RPC (`scripts/drivers/omp_rpc.py:348`, `scripts/drivers/omp.py:503`) and `write proc://<id>/kill` (`omp://tools/task.md:157`, `skills/poteto-mode/references/omp-tools.md:47`); the cancel scenario is omp-only by design (`scripts/verify-portable.py:870-885`); profile native/hard, static-only since the refresh dropped the live settlement (#381, run `omp-1791892165-cbc0cc6e`) | different | static + historical live |
| T09 | Agent listing and completion notices | `get_subagents` over RPC (`scripts/drivers/omp_rpc.py:344`, `omp://rpc.md:158,1004`); `read proc://<id>` inspects without consuming delivery; `agent://<id>` and `history://<id>` hold output and transcript (`omp://tools/task.md:191`); profile `monitor` is a **shim** with no settling scenario (`profiles/omp.json:118-124`) | different | static |
| T10 | Deferred tool loading (`ToolSearch`) | no deferral layer: `tools.discoveryMode`, `tools.essentialOverride` and `mcp.discoveryMode` were removed (`omp://settings.md:1054`); each tool carries a load mode (`omp://tools/task.md:161`) and skills resolve on demand through `skill://` (`omp://skills.md:182`) | different | host-doc |
| T11 | `Skill` tool and `/command` | skills load natively through the plugin manifest (`skills/poteto-mode/references/omp-tools.md:11`); `/skill:<name>` forces one, embedding the body and the skill directory (`omp://skills.md:6,155-175`) | same | host-doc |
| T12 | `pstack:` skill namespace | bare names, with `<namespace>/<name>` only on a collision, namespace from plugin identity (`omp://skills.md:130,133`); agent types keep their file names (`omp://task-agent-discovery.md:57-61`) | different | host-doc |
| T13 | `AskUserQuestion` | `ask` with `{questions[{id, question, options, multi, recommended}]}` (`omp://tools/ask.md:1,14-26`); profile `human.ask` native/**advisory**, GAP note that no scenario settles asking (`profiles/omp.json:82-87`) | different | static |
| T14 | `TaskCreate`/`TaskUpdate`/`TodoWrite` | native `todo` tool owning phases and tasks per session (`omp://tools/todo.md:1`); profile `plan.update` native/advisory with a GAP note (`profiles/omp.json:100-105`); the `todo.md` fallback is a Grok-era adaptation, not the OMP surface (`skills/poteto-mode/references/omp-tools.md:15`) | different | static |
| T15 | `Read`/`Edit`/`Write`/`Bash`/`Grep`/`Glob` | `read`, `edit`, `write`, `bash`, `grep`, `glob` (and `find`) (`skills/poteto-mode/references/omp-tools.md:9`) | same | host-doc |
| T16 | `WebFetch`/`WebSearch` | `read` for a URL and native `web_search` (`skills/poteto-mode/references/omp-tools.md:10`), not a curl workaround | different | host-doc |
| T17 | `ScheduleWakeup` | no scheduler: profile `schedule` is **gap** with `verification_status: unverified` (`profiles/omp.json:109-114`), and no scheduled-run surface exists in the host tool docs | different | none |
| T18 | MCP tool discovery | native MCP servers, mapped `tool_mcp: mcp` and reached as `mcp://<uri>` (`profiles/omp.json:187`; `omp://mcp-config.md`) | same | static |
| T19 | Facts named in the system prompt | context files are discovered and injected at session start — `.omp/AGENTS.md` user and nearest non-empty project, plus standalone `AGENTS.md`/`CLAUDE.md` (`omp://context-files.md:5,24-25,71-79`); base prompt blocks are hashed into `system-prompt-digest` (`omp://session.md:331`) | different | host-doc |
| T20 | Image-generation tool | OMP has `generate_image`, default off and needing an explicit tool filter (`omp://tools/generate_image.md:2,11`), where the reference host has none; no pstack skill depends on either | different | host-doc |
| T21 | Nested agents up to three layers | host cap is `task.maxRecursionDepth`, default 2 (`omp://tools/task.md:171`) against the pstack policy claim `max_subagent_depth: 1` (`profiles/omp.json:242`, `skills/poteto-mode/references/omp-tools.md:22`); the profile's own note records that no nested grandchild spawn has run | different | static |

## A — agent definitions

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| A01 | `pstack:poteto-agent` | role agent file `agents/poteto-agent.md:1-3`, reached through host agent discovery and frontmatter (`omp://tools/task.md:43,107`; `omp://task-agent-discovery.md:129-177`) | different | static |
| A02 | Effort agents (`effort:` frontmatter → `--thinking`) | per-spawn effort is `lo`, `med`, `hi` gated by `task.enableEffort` (default off) (`omp://tools/task.md:46,162`), and an agent's own selector supplies the default (`omp://tools/task.md:46`; `omp://models.md:635`) | different | host-doc |
| A03 | `pstack:comment-sicko` | same path as A01 with `agents/comment-sicko.md` | different | static |
| A04 | Manifest `agents[]` registration | the OMP manifest carries only an `omp` block; conventional `skills/<name>/SKILL.md` and `agents/*.md` siblings are what the host discovers (`scripts/project-package.py:149-167`, `.omp-plugin/package.json`) | different | static |
| A05 | `general-purpose` agent type | the spawn policy's default agent, usually `task` (`omp://tools/task.md:43`); no pstack agent file needed | different | host-doc |
| A06 | Agent file body as the child's system prompt | the host assembles the child prompt: the agent file plus the call's `CONTEXT` section (`omp://tools/task.md:35`); the reference's `--append-system-prompt` assertion does not transfer | different | host-doc |

## H — hooks and configuration

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| H01 | `SessionStart` hook | the host has a `session_start` hook event and loads hook modules from `.omp/hooks/pre/*.ts` (`omp://hooks.md:10,80,118`), but the OMP package ships no hook (`scripts/project-package.py:149-167`); routing is carried by skills | different | host-doc |
| H02 | `CLAUDE_PLUGIN_ROOT` | the host enrolls a package by the `omp` (or legacy `pi`) key and then discovers its conventional roots (`scripts/project-package.py:152-156`); installed plugin packages live under `~/.omp/plugins/node_modules` (`omp://skills.md:93`) | different | host-doc |
| H03 | `~/.claude` config directory | `~/.omp/agent` for user context and `~/.omp/plugins` for plugins (`omp://context-files.md:24`; `profiles/omp.json:4-5`) | different | static |
| H04 | Override sheet plus `@` include | no override-sheet mechanism in the target adapter — `grep -rn sheet` over the repo's own sources finds nothing outside vendored packages; the reference's sheet is Grok/Claude prose | different | static |
| H05 | `CLAUDE.md` instructions file | `.omp/AGENTS.md` (user, and project from the nearest non-empty `.omp/`), standalone `AGENTS.md` and `CLAUDE.md` providers all load (`omp://context-files.md:71-79`) | different | host-doc |
| H06 | `.claude/settings.local.json` env for todo tools | not applicable: OMP has native todo tools, so no env shim is needed (`omp://tools/todo.md:1`; `profiles/omp.json:100-105`) | different | host-doc |

## F — files, transcripts and stores

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| F01 | `~/.claude/projects` transcripts | file-backed JSONL sessions at `~/.omp/agent/sessions/<encoded-cwd>/<timestamp>_<sessionId>.jsonl` (`omp://session.md:42,65`); profile `session.persist` native with no settling scenario (`profiles/omp.json:127-131`) | different | static |
| F07 | Own transcript as evidence | `history://<id>` is a concise transcript and `agent://<id>` the full output (`omp://tools/task.md:26,191`); durable evidence is the four-plane receipt under `.audit/evidence/` (`profiles/omp.json:145-150`) | different | offline receipt |
| F02 | `.claude/skills/` project and user skills | `.omp/skills` through the `native` provider, or the `agents` provider (`.agent[s]/skills`) (`omp://skills.md:89,122`; `profiles/omp.json:4`) | different | static |
| F03 | `~/.claude/plugins/` install path | `~/.omp/plugins/node_modules` through the `omp-plugins` provider (`omp://skills.md:93`) | different | static |
| F04 | `~/.claude/orchestrate/<slug>/` store | no store is shipped: durable orchestration state stays host-owned (`adr/0006-host-owned-durable-orchestration-state.md:10-12`), and the host session file is the durable record (`omp://session.md:42`) | different | static |
| F05 | `~/.claude/shell-snapshots/` cleanup advice | nothing to port: OMP has no shell-snapshot store, and the row is advice in both ports | same | host-doc |
| F06 | `.claude/worktrees` | host-owned isolation workspace directories under the isolation lifecycle (`omp://tools/task.md:142`; residue check `scripts/drivers/omp.py:138-155`) | different | static + historical live |

## S — skills

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| S01 | Bundled `run` skill | run the app through `bash` (`skills/poteto-mode/references/omp-tools.md:9`) | same | host-doc |
| S02 | `verify` skill | project verification is `scripts/verify-portable.py` with the four-plane receipt (`docs/guide/12-porting.md:179-181`) | different | offline receipt |
| S03 | `loop` skill | no interval or self-paced scheduler on OMP (`profiles/omp.json:109-114`) — **GAP retained** | different | none |
| S04 | `plugin-dev:skill-development` | the host's skills docs plus skill authoring; pstack ships `skill-authoring`/`writing-skills` (`omp://skills.md:240,255`) | different | host-doc |
| S05 | Bundled `babysit` disambiguation | OMP bundles no `babysit`: its skill providers are `native`, `skillshare`, `omp-plugins` and vendored foreign providers (`omp://skills.md:89-102`), and bundled agents are `scout`/`reviewer`/`security-reviewer` (`omp://task-agent-discovery.md:135`), so the reference's collision does not arise from the host | same | host-doc |
| S06 | `superpowers`, `code-review`, `simplify`, `security-review` | no bundled counterparts; the OMP-native review surfaces are the bundled `reviewer` and `security-reviewer` agents (`omp://task-agent-discovery.md:135`); the pstack skills keep their own names | different | host-doc |
| S07a | Frontmatter `user-invocable: false` | not a host field: the skill frontmatter set is `name`, `description`, `globs`, `alwaysApply`, `hide`, `disableModelInvocation`, `enabled`, with unknown keys preserved as metadata (`omp://skills.md:52-60`); menu-visibility claims stay unproven | different | host-doc |
| S07b | Frontmatter `paths:` auto-load | `globs` and `alwaysApply` are metadata, explicitly not invocation controls (`omp://skills.md:63`); exactly one pstack skill sets `paths:` (`skills/typescript-best-practices/SKILL.md`) | different | host-doc |
| S07c | Frontmatter `disable-model-invocation` | honored: normalized to `disableModelInvocation` (`omp://skills.md:59`); 50 pstack skills set it. The reference's "no pstack skill sets it" describes that port, not this tree | same | host-doc |

## C — CLIs and scripts

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| C01 | `gh` | same CLI through `bash` (`skills/poteto-mode/references/omp-tools.md:9`); the host also ships a native `github` tool (`omp://tools/github.md`) | same | host-doc |
| C02 | `origin` | same CLI through `bash` (`skills/poteto-mode/references/omp-tools.md:9`) | same | host-doc |
| C03 | `gt` (Graphite) | retired in the reference before `7bad1eb`; no OMP row to map | n/a | none |
| C04 | `claude`/`codex` CLI | prose only; no OMP adapter behavior depends on it | same | host-doc |
| C05 | `bun` scripts | run through `bash`; `eval` JavaScript workers are Bun-backed (`omp://tools/eval.md:72`) | same | host-doc |
| C06 | `node` scripts | run through `bash` | same | host-doc |

## X — model, effort and context

| Row | Reference mechanism | OMP counterpart (evidence) | Class | Settlement |
| --- | --- | --- | --- | --- |
| X01a | Family names (`opus`, `fable`, `sonnet`, `haiku`) on an Anthropic session | not a target concept: selection is role → tier → model, and the OMP host block resolves every tier to `inherit-parent` with an empty catalog and `fallback: fail-closed` (`examples/portability/model-role-policy.example.json`, `hosts.omp`); `profiles/omp.json:247` sets `default_model: "pi"`; the host switches by role or preset with a `:thinkingLevel` suffix (`omp://models.md:635,705-726`) | different | static |
| X01b | Family names on a ChatGPT sign-in | as X01a: no per-provider family table on the OMP surface | different | static |
| X01c | Family names on the legacy OpenAI Codex sign-in | as X01a: no per-provider family table on the OMP surface | different | static |
| X02 | Effort levels and `@level` | `:thinkingLevel` accepts `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, `auto`, `inherit` (`omp://models.md:635`) and gated `lo`, `med`, `hi` per spawn (`omp://tools/task.md:46,162`); pstack's four-value ladder is a Grok snapshot (`scripts/effort_ladder.py:19-21`) | different | host-doc |
| X03 | `inherit-parent` / `auto` | same semantics, different plumbing: the OMP tier default is `inherit-parent` (`examples/portability/model-role-policy.example.json`, `hosts.omp.tier_defaults`), the child takes the parent's model unless an override or frontmatter names one (`omp://tools/task.md:107`), and `:inherit`/`auto` exist as thinking suffixes (`omp://models.md:635`) | same | static |
| X04 | Compaction and `/clear` | `/clear` writes a reset/compaction boundary and rebuilt context starts after it (`omp://session.md:305`; `omp://compaction.md`); skills re-resolve per session through the plugin manifest (`skills/poteto-mode/references/omp-tools.md:11`), so routing does not depend on a hook re-injection | different | host-doc |
| X05 | Session scratchpad | the session file and the artifacts directory are the durable store (`omp://session.md:42`); no scratchpad concept exists | different | host-doc |

## Profile reconciliation

Every `profiles/omp.json` row that carries a `GAP:` note or a `gap` status is reachable from this
matrix, and no row here upgrades one. Rows marked **GAP** match the profile exactly.

| `profiles/omp.json` binding | Status (line) | Rows it carries | Matrix class |
| --- | --- | --- | --- |
| `agent.spawn` | native, static-only (10-16) | T01, T02, T03, A01, A04, A05, A06 | different, no receipt at this revision |
| `agent.join` | native, static-only (19-23) | T04, T09 | different, no receipt |
| `agent.message` | **gap** (28-35) | T07 | unproven — GAP retained, #389 |
| `agent.cancel` | native, static-only (37-42) | T08 | different, historical live only |
| `agent.resume` | native, static-only (46-50) | F01 | different, no receipt (#390) |
| `workspace.shared` | native, GAP note (55-59) | F06 | different, no receipt |
| `workspace.isolated` | native, static-only (64-70) | T06, F06 | different, no receipt at this revision |
| `workspace.readonly` | native, advisory, GAP note (73-79) | T05 | different, advisory only |
| `human.ask` | native, advisory, GAP note (82-87) | T13 | different, no receipt |
| `human.gate` | native, advisory, GAP note (91-96) | T13 | different, no receipt |
| `plan.update` | native, advisory, GAP note (100-105) | T14 | different, no receipt |
| `schedule` | **gap**, unverified (109-114) | T17, S03 | different — GAP retained |
| `monitor` | shim, GAP note (118-124) | T09 | different, no receipt |
| `session.persist` / `session.resume` | native, GAP notes (127-140) | F01, X05 | different, no receipt |
| `evidence.capture` | native, offline scenario only (145-150) | F07 | different, offline only |
| `verify` | native, `doctor-profile-omp` (154-163) | S02 | different, offline only |

## Reusable contract tests vs divergent implementations

Reusable (host-neutral postconditions, safe to drive on any host): the capability vocabulary and
binding schema, the per-capability scenario ids (`runtime-child-spawn-omp`,
`runtime-child-cancel-omp`, `runtime-isolation-omp`, `runtime-evidence-capture-omp`,
`doctor-profile-omp`), the four-plane receipt shape, and the live gate pattern in
`tests/test_omp_rpc.py:271`. A second host reruns the same scenario ids against its own driver.

Divergent, so nothing may be copied across (and nothing was):

- Process model. The reference drives a Pi extension that starts `pi --mode rpc` and sends the
  prompt as an RPC command; the OMP adapter drives a bounded `omp --mode rpc` v2 session and
  reduces `subagent_lifecycle` frames (`scripts/drivers/omp_rpc.py:264-378`).
- Steering. Pi's `send_message` is an RPC steer on the child's stdin. OMP's host method exists
  (`omp://rpc.md:161`) but the runner does not expose it, so the row stays GAP.
- Session and transcript store. Pi layouts (`find-transcript.mjs`, `.claude/projects`) have no OMP
  equivalent; OMP sessions are JSONL under `~/.omp/agent/sessions/`. No Pi process or session
  store is imported (issue #443 acceptance).
- Isolation paths and backends. `.claude/worktrees` against the host isolation PAL
  (`overlayfs`/`btrfs`/`reflink`/copy), with a different residue contract.
- Model and effort resolution. A per-provider family table against role → tier → model with
  `inherit-parent` and `fail-closed`; `--thinking` against the `:thinkingLevel` set plus gated
  per-spawn effort.
- Hook and sheet injection. A `SessionStart` hook and an `@`-include sheet against skills that
  re-resolve per session and host context-file discovery.
- Scheduler. Present in the reference's skill surface, absent on OMP, so `schedule` stays a
  declared gap rather than a synthesized store.

## Open items

1. `agent.message` stays GAP (#389). The host documents `steer_subagent`; no driver method and no
   receipt settle it, so the row is not promoted on documentation alone.
2. `profiles/omp.json:248-252` lists `model` among `allowed_spawn_fields`, but the host's `task`
   wire shape has no model field (`omp://tools/task.md:38-50`). Either the adapter translates a
   pstack wire convention or the profile narrows it; this pass records the discrepancy and changes
   nothing.
3. Host revision. The profile's static mappings pin `can1357/oh-my-pi@0affc77`; the installed host
   is `omp/18.11.2`. `omp://` citations are the installed host's docs, and no row claims behavior
   that could differ between the two without a host-version-specific live receipt.
4. No runtime parity is claimed: the durable receipt's runtime plane is `UNTESTED`, and the
   historical live settlements for spawn, cancel and isolation were dropped by the 2026-10-17
   static refresh. Restore with
   `PSTACK_RUN_OMP_LIVE=1 python3 scripts/verify-portable.py run --host omp`.
5. `C03` (`gt`) is retired in the reference port; this matrix has no row for it.
