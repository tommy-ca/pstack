---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Can critique architecture. Use why for motivation."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Spawn one subagent using role `how-explainer` (resolved via active profile; `subagent_type: "pstack:how-explainer"`) in read-only mode that explores and explains in one pass. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

For complex questions spanning multiple subsystems, spawn parallel explorers using role `how-explorer` (`subagent_type: "pstack:how-explorer"`) across distinct angles before synthesizing. For critique mode, spawn multiple models using role `how-critics` (`subagent_type: "pstack:how-critics"`).

## 2. Present

Present the subagent's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## 3. Critique Contracts

A critique is advisory, so it owes the reader the evidence behind each finding:

- **Authority, not hearsay.** Name the resolved base and the head commit you read, and cite the immutable commit SHA and path the answer rests on. A stale document, an unmerged branch description, or another skill's summary is a lead, not authority.
- **Consumers before deletion or moves.** Before recommending that a seam be deleted, moved, or collapsed, name the consumers you searched (in-repo call sites, tests, docs, registry or dynamic lookup by name, published API, plugin, config, and route seams) and which ones you could not rule out. No in-repo reference is not evidence of deletability, and `Nothing references it` is not consumer reachability.
- **A behavior pin, not a compile.** State the observable behavior the move preserves and the evidence for it. A typecheck or a green suite that never exercised the path is not a behavior pin; where behavior changes, name the delta and who it affects.
- **Net maintained obligation.** Say what the change removes as an obligation (a concept, branch, mode, wrapper, config knob, or error path nobody has to maintain) rather than how many lines it moves.
- **Order findings by observable impact.** Rank by what a user or operator can observe (correctness, data and security effects, lifecycle and consumer breakage, then structure, then style). Each finding gets a disposition and the recheck that would settle it.
