# Benny on Grok Build

`automations/benny/skills/` is the **upstream reference** for marker names and atomic intent. These grok files are the live contract. They are not slash skills. They are not pstack plugin hooks.

Grok has no Slack channel auto-start. You pass `args.thread_url` into a workflow. Overnight waits use `/loop`, which expands to `scheduler_create`. Fan-out uses `spawn_subagent` with `pstack:<role>`.

## Copy into a target repository

```bash
mkdir -p .grok/hooks .grok/workflows .grok/benny
cp automations/benny/grok/hooks/hooks.json .grok/hooks/benny.json
cp automations/benny/grok/bin/fail-closed.sh .grok/hooks/bin/fail-closed.sh
chmod +x .grok/hooks/bin/fail-closed.sh
cp automations/benny/grok/workflows/*.rhai .grok/workflows/
cp automations/benny/grok/triage.md automations/benny/grok/repro.md .grok/benny/
cp automations/benny/templates/configuration.example.yaml .grok/benny/configuration.yaml
```

Fix the hook `command` path so it is relative to `.grok/hooks/benny.json` (use `bin/fail-closed.sh` next to that JSON, or copy `bin/` beside it). Trust the folder (`/hooks-trust` or `--trust`) or project hooks stay skipped.

Keep secrets out of YAML. User config stays in `.grok/benny/`.

Enable pstack from a host shell. `grok plugin enable pstack`. Spawn `pstack:how-explorer`, not `how-explorer`.

## Run

```text
/workflow benny-triage {"thread_url":"https://slack.com/archives/..."}
/workflow benny-repro {"thread_url":"https://slack.com/archives/..."}
```

Workflows read `automations/benny/grok/triage.md` and `repro.md`. Copy those files with the workflows. The parent posts one frozen-thread reply. Never a source-channel root message. That freeze is prompt-enforced. The copied hook only denies merge and force-push.

`/loop` with a checkable predicate expands to `scheduler_create` (min 60s, new turn).
