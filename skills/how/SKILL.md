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

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. One explainer explores and explains in a single pass, built from `references/explainer-prompt.md` without the explorer-findings section. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): spawn parallel explorers first, then hand off to the explainer. Go to Step 2a.

When in doubt, take the simple path.

For enforcement or runtime questions (sandbox, hooks, multiplexer, kernel policy), split **declared config** from **this process**. Nested `inspect` is a new process. It is not evidence of the parent TUI's profile.

### Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 angles, each a distinct slice of the subsystem. Spawn all explorers in a single parent turn using the current host's agent spawn capability (`agent.spawn`), each with `references/explorer-prompt.md` and its angle filled in. Join with the host's join capability (`agent.join`).

- `subagent_type` / `Role`: `pstack:how-explorer` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md)). Builtin `explore` is the later fallback when this plugin agent is unknown (HARNESS Skill order).
- `model`: toml key `how-explorer` per `../setup-pstack/SKILL.md` (or host configuration). Missing key omits; absent config resolves the host default model from the active profile. Do not send `reasoning_effort`.

Then go to Step 3.

### Step 2b. Direct Explain (simple questions)

Spawn a single child using the host's agent spawn capability (`agent.spawn`) that explores and explains in one pass:

- `subagent_type` / `Role`: `pstack:how-explainer` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md))
- `model`: toml key `how-explainer` per `../setup-pstack/SKILL.md` (or host configuration). Missing key omits; absent config resolves the host default model from the active profile. Do not send `reasoning_effort`.

Build its prompt from `references/explainer-prompt.md` without the explorer-findings section. Go to Step 4.

### Step 3. Synthesize (complex questions only)

Once all explorers have returned, spawn one child using the host's agent spawn capability (`agent.spawn`) to synthesize their findings into one explanation:

- `subagent_type` / `Role`: `pstack:how-explainer` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md))
- `model`: toml key `how-explainer` per `../setup-pstack/SKILL.md` (or host configuration). Missing key omits; absent config resolves the host default model from the active profile. Do not send `reasoning_effort`.

Build its prompt from `references/explainer-prompt.md` with every explorer's findings filled in.

### Step 4. Present

Present the explainer's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

### Output Format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.

**Gotchas (sandbox).** The active host's configured sandbox profile is not this TUI's process. Measure this process's `argv`, session `summary.json` `sandbox_profile`, and `/proc/self/mountinfo`; host-specific probes and the sandbox event log belong in the active host's `../poteto-mode/references/<host>-tools.md`, when it has a sandbox section. A nested host inspection command does not observe this process.

**Gotchas (skill provenance).** Resolve the symlink and inspect `source.path` before calling a path in the active host's personal skill directory a personal skill; the host reference names that directory. A `collidesWith` row is not provenance. Do not copy plugin skills into it.

## Critique Mode

Triggered when the user asks for architectural issues, problems, or improvements, not just understanding.

### Step 1. Explain First

Run the full explain flow above (Steps 1-4). You must understand the architecture before critiquing it.

### Step 2. Spawn Critics

After the explanation is complete, spawn critics using the host's `agent.spawn` primitive (from toml array `how-critics` or host configuration), all in a single message. If configuration is absent, spawn **one** critic using the host default model resolved from the active profile. Do not invent a multi-model panel.

For each critic:
- `subagent_type` / `Role`: `pstack:how-critics` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md))
- `model`: that array entry when it is a detected slug; omit when the entry is `inherit-parent`/`auto`. Configuration absent: host default model resolved from the active profile. Do not send `reasoning_effort` unless supported.

Read `references/critic-prompt.md` for the prompt template. Each critic gets:
1. The explanation from Step 1 (so they don't re-explore)
2. The relevant file paths (so they can read the actual code)
3. The architectural critique rubric from `references/critique-rubric.md`

### Step 3. Critique Contracts

A critique is advisory, so it owes the reader the evidence behind each finding:

- **Authority, not hearsay.** Name the resolved base and the head commit you read, and cite
  the immutable commit SHA and path the answer rests on. A stale document, an unmerged
  branch description, or another skill's summary is a lead, not authority.
- **Consumers before deletion or moves.** Before recommending that a seam be deleted, moved,
  or collapsed, name the consumers you searched — in-repo call sites, tests, docs, registry
  or dynamic lookup by name, published API, plugin, config, and route seams — and which ones
  you could not rule out. No in-repo reference is not evidence of deletability, and
  `Nothing references it` is not consumer reachability.
- **A behavior pin, not a compile.** State the observable behavior the move preserves and
  the evidence for it. A typecheck or a green suite that never exercised the path is not a
  behavior pin; where behavior changes, name the delta and who it affects.
- **Net maintained obligation.** Say what the change removes as an obligation — a concept,
  branch, mode, wrapper, config knob, or error path nobody has to maintain — rather than how
  many lines it moves.
- **Order findings by observable impact** — what a user or operator can observe:
  correctness, data and security effects, lifecycle and consumer breakage, then structure,
  then style. Each finding gets a disposition and the recheck that would settle it.

### Step 4. Lead Judgment

Same framework as the interrogate skill. You're a pragmatic lead, not an aggregator.

Categorize findings:
- **Act on.** Architectural problems worth fixing now
- **Consider.** Real concerns, but the cost/benefit is unclear
- **Noted.** Valid observations, low priority
- **Dismissed.** Wrong, missing context, or style preference

Present the explanation first (from Step 1), then the critique verdict below it. The explanation should stand on its own; someone who just wants to understand the system shouldn't wade through critique.
