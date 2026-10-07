## MODIFIED Requirements

### Requirement: Spawn types are plugin-qualified

Feature: pstack-grok-host
Rule: grok 1.0.13 registers plugin:name

Shipped skills and the Grok host mapping (`skills/poteto-mode/references/grok-tools.md`) MUST set `subagent_type` to `pstack:<role-key>` (`pstack:how-explorer`, `pstack:feature`, `pstack:poteto-agent`, `pstack:comment-sicko`, `pstack:independent-verifier`). They MUST NOT treat the bare stem as the TUI type. Toml model keys stay the bare role key. Effort overlays MUST use `~/.grok/roles/pstack:<key>.toml`.

#### Scenario: Bare how-explorer is unknown

- **GIVEN** pstack is in `[plugins].enabled`
- **WHEN** a parent spawns a how explorer
- **THEN** `subagent_type` is `pstack:how-explorer`
- **AND** inspect `.agents[].name` includes `pstack:how-explorer`
- **AND** it does not include bare `how-explorer`
