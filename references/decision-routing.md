# Decision routing registry

`decision-routing.json` is the canonical, provider-neutral inventory for the playbooks in the official pstack source tree. Each route records the playbook name, its source blob hash, and one selection mode. Semantic candidates also carry one closed class label. The JSON owns the rows; this document records how to read them and where the source came from.

## Interpretation

`direct` marks an explicit command or deterministic trigger. Those routes bypass semantic classification. `system_two` keeps route choice with the existing pstack judgment path. `semantic_candidate` allows a bounded semantic result to suggest only the listed route class after explicit commands, deterministic facts, and hard safety or autonomy policy have been applied. These labels are advisory. They grant no authority to diagnose, generate, execute tools, approve irreversible actions, merge, or bypass a human gate.

Explicit playbook invocation bypasses classification. Every other unknown, unsupported, `other`, unavailable, or abstaining result uses `baseline`. Hard safety, autonomy, and human-gate policy remains in the formal contract and cannot be changed by this registry. The registry does not enable a provider or alter current behavior.

The production route seam is the unresolved point in `/poteto-mode` immediately before it copies the selected playbook steps into the todo list. The `route_playbook` checks in conformance drivers validate a harness profile and target file. They do not classify a user task, so this registry does not treat them as the production router.

## Source capture

The inventory follows the official `cursor/plugins` source at commit `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (v0.15.29). Its resolved Git tree is `6e60624e2f172e2d8d796d6e644695ff5591e29f`. `source.revision` identifies the commit; `source.tree` identifies its root tree. The recorded router blob `21993f546032ca37671d5f1caf39c9a82ab4fa9d` (`skills/poteto-mode/SKILL.md`) supports drift checks, and each playbook row records its own canonical blob hash.

Capture the commit object and its resolved tree with:

```sh
gh api 'repos/cursor/plugins/commits/88d47514b82e7c44f00f2b2a72ff6dd12158038c' > upstream-commit.json
gh api 'repos/cursor/plugins/git/trees/6e60624e2f172e2d8d796d6e644695ff5591e29f?recursive=1' > upstream-tree.json
jq -e '.sha == "88d47514b82e7c44f00f2b2a72ff6dd12158038c" and .commit.tree.sha == "6e60624e2f172e2d8d796d6e644695ff5591e29f"' upstream-commit.json
```

The commit response binds the source revision to the separate tree identity recorded in the registry. The complete API export used for this registry reports `truncated: false`. The local `UPSTREAM` pin and `pstack.package.json#upstream_pin` match `88d47514b82e7c44f00f2b2a72ff6dd12158038c`.

### Playbook Classification Rationales (23 Playbooks)

- **Semantic Candidates (7)**:
  - `bug-fix` (`defect`): Low-risk, focused unit/regression repair with hermetic test verification.
  - `investigation` (`explain`): Read-mostly codebase and architectural explanation with zero mutations.
  - `perf-issue` (`performance`): Isolated bottleneck profiling and optimization with benchmark verification.
  - `prototype` (`prototype`): Disposable, bounded exploratory spike code.
  - `refactoring` (`refactor`): Semantics-preserving code reorganization under test invariant protection.
  - `runtime-forensics` (`runtime_diagnosis`): Diagnostic reproduction and log inspection without mutation.
  - `trace-forensics` (`trace_diagnosis`): Trace inspection and stack analysis without state modification.

- **Direct Deterministic (6)**:
  - `autonomous-run`, `autopilot-full`, `autopilot-stack`, `babysit`, `pause-safely`, `session-pickup`: Explicit session life-cycle commands with deterministic execution boundaries.

- **System-Two Gateways (10)**:
  - `authoring-a-skill`, `eval`, `feature`, `hillclimb`, `multi-phase-plan`, `opening-a-pr`, `orchestrate`, `shipping`, `visual-parity`, `worktree-cleanup`: Multi-step, architecturally consequential, safety-critical, irreversible, or forge/PR interacting workflows requiring human-in-the-loop or System-Two planning.
