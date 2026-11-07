---
name: make-pr-easy-to-review
description: Prepare PRs for review by cleaning noisy history, improving PR descriptions, and adding reviewer guidance without changing code behavior. Use for "make this easy to review", "tidy this PR", "clean up commits", or "annotate the diff".
---

# Make PR Easy to Review

Prepare a PR so a reviewer can quickly understand the intent, important files, and risk. The default goal is reviewability without behavior changes.

## Workflow

1. Resolve the target PR from the user-provided URL or current branch.
2. Inspect commits, diff size, changed paths, generated files, and PR description.
3. Identify reviewability issues: noisy commits, stale description, unrelated changes, mixed mechanical and logic changes, missing tests, or unclear reviewer entry points.
4. Propose a plan before rewriting history or force-pushing.
5. Apply safe improvements, then verify the tree or diff still matches the intended code.

## History Cleanup

Only rewrite history when the user asks for it or agrees to the plan. Before rewriting:

```bash
gh pr view <PR> --json title,headRefName,baseRefName,state,commits
git fetch origin <headRefName> <baseRefName>
ORIGINAL_TREE=$(git rev-parse origin/<headRefName>^{tree})
```

Good commit groupings usually follow dependency order:

1. Schema/storage or generated API definitions.
2. Core logic.
3. Wiring and integration.
4. UI or surface behavior.
5. Tests.

After rewriting, verify content identity:

```bash
echo "Original tree: $ORIGINAL_TREE"
echo "Current tree:  $(git rev-parse HEAD^{tree})"
git diff origin/<headRefName> --stat
```

Do not push if the tree changed unintentionally.

## Reviewer Guidance

When code behavior should stay untouched, prefer PR description and review notes:

- Add a TL;DR that matches the actual diff.
- Separate core files from generated or mechanical files.
- Call out risky behavior changes, migration order, rollout plan, and test coverage.
- Link issue trackers, dashboards, or design docs when they explain intent.

## Verification Claims

When asked to polish an existing PR directly, reuse the [Opening a PR](../poteto-mode/playbooks/opening-a-pr.md) verification rules and the [Fix CI](../fix-ci/SKILL.md) current-head receipt checks. Do not create a second test or CI verdict system.

Only call a check `PASS` when it actually ran and its result still applies to the PR's current patch and required base checks. An unrun or planned check is `UNTESTED`; an unavailable required check is `BLOCKED`. A stale green receipt cannot be reported as current `PASS`. If the PR head or base changes, check freshness again before retaining test claims. Link the commands, observed outcomes, and known gaps; keep the PR body a short reviewer briefing.

## Guardrails

- Never hide meaningful behavior changes inside "cleanup".
- Do not bypass hooks unless the user explicitly asks.
- If the PR is too large to make reviewable with notes, recommend splitting instead of polishing around the problem.
