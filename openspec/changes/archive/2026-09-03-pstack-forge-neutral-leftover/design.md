## Context

In-force ADRs that constrain this change: 0003, 0004, 0005, 0007, 0008 (supersedes 0006), 0009, 0010, 0011. Historical only: 0001, 0002, 0006.

The no-write YAML contract is already applied. Orchestrate already forbids `scripts/orch` (ADR 0008). It still names Graphite `gt` as the frontier source. `test_forge_neutral_pr_path_without_graphite` never opens that file. `docs/guide/11-grok-workflows.md` still sends `capability_mode` on Rhai `agent()` while ADR 0005 keeps playbooks as markdown and the user-guide says capability mode is not a spawn argument.

## Goals / Non-Goals

**Goals:**

- Make orchestrate forge-neutral on the existing `github-pr-fallback.md` map.
- Fail CI if orchestrate requires `gt` again.
- Stop teaching `capability_mode` on the Rhai `agent()` example.
- Replace babysit cloud wording.

**Non-Goals:**

- Do not delete Codex `orch` / `watch-pr`.
- Do not change Benny `.rhai` copies in this change (optional copies, not the live slash path).
- Do not archive other OpenSpec changes.
- Do not update the installed host plugin.
- Do not add `inheritSkills` tests or restore `docs/guide/images/`.

## Decisions

### One change, two independent lanes

Forge playbook plus workflows guide share one leftover pass and one task DAG. They do not share files. Apply sequentially in the parent to avoid a dirty pytest file race. Alternative rejected: two OpenSpec changes. That doubles archive hygiene for two small spec deltas.

### Rewrite onto the existing map

Do not invent a new stack CLI. Copy the `origin pr` / `gh pr` table already in `github-pr-fallback.md`. Alternative rejected: keep `gt` when Graphite is installed. The spec says MUST NOT require Graphite, not "prefer Graphite when present."

### Test reads orchestrate.md

The previous forge-neutral test was the wrong observation method. It proved HARNESS and shipping, then inferred orchestrate. The new assertion reads the playbook. Alternative rejected: a body-text ban on the token `gt` in every markdown file. Codex docs and negatives need to name Graphite.

### Rhai example omits capability_mode

`pstack:how-explorer` already ships `capabilityMode: execute`. Teaching `read-only` on `agent()` would strip shell if honored and lie if ignored. Alternative rejected: set `capability_mode: "execute"` to match YAML. Spawn still ignores that field. Omit it.

## Risks / Trade-offs

[Risk] Operators who already run Graphite lose a named `gt` restack sentence. -> Mitigation: the fallback map already restacks with `git rebase` onto the parent branch, then views through `origin`/`gh`.

[Risk] Benny `.rhai` still sends `capability_mode: "execute"`. -> Mitigation: parked. Those files are optional copies, not `/benny-triage`.

## Migration Plan

Static rewrite plus pytest. No runtime migration. Revert the playbook and test if verify-harness fails.

## Open Questions

None. No in-force ADR needs supersession.
