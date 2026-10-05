---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Can critique architecture. Use why for motivation."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Two modes:

1. **Explain** (default). Explore the codebase and produce a clear explanation
2. **Critique.** Explain first, then spawn multiple models to independently identify architectural issues

## Explain Mode

### Step 1. Assess Complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. One explainer explores and explains in a single pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): spawn parallel explorers first, then hand off to the explainer. Go to Step 2a.

When in doubt, take the simple path.

For enforcement or runtime questions (sandbox, hooks, multiplexer, kernel policy), split **declared config** from **this process**. Nested `inspect` is a new process. It is not evidence of the parent TUI's profile.

### Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct slice of the subsystem. Spawn all explorers in a single parent turn using the current host's subagent primitive (Grok: `spawn_subagent`, Antigravity: `invoke_subagent`, Codex: `spawn_agent`, OMP: `pi_spawn`, OpenCode: `task.spawn` per `references/*-tools.md`). Join with the host's join primitive.

- `subagent_type` / `Role`: `pstack:how-explorer` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md)). Builtin `explore` is the later fallback when this plugin agent is unknown (HARNESS Skill order).
- `model`: toml key `how-explorer` per `../setup-pstack/references/resolve-model.md` (or host configuration). Missing key omits; absent config sends host default (`grok-4.6` on Grok, `pro` on Antigravity). Do not send `reasoning_effort`.

Each explorer gets the prompt in `references/explorer-prompt.md` with its angle filled in. Then go to Step 3.

### Step 2b. Direct Explain (simple questions)

Spawn a single child using the host's subagent primitive that explores and explains in one pass:

- `subagent_type` / `Role`: `pstack:how-explainer` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md))
- `model`: toml key `how-explainer` per `../setup-pstack/references/resolve-model.md` (or host configuration). Missing key omits; absent config sends host default (`grok-4.6` on Grok, `pro` on Antigravity). Do not send `reasoning_effort`.

Build its prompt from `references/explainer-prompt.md` without the explorer-findings section. Go to Step 4.

### Step 3. Synthesize (complex questions only)

Once all explorers have returned, spawn one child using the host's subagent primitive to synthesize their findings into one explanation:

- `subagent_type` / `Role`: `pstack:how-explainer` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md))
- `model`: toml key `how-explainer` per `../setup-pstack/references/resolve-model.md` (or host configuration). Missing key omits; absent config sends host default (`grok-4.6` on Grok, `pro` on Antigravity). Do not send `reasoning_effort`.

Build its prompt from `references/explainer-prompt.md` with every explorer's findings filled in.

### Step 4. Present

Present the explainer's output to the user. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

### Output Format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.

**Gotchas (Grok sandbox).** Config `[sandbox] profile` and nested `grok inspect` are not this TUI. Measure `argv`, `__GROK_INSIDE_BWRAP`, session `summary.json` `sandbox_profile`, `/proc/self/mountinfo`, and `~/.grok/sandbox-events.jsonl`.

**Gotchas (skill provenance).** Resolve the symlink and inspect `source.path` before calling a `~/.grok/skills` path a personal skill. A `collidesWith` row is not provenance. Do not copy plugin skills into `~/.grok/skills`.

## Critique Mode

Triggered when the user asks for architectural issues, problems, or improvements, not just understanding.

### Step 1. Explain First

Run the full explain flow above (Steps 1-4). You must understand the architecture before critiquing it.

### Step 2. Spawn Critics

After the explanation is complete, spawn critics using the host's subagent primitive (from toml array `how-critics` or host configuration), all in a single message. If configuration is absent, spawn **one** critic and send host default (`grok-4.6` on Grok, `pro` on Antigravity). Do not invent a multi-model panel.

For each critic:
- `subagent_type` / `Role`: `pstack:how-critics` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md))
- `model`: that array entry when it is a detected slug; omit when the entry is `inherit-parent`/`auto`. Configuration absent: host default (`grok-4.6` on Grok, `pro` on Antigravity). Do not send `reasoning_effort`.

Read `references/critic-prompt.md` for the prompt template. Each critic gets:
1. The explanation from Step 1 (so they don't re-explore)
2. The relevant file paths (so they can read the actual code)
3. The architectural critique rubric from `references/critique-rubric.md`

### Step 3. Lead Judgment

Same framework as the interrogate skill. You're a pragmatic lead, not an aggregator.

Categorize findings:
- **Act on.** Architectural problems worth fixing now
- **Consider.** Real concerns, but the cost/benefit is unclear
- **Noted.** Valid observations, low priority
- **Dismissed.** Wrong, missing context, or style preference

Present the explanation first (from Step 1), then the critique verdict below it. The explanation should stand on its own; someone who just wants to understand the system shouldn't wade through critique.
