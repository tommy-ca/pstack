# Cursor PStack 0.15.42 → Portable PStack: Audited Upstream Delta

**Status:** Research and intent audit. Linked to Epic #1344 and Issue #1345.

## Source Revision Contract

| Property | Verified Input |
|---|---|
| Port base | `tommy-ca/pstack@fa2cbfc0` |
| Port applied upstream pin | `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` |
| Upstream target tip | `cursor/plugins@bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7` |
| Declared package versions | Upstream `0.15.42`, Port `0.15.36-preview.0` |

Source-scoped Git comparison across `cursor/plugins/pstack` identified 59 changed files (376 insertions, 1032 deletions).
The vast majority of deletions stem from upstream Cursor collapsing `why` and `how` prompt templates into single-file skills.

## High-Impact Semantic Changes

### 1. Simplification of Why and How Skills vs Six-Harness Role Registry
Upstream Cursor collapsed `why/SKILL.md` to a single 48-word file and deleted `skills/why/references/*` (12 files).
Upstream also collapsed `how/SKILL.md` to a single file and deleted its 2 template files.
Crucially, upstream dropped `how explorer`, `how explainer`, `why investigators`, and `why synthesizer` from its Cursor-specific setup rule.

**Architectural Decision for Portable PStack:**
In Cursor, subagents are dynamically spun up with ad-hoc instructions or untyped Task calls.
In our six-harness portable architecture (Grok, Codex, OMP, OpenCode, Antigravity, Droid), each subagent is typed and verified against `pstack.package.json`'s 22 canonical roles.
Our test suite (`tests/test_model_role_constraints.py`, `tests/test_verify_harness.py`, `tests/test_project_package.py`) strictly enforces that all 22 roles exist and have valid bindings.
Overwriting or deleting these roles would break non-Cursor host adapters and fail portability invariants.
Therefore:
- We retain the 22 canonical roles in `pstack.package.json` and host projections.
- We decouple dependent skills (`blast-radius`, `recall`, `comment-sicko`, `poteto-help`) from obsolete internal prompt template paths.

### 2. Sharpen & Reflect Prompt Improvements
- `skills/sharpen/SKILL.md`: The prompt now directs the agent to prototype any choice an experiment can settle, reserving only product and preference choices for the human. This aligns directly with `principle-model-the-domain` and the Prototype playbook.
- `skills/reflect/references/synthesizer.md`: Replaces model rename examples with code refactor examples (`parseConfig` to `loadConfig`), keeping reflection focused on durable code patterns rather than transient model slugs.

### 3. Statechart Parent Border Edge Routing
- `skills/statechart/scripts/backends/mermaid.ts`: Introduces `drawnEdges` algorithm. When an edge enters a compound parent state, it connects cleanly to the parent's border rather than piercing through the cluster title bar.
- `skills/statechart/scripts/run.ts`: Adds plain-text error extraction fallback when SANY XML parsing aborts.

### 4. Classification Table Reconciliation
- Canonical table `skills/swarm/references/classification.tsv` is updated with all 59 delta paths from upstream commit `bf0c7cd8`.
