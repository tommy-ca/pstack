# LLM Wiki Schema

## Ownership Rules

| Path | Owner | Rule |
|------|-------|------|
| raw/** | extension | immutable after capture |
| wiki/** | model + user | editable knowledge pages |
| meta/* | extension | auto-generated |
| . | human + explicit request | operating rules |