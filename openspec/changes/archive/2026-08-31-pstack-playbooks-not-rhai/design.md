## Context

Grok 1.0.13 `PluginManifest` has no `workflows` field. User-guide 05-configuration.md discovers Rhai from `<repo>/.grok/workflows/` and `~/.grok/workflows/`. Built-ins win over project names. pstack already ships `/poteto-mode` as the playbook router. Benny has two optional `.rhai` files that `/workflow` will not see unless copied into a target `.grok/workflows/`.

In-force ADRs 0003 and 0004 cover plugin skills and Benny live path. None covers Rhai.

## Goals / Non-Goals

**Goals:**
- Record that playbooks stay markdown.
- Forbid cloning them into plugin Rhai.
- Keep Benny `.rhai` as optional copies.

**Non-Goals:**
- Deleting Benny `.rhai`.
- Implementing 22 Rhai playbooks.
- Adding a fake `workflows` key to `plugin.json`.

## Decisions

1. **Do not port playbooks to Rhai.** `/poteto-mode` matches a playbook and copies steps into todos. Rhai cannot do that match, cannot use `disable-model-invocation`, and does not load from plugin install.
2. **Rhai earns a place only in a target repo.** A bounded fan-out pipeline (`review-changes`, a verify panel) may live in that repo's `.grok/workflows/`. It is not a pstack plugin component.
3. **Benny `.rhai` stays optional.** Slash `/benny-triage` is the enable path. The script is a copy recipe for operators who already use `/workflow`.

## Risks / Trade-offs

- [Operators expect `/workflow feature`] -> Docs and this spec say no. Use `/poteto-mode`.
- [Benny `.rhai` looks like a precedent] -> Tests distinguish playbooks dir vs optional copies.
- [`thread` is reserved in Rhai] -> Already remapped to `thread_url` on Benny scripts.

## Migration Plan

No runtime migration. New ADR 0005. Tests fail if someone adds `playbooks/*.rhai` or `.grok/workflows/`.

## Open Questions

None. A later target-repo workflow is out of this plugin.
