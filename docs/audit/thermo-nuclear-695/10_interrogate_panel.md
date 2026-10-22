# Interrogate: adversarial panel

## Intent

Epic #695 removes Grok-only authority from shared pstack contracts while keeping the Grok adapter. The train `ef34052..1002590` and open PRs #717, #718, #719 were reviewed against one question. Does this deliver a trustworthy six-host contract, meaning a gate that can fail and evidence that can record bad news.

Two seats ran the same packed prompt, built once by `skills/interrogate/scripts/pack.py` and frozen before either spawned. Diff excluded `.audit/evidence` to keep the pack readable, which matters for one finding below.

## Reviewers

- Seat A, 11 findings. Verified by running the scanner, `refresh-static` for omp and grok, a live-FAIL durable write, an eight-module pytest block at base plus patch and at head, and the two #717 hermetic tests.
- Seat B, 8 findings. Verified by running scanner fixtures, `write_verification_evidence` with a live-FAIL receipt, a monkeypatched `refresh-static --host all`, and the applied patch's pytest runs.

Both seats ran on the same model family, because this host rejects a per-child model override. The panel is `DEGRADED` on family diversity and this is not multi-family proof.

## Consensus, two independent seats

**The evidence system can only improve.** Both seats reproduced it. A re-observed `runtime-child-spawn-omp` that now FAILs is refused with `REFUSING ... cannot be re-observed by a static refresh`, and the durable receipt keeps `overall_verdict: PASS`. Seat A named the message's second defect, that it calls a live run a static refresh and prescribes `PSTACK_RUN_OMP_LIVE=1`, which produces the same refusal. This agrees with two review lanes that reached it separately, so four independent readers now hold it.

**The gate's token list misses the paths the profile itself declares.** Seat A wrote `Write ~/.grok/roles/pstack:feature.toml` into a shared surface and got exit 0 with zero violations. I confirmed that `~/.grok/roles` is absent from the vocabulary at `1002590`, and that the file naming it, `skills/setup-pstack/SKILL.md`, is exempt from the scan. The overlay path is what `setup-pstack` writes, so the gate cannot see the write it exists to forbid.

**The setup projection has no writer.** Both seats and one review lane agree. `resolve_setup_projection` has zero production callers, and a profile declaring `source: none` does not stop the Grok writer.

**The new test file never runs in CI.** Both seats raised it. I confirmed `tests/test_setup_projection.py` appears in no workflow, so the 299 lines that cover the projection are outside the required gate.

**The pack cannot pass its own gate.** Both seats saw 8 failures in the evidence modules at base plus patch, from `package_driver_revision`, `profile_hash`, and `skills_tree_hash` mismatches, because #719 edits files that are hashed into the receipts. #718's restamp was excluded from the pack by my own diff filter, so the failure is partly an artifact of the pack. The coupling is not. Any PR that edits `portability_types.py` or the profiles invalidates every durable receipt, and `refresh-static --host omp` refuses to repair it. That belongs in the plan as an explicit restamp step, not as an assumption.

## Act on

The regression refusal, as the first program PR. It is the reason the program is ordered as it is.

The `~/.grok/roles` blind spot, as part of `boundary-gate`. Deriving install and overlay paths from `profiles/*` is the same fix, and both arena candidates already do half of it.

Registering `tests/test_setup_projection.py` in the offline workflow, as part of `setup-projection`.

## Consider

Seat A's note that `README.md:9` claims the map records independently verified evidence, while every receipt is stale at the packed head and the only live rows come from one self-produced run. That is a claim-tightening item for `gate-reconcile`, not a code fix.

## Noted

Seat B's false-positive note, that canonical prose containing `plain_text_question` or `write_to_file` fails as a host leak. Real, and both arena candidates narrow it by dropping free-text primitives from the vocabulary.

## Dismissed

Neither seat found a defect in the #717 fixture-home decision itself. Seat A ran the two hermetic tests and reports the property holds when read. The residual defects in that PR are the ones the dedicated lane found, not a wrong seam.

Seat B's statement that the pack's `runtime` plane claim is unverified is correct and out of scope. No live host execution was attempted by this review, and the report says so.

## Agreement map

Four readers, two lanes and two panel seats, independently converged on the evidence refusal. Three converged on the projection's missing caller. Two converged on the CI omission. Where a single seat found something, the `~/.grok/roles` blind spot and the false-positive vocabulary, I verified it directly before promoting it into the program.
