# LLM Wiki reference-derived contracts - OpenSpec additions

## ADDED Requirements

### Requirement: R-WIKI-001 Versioned, replay-safe source identity

Each captured source revision SHALL carry content SHA-256, stable source identifier and capture location. A successful revision SHALL not be overwritten by a different byte sequence. An exact repeated input SHALL be idempotent. Filename alone SHALL NOT be treated as a globally unique provenance identity.

#### Scenario: Same basename with distinct content

- **GIVEN** a successfully captured `spec.md` containing bytes A
- **WHEN** a second `spec.md` contains bytes B where B differs from A
- **THEN** the original bytes remain A and the conflict is explicitly reported
- **AND** a future content-addressed capture design may admit B under a *different revision identity*, never silently replace A

#### Scenario: Replay

- **GIVEN** bytes A were successfully captured
- **WHEN** bytes A are captured again under the same source identifier
- **THEN** no duplicate revision or promotion event is recorded

### Requirement: R-WIKI-002 Separate source, candidate and published authority

Raw evidence, human/LLM candidate, validated article and derived projection SHALL be distinguishable in identity, storage and privileges. Model-generated candidates SHALL NOT write directly to QStack's `knowledge/`, `knowledge/operations.jsonl` or bypass PStack's explicit review of curated pages.

#### Scenario: External compiler proposes a page

- **GIVEN** an Atomicstrata candidate includes valid Markdown and extracted sources
- **WHEN** it is transferred to PStack or QStack
- **THEN** it remains a quarantined candidate until the receiving publisher independently validates source pins, rights, schema, review and target-version preconditions
- **AND** a reviewer may reject without altering the last approved page

### Requirement: R-WIKI-003 Typed contracts are explicit and versioned

Typed candidates SHALL be checked against a schema version and declared kind. A runtime that does not implement candidate type validation SHALL report it as `UNTESTED` or `GAP`, not as a successful validation. Legacy Markdown without frontmatter SHALL NOT be silently reclassified as verified typed content.

#### Scenario: Invalid candidate envelope

- **GIVEN** the candidate lacks an evidence revision or contains an unknown lifecycle state
- **WHEN** schema validation runs
- **THEN** admission is rejected
- **AND** the legacy baseline's structural link validator cannot substitute for typed validation

### Requirement: R-WIKI-004 Traceable citation, not inferred truth

Claims SHALL bind a source revision and, when precise citation is available, a bounded span. A syntactically valid reference establishes resolvability, **not** factual entailment. Approval for high-impact claims SHALL obey QStack `human_ack` and independent-source requirements.

#### Scenario: Resolvable but unsupported claim

- **GIVEN** a generated assertion links to a real source and valid line interval
- **WHEN** the source text does not support the asserted conclusion
- **THEN** link resolution may pass but truth/entailment remains unverified
- **AND** the candidate cannot acquire a `supported` assertion from citation validity alone

### Requirement: R-WIKI-005 Candidate decisions are fail-closed and freshness-checked

Candidates SHALL have explicit review reasons and terminal decisions; unrecognized policy modes and stale expected source or target versions SHALL fail closed. Approval SHALL compare the recorded proposal against the current approved target and candidate bytes, preventing stale or modified-body promotion.

#### Scenario: Stale approval

- **GIVEN** a staged candidate binds source digest S and expected page revision P
- **WHEN** source S changes or the published page is now P2
- **THEN** approval rejects or returns to review rather than overwriting P2

### Requirement: R-WIKI-006 Search/index/graph are disposable derivations

Index and graph caches SHALL expose derivation identity and shall be rebuilt after changes to source page bytes, schema or eligible relations. A stale cache SHALL NOT grant write authority, impersonate fresh evidence or substitute for canonical Markdown. Rebuilds affecting one wiki space SHALL be serialized or otherwise equivalent to a serial history.

#### Scenario: Restart with stale graph cache

- **GIVEN** cached graph revision G was built from corpus H1
- **WHEN** a process restarts against corpus H2, H2 != H1
- **THEN** the system invalidates/rebuilds G or reports it stale
- **AND** search output does not become a publishing authorization

### Requirement: R-WIKI-007 No unsafe local file escape

A wiki ingest/index check SHALL refuse local page references resolving outside the admitted wiki root and must not follow attacker-controlled symlinks for captured source writes. Every claimed guarantee SHALL be backed by adversarial tests for the threat model; a `Path.is_symlink` preflight is not a defense against all concurrent directory swaps.

#### Scenario: Local link traversal

- **GIVEN** a wiki page links to `../../../../secrets`
- **WHEN** structural validation runs
- **THEN** the link is rejected even if the target happens to exist

### Requirement: R-WIKI-008 Rebuild and crash recovery are honest

Index writes SHALL be atomic where supported; raw capture and activity journal persistence SHALL either use a recoverable transactional protocol or be documented and verified as independently recoverable steps. Unknown future state schema versions SHALL fail closed rather than be overwritten.

#### Scenario: Crash between capture and event

- **GIVEN** source bytes were written but log append did not occur
- **WHEN** the wiki is reopened
- **THEN** repair must detect/reconcile the incomplete event or surface a BLOCKED/FAIL status
- **AND** no report asserts a successful atomic source+log transaction

### Requirement: R-WIKI-009 Orthogonal epistemic roles and provenance

Sources (what was observed), concepts/articles (what was synthesized) and query results (answers derived from current context) SHALL retain distinct provenance roles even if represented by shared Markdown or typed envelopes. Query answers SHALL not be automatically promoted to source truth.

#### Scenario: Query result references an inferred concept

- **GIVEN** an answer was synthesized from existing pages
- **WHEN** it is saved or indexed
- **THEN** the content is typed as query-derived or equivalent, its ancestry is retained
- **AND** it does not silently become a primary source revision

### Requirement: R-WIKI-010 Evidence labels and opt-in boundaries

The canonical baseline SHALL run without external wiki engines, providers or services. External candidate compilation and search remain optional until separately accepted. Verdict reduction SHALL preserve `FAIL > BLOCKED > UNTESTED > PASS`; static/docs success cannot be upgraded to observed-live, external model, or formal proof.

#### Scenario: Missing Rust binary or TLC

- **GIVEN** the optional checker is unavailable
- **WHEN** a release verifier is asked for complete formal and reference-engine parity
- **THEN** it reports `BLOCKED` or `UNTESTED` for that lane
- **AND** retained Python offline tests may still report PASS independently
