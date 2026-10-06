# Harness unification and Droid delivery stack

Published issue graph and explicit-parent PR stack for epic #162 (unify
five-host mapping architecture, fix receipt fingerprints) plus Droid as the
sixth declared host. This file records the real published URLs; the stack is
review-only and stops at merge-ready. Merging is a human decision.

## Issue graph

- Epic: [#162 — Unify 5-Harness Mapping Architecture and Retire Root HARNESS.md](https://github.com/tommy-ca/pstack/issues/162)
- Open children: [#165](https://github.com/tommy-ca/pstack/issues/165) (OpenSpec intent),
  [#166](https://github.com/tommy-ca/pstack/issues/166) (verifier migration),
  [#167](https://github.com/tommy-ca/pstack/issues/167) (retirement),
  [#169](https://github.com/tommy-ca/pstack/issues/169) (fingerprint defect fix)
- Closed history preserved unmodified: [#163](https://github.com/tommy-ca/pstack/issues/163),
  [#164](https://github.com/tommy-ca/pstack/issues/164)
- Droid work: [#170](https://github.com/tommy-ca/pstack/issues/170) (parent) with children
  [#171](https://github.com/tommy-ca/pstack/issues/171) (package/role projection) and
  [#172](https://github.com/tommy-ca/pstack/issues/172) (sixth-host declaration)
- Dependency edges: #169 blocks #166 and #167; #170 is blocked by #165 and #169.

## PR stack

Each PR targets its explicit parent branch; only S1 targets `main`. Review
each slice against its own base, not the cumulative diff.

| Slice | PR | Head branch | Base branch | Implements |
| --- | --- | --- | --- | --- |
| S1 | [#173](https://github.com/tommy-ca/pstack/pull/173) | `stack/s1-unify-intent` | `main` | #165 |
| S2 | [#174](https://github.com/tommy-ca/pstack/pull/174) | `stack/s2-fingerprint-invariance` | `stack/s1-unify-intent` | #169 |
| S3 | [#175](https://github.com/tommy-ca/pstack/pull/175) | `stack/s3-grok-tools-migration` | `stack/s2-fingerprint-invariance` | #166 |
| S4 | [#176](https://github.com/tommy-ca/pstack/pull/176) | `stack/s4-retire-harness-md` | `stack/s3-grok-tools-migration` | #167 |
| S5 | [#177](https://github.com/tommy-ca/pstack/pull/177) | `stack/s5-droid-package-roles` | `stack/s4-retire-harness-md` | #171 |
| S6 | [#178](https://github.com/tommy-ca/pstack/pull/178) | `stack/s6-droid-driver-lifecycle` | `stack/s5-droid-package-roles` | #172 |

Review-fix commits are appended to their owning branch: S5 carries the
execute-tools correction and the YAML-scalar quoting fix; the S5 generator
fix is reproduced on S6 by an appended cherry-pick, and S6 additionally
carries the driver evidence-label and durable-receipt guard fixes. No
published history was rewritten.

## Validation state

The repository has no PR CI workflow: `statusCheckRollup` is empty on every
PR. Absent checks are not passing checks. Each PR's evidence is the local
gate set applicable to its own slice, run serially at that PR's head SHA and
recorded in the PR body; the full suite and CLI gates run at the final
implementation head. Droid runtime capabilities (custom-role serving, model
selection, live `Task` execution) remain explicitly untested.
