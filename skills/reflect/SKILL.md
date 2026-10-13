---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript.

**Grok Build.** Use `~/.grok/sessions/<urlencoded-cwd>/<session-id>/chat_history.jsonl`. Sidecars in that directory include `summary.json`, `events.jsonl`, and `subagents/`. Confirm the first user `user_query` matches this conversation's opener. Do not glob Cursor `agent-transcripts/` or `~/.cursor/projects/*/`.

**Cursor host.** The system prompt names the workspace `agent-transcripts/` directory. Use that path. Do not glob across `~/.cursor/projects/*/`.

```bash
# Grok Build
ls -t ~/.grok/sessions/*/"$GROK_SESSION_ID"/chat_history.jsonl 2>/dev/null | head -5
# Cursor host
ls -t <agent-transcripts>/*.jsonl <agent-transcripts>/*/*.jsonl <agent-transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Cursor layouts: legacy flat (`<id>.jsonl`), current nested (`<id>/<id>.jsonl`), and subagent (`<parent>/subagents/<child>.jsonl`).

If none matches, pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

One message, three subagent spawn calls. Judgment and divergent lenses use `subagent_type: "pstack:reflect-judgment"`. Tooling uses `subagent_type: "pstack:reflect-tooling"`. [`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md). Resolve `model` per `../setup-pstack/references/resolve-model.md`. Do not send `reasoning_effort` on spawn. Reviewers need MCP access to look up the tickets, chat threads, and observability traces the transcript references. The prompt forbids file writes; the parent applies edits.

| Lens | toml key | Prompt template |
|---|---|---|
| Judgment | `reflect-judgment` | `references/judgment-reviewer.md` |
| Tooling | `reflect-tooling` | `references/tooling-reviewer.md` |
| Divergent | `reflect-judgment` | `references/divergent-reviewer.md` |

Omit `model` on a spawn when that key is `inherit-parent` or `auto`. File absent: send host default model resolved from active profile (omit if rejected). Three lenses are three prompts, not a guessed multi-slug panel.

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their response body.

## 3. Synthesize

One subagent spawn call, `subagent_type: "pstack:reflect-judgment"`, toml key `reflect-judgment` (no toml: host default model resolved from active profile; inherit-parent/`auto`/missing key: omit `model`). Do not send `reasoning_effort` on spawn. The synthesizer's quality check includes spot-verifying citations, which can require MCP access. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Those are tracker submissions, not skill edits. Only the Accepted list waits for approval.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Grok Build's `/create-skill` and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `create-skill` and run its description-optimization loop.
- `new skill via create-skill: <kebab-name>`: hand creation to `create-skill`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
