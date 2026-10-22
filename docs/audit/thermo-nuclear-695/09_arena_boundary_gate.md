# Arena: boundary gate

Two candidates, one base, one cross-judge. Base for the comparison is `10025900e8cb481540ce6f61f32d6b73ff638b3f`. Candidate A is `arena/bnd-a` in `.worktrees/arena/bnd-a`. Candidate B is `arena/bnd-b` in `.worktrees/arena/bnd-b`.

Both candidates were graded against a rubric frozen before either spawned.

1. Detection preserved across install path, routing directive, primitive name, and concrete default model, with no vocabulary shrink.
2. No line-numbered carve-out, invariant under a line move, and a reword yields a graded violation rather than an exception.
3. Exemptions must not cover a surface the epic is migrating.
4. Fail closed on an unparsable profile or an unreadable in-scope file.
5. Vocabulary derived from `profiles/*.json` where the profile already declares the fact.
6. Size and surface counted against the number of proofs.

## Candidate A

One module, three named text-keyed detectors per line. Profile-derived vocabulary covers primitives, models, wire targets, and `plugins_dir`. Routing is clause-scoped with position-scoped negation. Reviewed sentences are keyed by text, and the residual line is rechecked.

Measured by the candidate and by me. Scanner 446 lines. Test file 30 parametrized items, all green in 1.43 seconds. Vocabulary 39 items with `lost tokens: []` against base. All eight profile `plugins_dir` paths added. The reviewed sentence passes at line 1 and line 401. `hand to Grok Build's /create-skill` now flags. A bare mention and a comparison do not.

## Candidate B

One line-oriented pass over three declarative tables. A single forbidden-vocabulary map, one clause-scoped routing rule, and one path-glob exemption list whose only allowance is keyed to a sentence's text.

Measured by the candidate and by me. Scanner 385 lines. Test file 20 items, all green in 1.61 seconds. Scan reports 143 files and 0 leaks. Vocabulary 39 items, install paths derived from every profile, not one hardcoded path. The possessive routing case and the negated-then-directive case both flag.

## Scores

| criterion | A | B |
| --- | --- | --- |
| 1 detection preserved | routing 10 of 10 phrasings, 2 of 8 false positives on legal mentions | routing 8 of 10 phrasings, 7 of 8 false positives on legal mentions |
| 2 no line key | allowance short-circuits the line, so `Hand the loop to Grok Build.` on the sanctioned line passes | per-occurrence accounting, sanctioned plus a directive still flags |
| 3 migrating surface | fail, `skills/setup-pstack/**` still exempt with a Grok-only reason | fail, same exemption with the same stale reason |
| 4 fail closed | fail, both silently continue on a corrupt profile and lose that host's vocabulary | fail, same measurement |
| 5 profile-derived vocabulary | derives every `plugins_dir`, including absolute paths | derives only home-relative `plugins_dir` |
| 6 size against proofs | 446 lines, 30 tests | 385 lines, 20 tests |

Criterion 4 was measured by the cross-judge by corrupting `profiles/bad.json` and running each candidate. My first read of candidate A inferred fail-closed from the absence of a blanket `except`, and that inference was wrong. Both candidates swallow the parse error. Neither candidate's result is final. The base and the two grafts are plan steps in `boundary-gate`, not an applied artifact, so the synthesized scanner does not exist yet and nothing here claims it does.

## Decision

Base is A. The cross-judge picked A and my first read picked B. The disagreement resolved on criterion 1, which the rubric ranks first. B misses two routing phrasings that A catches and raises seven false positives on legal verb-bearing mentions against A's two. A's defect is local, an allowance that shelters the rest of the line. B's precision hole would need A's object and preposition rule rebuilt inside it, and widening B's verb list multiplies its false positives.

Grafts from B, both accepted.

B's per-occurrence `_allowed_occurrences` accounting, which removes A's directive shelter and its false positive on the sanctioned line.

B's `test_cli_exits_1_on_a_leak`, because A's suite never proves a non-zero exit on a real leak.

Two requirements belong in either base and neither candidate met them. Abort on an unparsable profile and on an unreadable in-scope file. Narrow or delete `skills/setup-pstack/**`, which after PR #719 is the host-neutral entry.

## Independent findings the arena produced

Both candidates found and fixed the same two real directives that the review found separately. `skills/reflect/SKILL.md:56` and `skills/automate-me/SKILL.md:67`. Two independent candidates converging on the same leak is corroboration that the base gate was blind to it.

## Family diversity

The harness rejected a per-child model override on this host, so both candidates and the judge ran on the same model family. This arena records generation diversity only. It is not multi-family independent judgement and the run is `DEGRADED` on that axis.
