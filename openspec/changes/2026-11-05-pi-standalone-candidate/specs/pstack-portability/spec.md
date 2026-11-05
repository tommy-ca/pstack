# Delta: PStack portability — standalone Pi candidate

## ADDED Requirements

### Requirement: Standalone Pi is not OMP

A standalone Pi port MUST use its own declared candidate identity and native tool mapping. It MUST NOT reuse OMP process, session, RPC or evidence paths as observed Pi proof. Candidate identity MUST NOT be inserted into the six built-in host targets before native packaging and proof pass.

#### Scenario: Candidate profile without native proof
- **GIVEN** Pi core and extension documentation but no installed Pi runtime
- **WHEN** the adapter map is reviewed
- **THEN** each mapping has static-only or unverified status
- **AND** no Pi receipt is promoted to observed live
- **AND** the existing six shipped hosts remain unchanged

### Requirement: Minimal Pi extension ownership

Native Pi MUST own its MCP, codemode, tool-search, sessions and model/tool lifecycles. Exactly one delegated-agent engine SHOULD be active for PStack execution. Other extensions MUST be justified by a required capability or measured workload. Workflow policy MUST stay with canonical PStack semantics.

#### Scenario: Competing delegate engines
- **GIVEN** both pi-subagents and pi-dynamic-workflows are enabled
- **WHEN** the Pi/PStack profile is composed
- **THEN** the default profile MUST refuse ambiguous delegation ownership or disable the nonselected engine
- **AND** must not create two task ledgers

### Requirement: Sandbox claims are evidence-bound

A sandbox extension's installed state MUST NOT imply enabled task confinement. Parent, child and background actor profiles MUST be measured independently where applicable. A permission tool-hook or trusted extension exception MUST NOT be reported as an OS boundary.

#### Scenario: Child trusted-tool bypass
- **GIVEN** a read-only confined child and a trusted extension tool that can mutate files
- **WHEN** the child attempts the mutation
- **THEN** the verifier MUST record actual admission and filesystem effects
- **AND** any mutation outside policy MUST FAIL the isolation claim
- **AND** a refusal or untested tool MUST NOT be promoted to PASS

### Requirement: Functional and formal verification reuse existing levers

The Pi candidate MUST reuse the existing three-tier verification skill machinery, receipt evidence, and create/maintain formal-verification procedures. No new generic proof registry may be introduced. Formal model checking MUST identify code correspondence, bounds, version, sync commit and at least one failing mutant.

#### Scenario: Model passes but code diverged
- **GIVEN** a formal model verified against a prior revision
- **WHEN** covered implementation code changes
- **THEN** the result MUST remain stale/unverified until reviewed and rerun
- **AND** completion MUST NOT be claimed from the old model PASS

### Requirement: LLMWiki records candidate status truthfully

The Pi semantic crosswalk MUST be curated in the existing self-contained .llm-wiki and keep raw source ingestion separate from authored knowledge. Sources MAY be cited externally in a candidate page but MUST NOT be represented as locally ingested immutable sources without a digest-bearing ingest record.

#### Scenario: External citation without local ingest
- **GIVEN** a candidate Pi mapping with public documentation links
- **WHEN** the LLMWiki is checked
- **THEN** the article identifies the citation as external/provisional
- **AND** no raw source digest or runtime conformance is invented
