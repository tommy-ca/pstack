# Grok transcript location

Grok adapter surface. Resolve the active transcript on Grok Build only.

Use `~/.grok/sessions/<urlencoded-cwd>/<session-id>/chat_history.jsonl`. Sidecars in that directory include `summary.json`, `events.jsonl`, and `subagents/`. Confirm the first user `user_query` matches this conversation's opener. Do not glob Cursor `agent-transcripts/` or `~/.cursor/projects/*/`.

```bash
ls -t ~/.grok/sessions/*/"$GROK_SESSION_ID"/chat_history.jsonl 2>/dev/null | head -5
```
