---
name: thermos
description: Launch both thermo-nuclear review subagents in parallel, then synthesize their findings. Use for thermos, double thermo review, or combined bug/security and code-quality branch audits.
disable-model-invocation: true
---

# Thermos Dual Review

Use this skill to orchestrate a double thermo-nuclear review across a git branch or pull request.
Thermos runs two focused review passes in parallel and synthesizes their findings into one unified report.
The first pass evaluates correctness, security vulnerabilities, and developer experience regressions.
The second pass evaluates architecture, maintainability, and code quality rubrics.

## Workflow Overview

Follow this four-step workflow.

1. Determine the review scope from the user request, current branch, or target pull request.
2. Gather the git diff and inspect the full content of modified files.
3. Launch both review passes in parallel using subagents.
4. Synthesize, deduplicate, and rank the findings into a single prioritized report.

## Step 1. Scope Determination

Determine what code needs review.

- If the user names specific files or paths, bound the review to those paths.
- If a pull request number is provided, resolve the PR diff using the forge CLI.
- If working on a feature branch, resolve the diff against the target base branch using `git diff origin/main...HEAD`.
- If uncommitted changes exist in the working directory, resolve the diff using `git diff HEAD`.

## Step 2. Context Gathering

Collect complete context before launching review subagents.

- Gather the full unified diff.
- Enumerate every modified, added, or deleted file.
- Inspect surrounding module boundaries and caller sites when contracts change.
- Verify whether tests or documentation were updated alongside code changes.

## Step 3. Launch Parallel Review Passes

Launch both review passes simultaneously using the active host subagent capability.
Pass the gathered diff and file list to each pass.

### Pass A. Correctness and Security Audit

Invoke the `thermo-nuclear-review` skill.
This pass scrutinizes the diff for the following issues.

- Logic bugs and unhandled boundary conditions.
- Security vulnerabilities and authorization flaws.
- Developer experience regressions and altered environment variables.
- Premature feature-flag leaks and unhandled breaking changes.

### Pass B. Maintainability and Architecture Audit

Invoke the `thermo-nuclear-code-quality-review` skill.
This pass scrutinizes the diff for the following issues.

- File size sprawl crossing the one thousand line threshold.
- Unnecessary abstractions, wrapper bloat, and indirection layers.
- Spaghetti logic, ad-hoc conditionals, and scattered special cases.
- Opportunities for structural code judo simplifications.

## Step 4. Synthesis and Deduplication

Synthesize the findings from both passes into a single executive verdict.

- Deduplicate overlapping findings where code quality issues trigger correctness concerns.
- Prioritize critical security flaws and functional breakages over structural recommendations.
- Group related architectural findings to suggest unified refactoring moves.
- Provide actionable remediation steps with exact file and line references.

## Output Format

Present the final synthesized report in this structure.

### Executive Summary
State the overall verdict, risk level, and review recommendation.

### Critical Blockers
List any defects that block shipping, including security vulnerabilities and broken behavior.

### Architecture and Maintainability Recommendations
List structural code judo moves and maintainability improvements.

### Developer Experience and Operational Notes
List environment, configuration, and tooling observations.

### Verification Trail
List the checks, commands, and file references used to prove each finding.
