---
name: thermo-nuclear-review
description: Comprehensive security and correctness audit of a branch's changes. Use for thermo nuclear, thermonuclear, or deep review requests, or branch/PR diff audits focused on bugs, breaking changes, security issues, devex regressions, and feature-gate leaks.
disable-model-invocation: true
---

# Thermo-Nuclear Review

Use this skill for an unusually strict correctness and security audit.
Focus on logic bugs, breakages, security vulnerabilities, and developer experience regressions.
Restrict reporting strictly to code added or modified in the diff.
Do not report pre-existing issues in untouched legacy code.

## Core Prompt

Start from this baseline.

> Perform a deep security and correctness audit of the changes.
> Scrutinize the code for logic bugs, breaking changes, security vulnerabilities, and developer experience regressions.
> Trace cross-package side effects and implicit contract assumptions.
> Verify every hypothesis against real repository files before reporting.
> Cite exact file and line numbers for all findings.

## Scope and Boundaries

Follow these strict scope rules.

1. Report only on added or modified lines in the active diff.
2. Do not report pre-existing vulnerabilities in untouched code.
3. Trace cross-package dependencies when modified code affects external callers.
4. Verify repository state directly instead of guessing what external components do.

## Core Review Guidelines

### 1. Breaking Functionality Guidelines

Trace cross-module and cross-package dependencies exhaustively.
Catch subtle interactions where small changes in one component break functionality elsewhere.
Look for altered function signatures, changed return types, and dropped parameters.
Look for unhandled null, undefined, or empty collections.
Check that callers across all packages adapt to the new contract.

### 2. Breaking DevEx Guidelines

Catch modifications that disrupt a developer running or building the code locally.
Check for altered secret reading paths or changed credential schemas.
Check for updated or newly introduced environment variables that lack default values.
Check for remapped network ports or socket bindings.
Check for newly mandated setup scripts or database migration prerequisites.

### 3. Feature Leak Guidelines

Ensure features meant to remain hidden behind feature gates do not leak prematurely.
Inspect conditional gates to ensure default behavior remains unchanged for standard users.
Check for exposed internal endpoints, unguarded CLI flags, or public exports.
Check that unfinished features are not enrolled in production routers.

### 4. Intended Breakage Guidelines

A branch may deliberately introduce a breaking change or retire a legacy interface.
Do not report intended breakages when the change is explicitly planned and documented.
Report intended breakages only when the author appears unaware of unmigrated callers.
Report intended breakages when the scope of breakage exceeds the stated goal.

### 5. Over-Reporting Guidelines

Do not inflate minor issues into critical blockers.
Maintain complete confidence in a finding before marking it high severity.
Every high-severity finding requires a concrete reproduction path.
False alarms erode developer trust.
Focus on high-signal defects.

## Execution Protocol

### Fresh Eyes Protocol

Perform an independent audit with fresh eyes before reading pull request comments.
Form your own judgment from the diff and the codebase directly.
Query existing discussion threads only after completing your independent review.
Use existing threads to validate, deduplicate, or clarify open findings.

### No Unfinished Research Rule

Never present findings with unfinished research.
Never state that an issue depends on unseen code when that code exists in the repository.
Read backend handlers, database schemas, and shared utilities directly.
Deliver concrete, verified conclusions backed by cited evidence.

## Report Structure

Structure the review report with these sections.

1. Summary. State the overall review verdict and risk assessment.
2. Critical Findings. List security vulnerabilities and breaking defects with file and line citations.
3. DevEx and Operational Findings. List developer experience and configuration risks.
4. Advisories. List lower-priority edge cases and defensive recommendations.
5. Verification Evidence. List the commands and file inspections that proved each finding.
