# pstack-portability delta: OMC/OMX execution contract

## ADDED Requirements

### Requirement: External host and child runtime authority are disjoint
A selected host MUST own program graph revision, work admission, attempts and acceptance. OMC/OMX native team, goal or graph runtime MAY own bounded child execution only. No child API or internal filesystem may be treated as a universal host-owned mutation surface. A standalone OMC-derived host MUST exclusively own its namespace.

#### Scenario: OMX team completes a task
- **GIVEN** an OMX Team API terminal transition inside one parent attempt
- **WHEN** the parent host receives its result
- **THEN** it retains artifact and attempt provenance
- **AND** it independently verifies and accepts the parent work.

### Requirement: Sealed executable graphs preserve integrity and effect policies
An executable graph MUST be validated and revision-bound before dispatch. A sealed descriptor's digest MUST be checked independently of its JSON Schema shape. Agent/command nodes MUST declare side-effect-free, idempotent with effect ID, or reconcile policies. Back edges MUST be bounded and general arbitrary cycles forbidden.

#### Scenario: recovered graph has a mismatched digest
- **GIVEN** a persisted graph descriptor does not match its declared digest
- **WHEN** a controller attempts to recover execution
- **THEN** it blocks and records a corrupt/mismatched descriptor
- **AND** it does not recompute silently and proceed.

### Requirement: Native mutation uses the owning runtime API
Native team task claims, messages and terminal updates MUST be made through the owning host's supported mutation surface. OMX external interop uses its CLI Team API, not direct writes to .omx/state files; other adapters MUST map equivalent observable postconditions, not pretend the CLI exists elsewhere.

#### Scenario: external OMX broker wants to complete task
- **GIVEN** a broker has read the current task record
- **WHEN** it changes status to completed
- **THEN** it uses the supported claim/version/transition path
- **AND** direct filesystem mutation is not counted as a supported implementation.

### Requirement: Goals and sessions remain distinct
Durable goal/Ultragoal ledgers and active native session goal directives MUST remain separate lifecycle facts. A shell command that prints /goal handoff text MUST NOT claim to have invoked /goal, and goal-complete ledger state MUST NOT establish independently verified program completion.

#### Scenario: durable goal is checkpointed but native session was lost
- **GIVEN** goal artifacts survive and native session liveness is unknown
- **WHEN** a new worker resumes
- **THEN** it rehydrates from accepted artifacts and records native resume or explicit gap
- **AND** does not fabricate an interactive goal state.

### Requirement: Structured verification reports do not prove execution authenticity
Evidence syntax, path confinement, claim token linkage and file freshness MAY reject malformed task reports, but MUST NOT be represented as attestation that commands ran. Exact-revision artifact verification MUST be performed using independent observable tools and recorded in pstack's existing four-plane receipt format.

#### Scenario: a valid JSON evidence file contains a fabricated successful test
- **GIVEN** a task supplies schema-valid completion evidence
- **WHEN** the host evaluates acceptance
- **THEN** it remains unaccepted without actual verification
- **AND** the runtime plane cannot pass solely on the file's content.
