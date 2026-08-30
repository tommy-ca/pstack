# Benny on Grok Build

Cursor Benny stays under `../`. These files are the grok remap. They are not slash skills. They are not pstack plugin hooks.

Grok has no Slack channel auto-start. You pass the thread into a workflow. Overnight waits use `/loop`, which expands to `scheduler_create`.

## Copy into a target repository

```bash
mkdir -p .grok/hooks .grok/workflows .grok/benny
cp automations/benny/grok/hooks/hooks.json .grok/hooks/benny.json
cp automations/benny/grok/bin/fail-closed.sh .grok/hooks/bin/fail-closed.sh
chmod +x .grok/hooks/bin/fail-closed.sh
cp automations/benny/grok/workflows/*.rhai .grok/workflows/
cp automations/benny/templates/configuration.example.yaml .grok/benny/configuration.yaml
```

Fix the hook `command` path so it is relative to `.grok/hooks/benny.json` (use `bin/fail-closed.sh` next to that JSON, or copy `bin/` beside it). Trust the folder (`/hooks-trust` or `--trust`) or project hooks stay skipped.

Keep secrets out of YAML. User config stays in `.grok/benny/`, not inside `automations/benny/`.

Enable pstack from a host shell. `grok plugin enable pstack`. Spawn `pstack:how-explorer`, not `how-explorer`.

## Run

```text
/workflow benny-triage {"thread_url":"https://slack.com/archives/..."}
/workflow benny-repro {"thread_url":"https://slack.com/archives/..."}
```

Keep `automations/benny/skills/` with the workflows. The Rhai files tell the agent to read those SKILL.md files. Copying only `grok/` is not enough.

The workflow agent must follow those operational files. Reply only in the frozen thread. Never post a source-channel root message. That `thread_ts` rule is prompt-enforced. The copied hook only denies merge and force-push. Draft pull requests only. It does not see Slack MCP or `gh pr create`.

`/loop` with a checkable predicate expands to `scheduler_create` (min 60s, new turn).
