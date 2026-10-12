---
name: principle-guard-the-context-window
description: "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads."
disable-model-invocation: true
---

# Guard the Context Window

The context window is finite and non-renewable within a session. Every token should be worth its cost.

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Isolate large payloads.** Route verbose outputs, screenshots, and large documents to subagents. The main context gets summaries, not raw data.
- **Keep frequently used content inline.** Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time.
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.

## Measure the work, not the opening tokens

Deferring a payload pays only when the task's total work is no worse: the bytes left in context,
the reads, the re-reads of a file already read, and the searches retried after an empty result. A
smaller first response proves nothing by itself.

- Report the counts you measured and name the ones you did not; never present a token reduction as
  efficiency evidence.
- Keep the retrieval identifier with every summary: the path, symbol, or query that restores the
  payload in one call. Dropping it causes the re-reads and the retried searches.
- Disclose truncation: what was cut and how to get the rest.
- When a subagent owns a payload, the main thread keeps its summary and does not re-read the raw
  output.

## Load an optional domain overlay only for a declared capability

UI, i18n, release, archive, browser, performance and forge-stack guidance belongs to the project
that has the capability, not to every task.

- Name the positive predicate first: the project declares the capability and the task's domain or
  explicit request matches.
- Capability absent leaves the pack unloaded. A pack requested anyway is reported `BLOCKED` or
  `UNTESTED`, never silently skipped and never `PASS`.
- A prohibited context (docs-only, backend-only, read-only, single-locale) deactivates the pack
  even when the capability exists.
- Each pack states its condition in its first line, so it can be rejected unread.
