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
