# Feature: Truthful Archive and Scaffold Decoupling
Tracking document for Epic #1281: Remediate adversarial findings by annotating truthful task outcomes on archived changes, removing OpenSpec wrapper from scaffolder, and enforcing direct bunx execution.

## Specs
S1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review"
S2: "build and update verification skills/tools"
S3: "clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate"
S4: "new stacked prs, merge and ship then, end to end verify the workflows then"
S5: "A task that required an unavailable external repository, host, or credential MAY close with an explicit outcome annotation only when the annotation states that the action was deferred, names the reason, and points to the follow-up; it MUST NOT claim that the external action ran."
S6: "All OpenSpec Python wrappers in scripts/ have been deleted in favor of direct bunx execution."

## Tasks
- [x] T1 (S1, S3, S5) [route: inline] [commit: 254c754] Truthfully annotate historical PR resolution and follow-up outcomes on all 77 reconciled tasks in the 3 archived changes.
- [x] T2 (S1, S2, S6) [route: inline] [commit: c52ec89] Remove redundant audit_openspec_status and --check-openspec from scripts/scaffold_verification_skill.py.
- [x] T3 (S1, S2, S4) [route: inline] [commit: b8464a6] Point verify:openspec:audit in mise.toml to direct bunx execution, tighten tests/test_openspec_direct.py, update docs and todo.md, refresh evidence, and close Epic 1281.

## Log
L1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review build and update verification skills/tools, clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate, new stacked prs, merge and ship then, end to end verify the workflows then"
