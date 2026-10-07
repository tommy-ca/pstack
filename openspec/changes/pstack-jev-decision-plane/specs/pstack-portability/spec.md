# pstack-portability Specification

## ADDED Requirements

### Requirement: Optional semantic decision providers do not expand the portability floor

A pstack port MAY integrate an optional bounded semantic decision provider such as Jev above the portable core.

The provider MUST NOT become a required harness capability, a new workflow runtime, or a source of canonical playbook semantics. Provider-specific SDK/API syntax MUST stop at an optional provider boundary.

When the provider is absent, disabled, unavailable, or below a calibrated confidence threshold, canonical pstack routing and verification MUST continue without semantic loss.

Hard safety/autonomy policy and required human gates MUST remain authoritative over provider output.

#### Scenario: harness has no decision provider

- **GIVEN** a harness satisfies the portable capability and conformance requirements
- **AND** no optional semantic decision provider is configured
- **WHEN** harness support state is derived
- **THEN** the harness may still reach `supported`
- **AND** pstack follows its existing router/playbook behavior
