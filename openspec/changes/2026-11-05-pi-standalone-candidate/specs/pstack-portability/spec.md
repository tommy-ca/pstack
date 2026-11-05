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

### Requirement: Pi interactive human decisions do not bypass authorization

The interactive candidate profile SHOULD provide `pi-ask-user` to implement structured `human.ask`. A successful `ask_user` response MUST NOT alone prove `human.gate` or hard permission enforcement. Every effect requiring approval MUST have an independently mediated authorization decision, including child launches and noninteractive/headless modes.

#### Scenario: Noninteractive agent requests unsafe operation
- **GIVEN** a headless Pi run without a permitted human gate
- **WHEN** an agent requests an effect that requires operator consent
- **THEN** execution MUST remain blocked pending separately authenticated authorization
- **AND** an `ask_user` fallback or pre-filled prompt MUST NOT authorize the effect

### Requirement: Delegation extension owns schedules and lifecycle receipts

If installed `pi-subagents` exposes `mission.*`, `schedule.*`, and `subagent_launch`, the adapter MAY bind PStack `schedule` and `monitor` through version-gated primitives, but MUST NOT add a PStack-owned scheduler/mission database. Native proof MUST test permission-denied child launch, legacy background resume refusal, schedule restoration and terminal status without falsely promoting source documentation.

#### Scenario: Permission extension denies workflow child
- **GIVEN** a policy that denies the `subagent_launch` tool action
- **WHEN** a Pi workflow attempts to create that child
- **THEN** the child MUST NOT run and the parent MUST report a blocked outcome
- **AND** no acceptance receipt may record PASS

### Requirement: Sandbox claims are evidence-bound

A sandbox extension's installed state MUST NOT imply enabled task confinement. Parent, child and background actor profiles MUST be measured independently where applicable. A permission tool-hook or trusted extension exception MUST NOT be reported as an OS boundary.

#### Scenario: Credentials and outside-project defaults
- **GIVEN** a newly configured subagent policy with broad file/credential defaults
- **WHEN** a privileged child attempts to read or alter stored credentials or outside-project files
- **THEN** the verifier MUST explicitly check and record the effective policy
- **AND** PStack MUST NOT claim read-only or least-privilege enforcement from the installed sandbox alone

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
