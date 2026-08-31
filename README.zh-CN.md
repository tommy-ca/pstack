# pstack

[English](README.md) · [简体中文](README.zh-CN.md)

这是 official pstack 的 Grok Build 移植。玩法和原则来自 poteto 的 official pstack；调用层换成 grok-build 工具。

## 来源

22 个玩法（playbooks）和 21 条原则（principles）是 [poteto](https://x.com/poteto) 写的，出自 [official pstack](https://github.com/cursor/plugins/tree/main/pstack)。本仓库是 **`tommy-ca/pstack`**，适配自 [aa2246740/pstack-grokbuild](https://github.com/aa2246740/pstack-grokbuild)。调用层用 [HARNESS.md](./HARNESS.md) 里的 Grok Build 工具名。玩法和原则不是本仓库写的。

poteto 的判断是：少写 slop；想快就先做深；当你能信一个 agent 写出可核验的代码，才谈得上放心并行。那是 poteto 的想法，下面按来源引用，不当成本仓库作者的自述。

## 安装

```bash
grok plugin install tommy-ca/pstack --trust
grok plugin enable pstack
```

xAI Official 也登记了一个名为 `pstack` 的插件，指向 `cursor/plugins`。用 owner/repo。不要把裸的 `grok plugin install pstack` 当成这份移植。本仓库是单插件树。不要嵌成 `plugins/pstack`。可选目录：[tommy-ca/grok-build-plugins](https://github.com/tommy-ca/grok-build-plugins)。

本地目录也可以：

```bash
grok plugin install /path/to/pstack --trust
grok plugin enable pstack
```

## 第一次会话

1. `grok plugin enable pstack` 若对 `config.toml` 报 EROFS，到**宿主 shell** 跑：

   `grok --sandbox off plugin enable pstack`

   或在 Plugins 页按空格。`inspect` 的 enabled 是 trust。技能和 `pstack:<role>` agent 只有写进 `[plugins].enabled` 才会加载。

2. 重载：Plugins 页按 `r`，或开**新会话**。当前会话在 enable 之后不会长出 `pstack:how-explorer`。

3. Spawn 用 `pstack:how-explorer`，不要用 `how-explorer`。输入 `/poteto-mode …`。它不会自动进。`/setup-pstack` 可选。

4. 不要在沙箱 agent 里跑 `grok plugin marketplace add`。那也会写 `config.toml`，同样 EROFS。会话里 owner/repo 安装仍然可用。

工具对照见 [HARNESS.md](./HARNESS.md)。

## 开始用

两步。

1. 要做事、要严谨，直接用 [`/poteto-mode`](./skills/poteto-mode/SKILL.md)。不用先跑 setup。
2. 只有想改模型或 effort 时，才跑 [`/setup-pstack`](./skills/setup-pstack/SKILL.md)。它是可选的、全局的，写入 `~/.grok/pstack-models.toml` 和 `~/.grok/roles/pstack:<role>.toml`。

第一次用可以看 [pstack 指南](./docs/guide/README.md)：安装、提问、核验、过夜跑。指南是英文。

其余技能是按需的。`/poteto-mode` 会在步骤需要时自己去调。

## 默认模型与 effort

装完就能用，不必先 `/setup-pstack`。

**模型.** 每个角色默认 `grok-4.6`。若 `spawn_subagent` 拒收这个 slug，就省略 `model`。不要编造 Cursor 面板 slug（`grok-4.6-fast-xhigh`、`gpt-5.6-sol-max`、`claude-fable-5-thinking-max`、`claude-opus-5-thinking-xhigh`）。Spawn 和 join 的名字见 [HARNESS.md](./HARNESS.md)。`spawn_subagent` 的线名别名是 `task`。

**effort.** 以 grok 1.0.13 现场 CLI 为准。`use one of: xhigh, high, medium, low`。本仓库出厂分层是判断 / 解释 / 核对 / 评审组 `xhigh`，跟指令（bug-fix、perf-issue、hillclimb、reflect-tooling）`high`，机械活（feature、refactoring、how-explorer、why-investigators、swarm-workers）`medium`。不默认 `max`。这个 CLI 不认 `max`。skill 从不在 `spawn_subagent` 上发送 `reasoning_effort`。

没有覆盖文件就用上述出厂值。toml 里缺键、`inherit-parent` 或 `auto` 时，省略 `model`。`/setup-pstack` 会按当前 CLI 的 `use one of:` 再探测一遍；若分层变了就重写。二进制以后多出新档位，要再跑一次 setup。子 skill 看不到新 enum。

## 这不是 Cursor 插件

这里的 [`/setup-pstack`](./skills/setup-pstack/SKILL.md) 只给 Grok Build 配模型和 effort。官方 Cursor `/setup-pstack`（Cursor 里，或 Grok Bot 里那份）是另一个插件。那份会写 `~/.cursor/rules`，并用 Cursor 的模型名。不要在 Grok Build 上跑那份，也不会在这里生效。

## 用法

任务开头用 [`/poteto-mode`](./skills/poteto-mode/SKILL.md)。它读请求、选一个玩法、按步骤去调其他 skill。

### 直接用 `/poteto-mode`

这是主入口。需要严谨工程时从这里进。内置二十二个玩法：

```
/poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro
first, then fix and verify.
```

```
/poteto-mode i'm going to bed. land the stack even if ci flakes. i want everything merged by
morning.
```

<details>
<summary>二十二个玩法</summary>

| playbook | for |
|---|---|
| [investigation](./skills/poteto-mode/playbooks/investigation.md) | a read-only question. how does x work, why was y built this way, are we sure. |
| [bug fix](./skills/poteto-mode/playbooks/bug-fix.md) | reproduce a defect, root-cause it, and fix with runtime evidence. |
| [perf](./skills/poteto-mode/playbooks/perf-issue.md) | trace a measured slowness and improve it against a baseline. |
| [hillclimb](./skills/poteto-mode/playbooks/hillclimb.md) | sustained, scientific improvement of one metric against a target, looping hypotheses with before/after measurement and one commit per accepted win. |
| [runtime forensics](./skills/poteto-mode/playbooks/runtime-forensics.md) | diagnose a live symptom (leak, idle-cpu spin, glitch) from instrumentation. |
| [trace forensics](./skills/poteto-mode/playbooks/trace-forensics.md) | diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot). |
| [feature](./skills/poteto-mode/playbooks/feature.md) | new or changed behavior, built from a named data shape. |
| [refactoring](./skills/poteto-mode/playbooks/refactoring.md) | a behavior-preserving change to structure or shape. |
| [prototype](./skills/poteto-mode/playbooks/prototype.md) | a throwaway sketch to make a design or behavioral decision cheaply, or to settle an empirical fork by observing it. |
| [visual parity](./skills/poteto-mode/playbooks/visual-parity.md) | pixel-exact ui equivalence between two implementations. |
| [authoring a skill](./skills/poteto-mode/playbooks/authoring-a-skill.md) | writing or editing a SKILL.md. |
| [eval](./skills/poteto-mode/playbooks/eval.md) | test how a skill or prompt change affects agent behavior, blinded. |
| [babysit](./skills/poteto-mode/playbooks/babysit.md) | drive a pr or a stack to merge-ready: conflicts, review threads, ci. |
| [shipping](./skills/poteto-mode/playbooks/shipping.md) | independently verify a green stack, then land the contiguous verified run with graphite merge-when-ready. |
| [autonomous run](./skills/poteto-mode/playbooks/autonomous-run.md) | drive a long task to completion without stopping. |
| [orchestrate](./skills/poteto-mode/playbooks/orchestrate.md) | a standing project handed to one coordinator chat: multi-day, many stacked prs, fleets of subagents. |
| [autopilot-full](./skills/poteto-mode/playbooks/autopilot-full.md) | run independent prs to merged with one owner per pr and root verification of each merge-ready head. |
| [autopilot-stack](./skills/poteto-mode/playbooks/autopilot-stack.md) | build and verify one linear graphite stack for the operator to review and land. |
| [session pickup](./skills/poteto-mode/playbooks/session-pickup.md) | resume or take over a prior agent's in-flight work. |
| [pause safely](./skills/poteto-mode/playbooks/pause-safely.md) | suspend in-flight work cleanly so it can be resumed later. |
| [multi-phase plan](./skills/poteto-mode/playbooks/multi-phase-plan.md) | work that spans phases or stacked PRs. |
| [worktree cleanup](./skills/poteto-mode/playbooks/worktree-cleanup.md) | reclaim disk by pruning merged or abandoned worktrees and stale ios simulators, safety-gated. |

</details>

调用之后它会：

1. 打开 todo。第一项是读 skill 里的原则索引。
2. 把任务匹配到一个 [玩法](./skills/poteto-mode/playbooks/)，把步骤原样拷进 todo。
3. 步骤触发时转到其他 skill。
4. 按读者和维护者各写一版、去掉 slop 的回复。

完整规则和玩法在 [`skills/poteto-mode/SKILL.md`](./skills/poteto-mode/SKILL.md)。

匹配到玩法、或任务需要严谨时再输入 [`/poteto-mode`](./skills/poteto-mode/SKILL.md)。它不会自动进。同一会话的后续轮次保持这套风格，直到你说退出。

[`/poteto-mode`](./skills/poteto-mode/SKILL.md) 能跟 grok-build `/loop` 一起用（展开为 `scheduler_create`）。可以把可检查的谓词挂几个小时，不必丢掉严谨性。

## 技能

[`/poteto-mode`](./skills/poteto-mode/SKILL.md) 会在步骤需要时替你跑其中大部分（`how`、`why`、`architect`、`arena`、`swarm`、`interrogate`、`unslop`、`no-comments`、`technical-writing`、`tdd`，以及原则）。下表是想单独点某个 skill 时用的。

```
/how do we cancel runs? do we have an n+1 when we look up every run to cancel?
```

```
/interrogate review this pr.
```

<details>
<summary>全部技能</summary>

| skill | use it when |
|---|---|
| [`/poteto-mode`](./skills/poteto-mode/SKILL.md) | default entry point for any non-trivial task. |
| [`/how`](./skills/how/SKILL.md) | you want a walkthrough of how a subsystem works. |
| [`/why`](./skills/why/SKILL.md) | you want to know why something was built this way. discovers available MCPs at run time and queries each evidence category in parallel (source control, issue tracker, long-form docs, real-time chat, infra observability, error tracking, analytics warehouse). |
| [`/recall`](./skills/recall/SKILL.md) | you're starting or resuming work and want your recent context on a topic rebuilt from your own chat history and the shared record, handed back as a tight current-state brief. |
| [`/blast-radius`](./skills/blast-radius/SKILL.md) | you have a small-looking change and want to know what else it could break, with the one fact it's safe because of proven by running code, not asserted. |
| [`/architect`](./skills/architect/SKILL.md) | you're about to write code that crosses a function boundary and want the caller's usage, types, and module shape settled first. |
| [`/arena`](./skills/arena/SKILL.md) | you want N parallel attempts at the same thing, then to grab the best parts of each. |
| [`/swarm`](./skills/swarm/SKILL.md) | you want N parallel workers across different slices or races, then one aggregated report. |
| [`/interrogate`](./skills/interrogate/SKILL.md) | you have a diff and want several different models to try to break it, including a strict code-quality lens. |
| [`/automate-me`](./skills/automate-me/SKILL.md) | you want your own `-mode` skill, drafted from how you've actually worked. |
| [`/setup-pstack`](./skills/setup-pstack/SKILL.md) | override the shipped `grok-4.6` + per-role effort default. detects your models and writes `~/.grok/pstack-models.toml` plus `~/.grok/roles/pstack:<role>.toml`. |
| [`/reflect`](./skills/reflect/SKILL.md) | a long task landed and you want the recipe captured as a skill edit. |
| [`/teach`](./skills/teach/SKILL.md) | you want to actually understand a change or subsystem, not just have it summarized. runs how + why and weaves one plain explanation, built up diagram by diagram. |
| [`/tdd`](./skills/tdd/SKILL.md) | you're fixing a bug and there's a cheap local test path. write the failing test first, then the fix. |
| [`/no-comments`](./skills/no-comments/SKILL.md) | strip comments before review; spawns Comment Sicko, fixes accepted findings, offers encodings for claimed constraints. |
| [`/typescript-best-practices`](./skills/typescript-best-practices/SKILL.md) | you're reading or editing typescript. grounds the type-system-discipline principle in syntax. |
| [`/figure-it-out`](./skills/figure-it-out/SKILL.md) | no bundled playbook fits. designs a rigorous, auditable playbook for the task. |
| [`/show-me-your-work`](./skills/show-me-your-work/SKILL.md) | you want a reviewable decision trail. logs decisions to a tsv you can commit. |
| [`/create-verification-skill`](./skills/create-verification-skill/SKILL.md) | your project has no scripted way to prove app behavior. generates a project-local verify skill with a feature map, for any language or platform. |
| [`/maintain-verification-skill`](./skills/maintain-verification-skill/SKILL.md) | your verify skill's feature map has drifted from the app. source wave + one live pass, at most one PR of proven corrections. |
| [`/unslop`](./skills/unslop/SKILL.md) | you're cleaning up writing. removes AI tells. |
| [`/bro`](./skills/bro/SKILL.md) | you want the last message restated in plain human language, no jargon. |
| [`/technical-writing`](./skills/technical-writing/SKILL.md) | layered doc standard (Diátaxis + Google developer style + STE + Global English) for docs, RFCs, readmes, PR descriptions, commit messages. |

</details>

### 示例

多数任务在开头打 [`/poteto-mode`](./skills/poteto-mode/SKILL.md)，让它选玩法。其他 skill 由步骤按需触发。下面这些是偶尔直接点的。

<details>
<summary>全部示例</summary>

```
bug fix:           /poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even
                   when idle. repro first, then fix and verify.
perf:              /poteto-mode a big list takes a second or two to load even though we virtualize.
                   run a cpu trace and tell me why.
feature:           /poteto-mode build a small feature behind a feature flag. verify it really works.
prototype:         /poteto-mode build two prototypes of the markdown renderer so we can compare.
                   spawn an agent for each.
multi-phase:       /poteto-mode open source these skills as a plugin. nothing internal leaks, work
                   in a temp dir, show me the dependency graph first.
overnight run:     /poteto-mode i'm going to bed. land the stack even if ci flakes. i want
                   everything merged by morning.
babysit:           /poteto-mode check on pr 123. anything outstanding?
visual parity:     /poteto-mode the row spacing is too tall when this flag is on. the second image
                   is correct. repro and fix until it matches.
figure it out:     /poteto-mode i'm stepping away. migrate every caller from the synchronous store
                   to the new async one, keeping behavior identical. i want to trust it was done
                   right when i'm back.
how:               /how do we cancel runs? do we have an n+1 when we look up every run to cancel?
why:               /why is this feature flag not on yet?
architect:         design this instrumentation to be high signal with no false positives. /architect
                   this first.
arena:             /arena take my prompt to the arena verbatim. i want to compare their proposals
                   with yours.
swarm:             /swarm check every package under packages/ against its check.sh. one worker per
                   package. one report.
interrogate:       /interrogate review this pr.
tdd:               /tdd implement
unslop:            can we unslop and tighten the new changes?
reflect:           /reflect that took too long. capture what we learned so the next run doesn't
                   repeat it.
show-me-your-work: /show-me-your-work keep a decision trail i can review when i'm back.
automate-me:       /automate-me
```

</details>

## poteto-agent 与 Comment Sicko

本插件还带一个把这套风格跑到底的子 agent。没有角色键时，父会话用 `spawn_subagent` 的 `subagent_type: "pstack:poteto-agent"` 生成它。`spawn_subagent` 的线名别名是 `task`。玩法角色生成 `pstack:<role-key>`（`pstack:feature`、`pstack:how-explainer` 等），这样出厂 frontmatter `effort` 会生效，`/setup-pstack` 写在 `~/.grok/roles/pstack:<key>.toml` 里的覆盖也能生效。换成 `general-purpose` 会跳过 poteto-mode 的阅读，容易漂。子进程不能再生成更深的子进程（`MAX_SUBAGENT_DEPTH` 是 1）。不要在 `spawn_subagent` 上发送 `reasoning_effort`。

[`/poteto-mode`](./skills/poteto-mode/SKILL.md) 和 [`subagent_type: "pstack:poteto-agent"`](./agents/poteto-agent.md) 走同一层包装。

另外还有 [Comment Sicko](./agents/comment-sicko.md)，只读评论审查，`subagent_type: "pstack:comment-sicko"`。一般通过 [`/no-comments`](./skills/no-comments/SKILL.md) 调用，不要直接开。

## 原则

二十一个短 skill，一条原则一个。`poteto-mode` 在开头内联索引并读一遍。独立文件是为了别的 skill 能按名字引用，以及索引能链到完整规则。

<details>
<summary>全部二十一条原则</summary>

| principle | group | rule |
|---|---|---|
| [laziness-protocol](./skills/principle-laziness-protocol/SKILL.md) | core | Bias toward deletion and the smallest change that solves the problem. |
| [foundational-thinking](./skills/principle-foundational-thinking/SKILL.md) | core | Apply before writing logic: choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share. Get the data structures right so downstream code becomes obvious. |
| [redesign-from-first-principles](./skills/principle-redesign-from-first-principles/SKILL.md) | core | Redesign as if the requirement had been a foundational assumption from day one, instead of bolting it on. |
| [subtract-before-you-add](./skills/principle-subtract-before-you-add/SKILL.md) | core | Remove dead weight, redundant validators, and stub references first, then build on the simpler base. |
| [minimize-reader-load](./skills/principle-minimize-reader-load/SKILL.md) | core | Count layers between question and answer, and hidden state in the reader's head; collapse one-caller wrappers and shrink mutable scope. |
| [outcome-oriented-execution](./skills/principle-outcome-oriented-execution/SKILL.md) | core | Apply during planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture; don't preserve smooth intermediate states with throwaway compatibility code. |
| [experience-first](./skills/principle-experience-first/SKILL.md) | core | Choose user delight over implementation convenience; ship fewer polished features over more rough ones. |
| [exhaust-the-design-space](./skills/principle-exhaust-the-design-space/SKILL.md) | core | Build 2-3 competing prototypes and compare side by side before committing. |
| [build-the-lever](./skills/principle-build-the-lever/SKILL.md) | core | Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks. Build the tool that does it or proves it (codemod, script, generator, or a skill your subagents follow) instead of working by hand. The tool is the artifact a reviewer can rerun. |
| [model-the-domain](./skills/principle-model-the-domain/SKILL.md) | architecture | Encode the domain in a structure instead of scattered conditionals. |
| [boundary-discipline](./skills/principle-boundary-discipline/SKILL.md) | architecture | Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions. |
| [type-system-discipline](./skills/principle-type-system-discipline/SKILL.md) | architecture | Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, refuse to lie to the compiler, exhaust variants, derive from authoritative schemas. |
| [make-operations-idempotent](./skills/principle-make-operations-idempotent/SKILL.md) | architecture | Converge to the same end state regardless of partial prior runs. |
| [migrate-callers-then-delete-legacy-apis](./skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | architecture | Migrate callers and delete the old API in the same wave instead of preserving compatibility layers. |
| [separate-before-serializing-shared-state](./skills/principle-separate-before-serializing-shared-state/SKILL.md) | architecture | Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant. |
| [prove-it-works](./skills/principle-prove-it-works/SKILL.md) | verification | Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'. |
| [fix-root-causes](./skills/principle-fix-root-causes/SKILL.md) | verification | Trace each symptom to its root cause and fix it there; reproduce first, ask why until you reach it, resist nil-check guards that silence crashes. |
| [sequence-verifiable-units](./skills/principle-sequence-verifiable-units/SKILL.md) | verification | Apply to multi-step work (sweeps, migrations, runs of similar edits) and to how you stack commits and PRs. Break work into small units that each end in a verifiable state, check each before the next, and order delivery so the sequence proves itself to a reviewer. |
| [guard-the-context-window](./skills/principle-guard-the-context-window/SKILL.md) | delegation | Route bulk to subagents; keep summaries in the main thread, not raw payloads. |
| [never-block-on-the-human](./skills/principle-never-block-on-the-human/SKILL.md) | delegation | Proceed, present the result, let the human course-correct after the fact; reserve confirmation for irreversible actions. |
| [encode-lessons-in-structure](./skills/principle-encode-lessons-in-structure/SKILL.md) | meta | Encode the rule as a lint, metadata flag, runtime check, or script instead of more text. |

</details>

## 本移植未带的东西

Cursor 版 pstack 的 `poteto-mode` 还引用过这些，这里没有打包：

- `/deslop`、`control-cli`、`control-ui` 在 `cursor-team-kit` 里。这里用 `/unslop`、`/no-comments`，应用自己去点、去跑。
- 独立核验是 `spawn_subagent`，`subagent_type` 为 `pstack:independent-verifier`。toml 里是已探测到的 slug 时另传 `model`，否则省略 `model`。不是 Cursor Cloud Agent。见 [HARNESS.md](./HARNESS.md)。
- Graphite `gt` 可选。没有就用 `gh` 和 git。
- Benny 的 Cursor 包在 `automations/benny/skills/`，是 **upstream reference**。现场 grok 合同在 [`automations/benny-grok/`](./automations/benny-grok/)（enable 后 `/benny-triage`）。不是本插件的 plugin hooks。

## 为什么没有规划技能

grok-build 自带 `plan` agent 类型。pstack 仍然默认不规划。最好的规格是代码。如果确实要计划，[`/poteto-mode`](./skills/poteto-mode/SKILL.md) 覆盖得了。

## 做成你自己的

`poteto-mode` 是 poteto 的风格。你可以不要一模一样的那套。

输入 [`/automate-me`](./skills/automate-me/SKILL.md)。它从你最近的 transcript 里挖习惯，起草一个 `<your-name>-mode` skill，底层仍走 pstack。pstack 当底座，旁边多一个你自己的路由 skill。

Grok Build 默认仍是 `grok-4.6` 加按角色的 effort。只有要改的时候才跑 [`/setup-pstack`](./skills/setup-pstack/SKILL.md)。它探测 `spawn_subagent` 能收的 slug，按角色问 reasoning effort，写入 `~/.grok/pstack-models.toml` 和由本插件管理的 `~/.grok/roles/pstack:<role>.toml`。它不会写 `~/.cursor/rules`。这不是 Cursor 插件。

## 自动化

仓库里还有一份休眠的 [benny automation pack](./automations/benny/)。Cursor `skills/` 是 **upstream reference**。现场 grok 合同在 [`automations/benny-grok/`](./automations/benny-grok/)。enable pstack 后用 `/benny-triage`。不要给 `plugin.json` 加 `hooks`。

可以 fork，可以改，欢迎 PR。

## 许可

MIT.

上游是 official pstack / poteto（Lauren Tan）。本仓库是 **`tommy-ca/pstack`**，适配自 [aa2246740/pstack-grokbuild](https://github.com/aa2246740/pstack-grokbuild)。
