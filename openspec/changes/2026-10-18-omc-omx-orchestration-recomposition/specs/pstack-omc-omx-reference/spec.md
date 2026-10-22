# pstack-omc-omx-reference: formal reference extraction

## ADDED Requirements

### Requirement: Source references are immutable and classified
Every adopted OMC/OMX semantic building block MUST record repository, immutable commit, file path, observed code behavior, target contract owner, status (preserve, adapt, exclude, gap) and evidence level. Source review MUST be differentiated from executable native harness conformance.

#### Scenario: OMC graph contract changes upstream
- **GIVEN** a new upstream commit changes graph schema or scheduler
- **WHEN** the source parity check runs
- **THEN** it reports the changed source and impacted requirements
- **AND** it does not silently migrate the normative target pin.

### Requirement: Reference designs do not expand portable capability IDs by implication
Reference concepts including effect policy, graph sealing, workpool, goal ledger and team mode are internal domain semantics or composed methods. A new public capability identifier MUST require its own reviewed behavioral postcondition and portable proof; it MUST NOT be added merely because a reference implementation exposes it.

#### Scenario: OMC exposes a new graph node kind
- **GIVEN** reference source adds a native graph kind
- **WHEN** crosswalk is updated
- **THEN** it is classified under the owning design contract or as an unsupported host feature
- **AND** no new pstack capability enum is created automatically.
