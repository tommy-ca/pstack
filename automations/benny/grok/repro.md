# Live grok repro

This file is the live coordinator. `automations/benny/skills/` is the **upstream reference** for marker names and atomic intent. Do not use it as the runbook.

## Input

`args.thread_url` is the Slack permalink. Freeze source channel and root message id from that URL. Load `.grok/benny/configuration.yaml`. Stop if the config is missing.

## Run

Parent session only. `MAX_SUBAGENT_DEPTH` is 1.

1. Read the frozen thread. Proceed only for a trusted `[benny:bug]` or `[benny:performance]` from the configured triage identity. Stop for `[benny:other]`, a missing verdict, or an untrusted author.
2. Stop if a person already owns the fix. If an existing PR or commit may fix it, verify through the real UI twice. Do not author a competing diff.
3. Reproduce the discriminating symptom twice through the real UI. A unit test or injected state is not a repro. For code, `spawn_subagent` with `subagent_type` `pstack:feature`. For a second check, `pstack:independent-verifier`. Do not send `reasoning_effort`. Children get no Slack write tools.
4. Open a draft pull request only after before-and-after UI proof. Never merge or deploy. The copied hook denies `gh pr merge` and force-push.
5. Overnight waits use `/loop` → `scheduler_create`.

The parent is the only Slack poster. Never post a source-channel root message.
