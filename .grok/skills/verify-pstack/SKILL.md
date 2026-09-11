---
name: verify-pstack
description: "Use when verifying this pstack Grok plugin, leftover Cursor harness call sites may still be live (leftover-scanner is Cursor harness token doctor, not git leftover clones or disk prune), plugin doctor is in doubt, refresh-hygiene, upstream pin, upstream recipe, or release-tag checks are needed, or an agent reaches for grok plugin validate, grok inspect, or pytest as a substitute for scripts/verify-harness.py."
disable-model-invocation: true
---

# Verify pstack

Short-lived CLI plugin. No server. Drive it with `.grok/skills/verify-pstack/scripts/verify.py`. Do not improvise doctor.

Plugin doctor lives at `.grok/skills/verify-pstack/`. Do not ship it under `skills/`. `plugin.json` lists `./skills/` and must not list `.grok/skills`. Do not write `.claude/skills`. Do not write `~/.grok/skills`.

The map lives at `features/`, next to this file. Do not read OpenSpec for drive recipes. Do not look under `references/features/`.

## Launch

Work in a pstack plugin checkout. `plugin.json` name is `pstack`. `scripts/verify-harness.py` exists.

Need `python3` and `grok` on `PATH`. Refresh-hygiene also needs `uv`. Do not run `mise use -g` to get them.

Each drive is its own process. Isolation is `--run-id`, not `--checkout`. There is no CDP checkout flag. Two runs may share a checkout when they use different `--run-id` values. There is no long-lived instance to keep alive. Refuse a second drive that would share live `~/.grok/skills` or the user's overlay dest.

Ready means leftover scanner printed `PASS` and exited 0. Run doctor until that is true.

## Doctor

Leftover scanner is required doctor. Run it. No substitutes. leftover-scanner is not git leftover clones; isolation reclaim is the worktree-cleanup playbook.

```bash
python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .
```

That runs `python3 scripts/verify-harness.py`, then `grok plugin validate .`. Leftover stdout must start with `PASS` and include `playbooks: 22 named + opening-a-pr`, `principles: 23`, and `plugin.json name: pstack`. Leftover exit 0. Validate stdout contains `Plugin manifest is valid.` Exit 0.

Later `drive` on the same `--run-id` refuses if leftover scanner did not PASS. `drive leftover-scanner` may run the scanner without a prior doctor log. Other features still require that leftover `PASS` in this run's doctor evidence.

**No exceptions.**

- Do not treat `grok plugin validate` as leftover scanner.
- Do not treat `grok inspect --json` as leftover scanner. `inspect` `plugins[].enabled` is trust.
- Do not treat `pytest` or `tests/test_verify_harness.py` as leftover scanner. Those are not the tree walk.
- Do not skip leftover scanner because TEST-PLAN.md says it is not an EDITH pass gate. TEST-PLAN is the live-CLI gate plan. This skill still requires the leftover scanner as doctor.
- Do not run validate first and call doctor done if leftover scanner did not print `PASS`.

Doctor also fails if `<root>/.grok/workflows` exists. Do not create that directory.

Re-run doctor after any failed drive, and before the first drive of a run.

| Excuse | Reality |
|---|---|
| `grok plugin validate` plus inspect is doctor | Leftover scanner is required doctor. Validate is the companion only. Inspect is not doctor. |
| pytest already covers leftover tokens | `tests/test_verify_harness.py` is not `scripts/verify-harness.py` walking the tree. Run the scanner. |
| TEST-PLAN says verify-harness is not a pass gate | EDITH live-CLI gates are a different check. This doctor still requires leftover `PASS`. |
| Static scan is not a user path | The operator path is `python3 scripts/verify-harness.py`. Drive it. |
| I will run leftover scanner later | Doctor first. A drive without leftover `PASS` is invalid. |

## Drive

```bash
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature leftover-scanner
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-pin
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-recipe
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature refresh-hygiene
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature release-tag
```

Omit `--feature` to drive every mapped feature. That walk follows `features/README.md` top to bottom. It is the Full sweep. Driving one convenient feature is not a sweep. That path requires leftover `PASS` in this run's doctor evidence first. `drive leftover-scanner` may run without that log. Other features on the same `--run-id` refuse until leftover scanner PASSed.

Read `features/README.md`, then the feature file. Drive the listed commands through `verify.py`. Do not paste `refresh-hygiene.py --apply-skills`. Do not run `scripts/release.sh` to completion from nested grok.

## Proof bar

Do not submit "look, it opens" captures. `grok plugin validate` plus inspect is not leftover scanner. A leftover `PASS` line, a 40-hex pin, `--recipe` stdout needles plus argv without `--log`, a hygiene TSV, or `PASS tests/test_release.py` counts only when it is the mapped operator path with stdout, stderr, and exit code in the same evidence directory.

- Drive the operator command through `verify.py`. Do not call internal Python functions as the proof.
- Run doctor first. A capture without leftover `PASS` in this run's doctor log is not evidence.
- Read the feature file. Exercise every reachable entry point it lists, and the success, cancel, error, empty, and persistence paths the change can affect.
- For a broad regression, walk `features/README.md` top to bottom. That is leftover-scanner, upstream-pin, upstream-recipe, refresh-hygiene, then release-tag.
- Show the trigger command and the stable end state in the same evidence directory.
- Verify side effects, not only stdout. Hygiene must leave `~/.grok/skills/reflect` unchanged and write `--host-script` dest under `/tmp/`.

## Evidence

Directory: `/tmp/verify-pstack-evidence-<runid>/`. `verify.py` prints `run_id` and `evidence` on PASS.

Keep command, stdout, stderr, and exit code for every step. Leftover proof is the `PASS` line plus playbook and principle counts. Pin proof is the 40-hex SHA that matches `UPSTREAM`. Recipe proof is `--recipe` stdout needles plus argv without `--log`. Hygiene proof is the TSV header, the `cp -- ` line, and an unchanged live skills fingerprint. Release proof is `PASS tests/test_release.py`.

Cleanup must not delete this directory.

## Cleanup

```bash
python3 .grok/skills/verify-pstack/scripts/verify.py cleanup --run-id <runid>
```

Removes `/tmp/verify-pstack-scratch-<runid>/` only. Confirm the evidence directory still exists after cleanup. Do not kill by process name. Do not `git worktree remove`. Isolation reclaim is the worktree-cleanup playbook, not verify cleanup. Do not delete leftover-worktree rows for OPEN PRs. Do not `rm` `/tmp/verify-pstack-evidence-<runid>/`.

## Helpers

`.grok/skills/verify-pstack/scripts/verify.py` is executable. This skill ships that driver. The verification-skill-example omits its driver on purpose. Do not omit this helper.

From a checkout that already has the skill:

```bash
python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .
python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature leftover-scanner
python3 .grok/skills/verify-pstack/scripts/verify.py run --root .
python3 .grok/skills/verify-pstack/scripts/verify.py cleanup --run-id <runid>
```

`run` is doctor, then every feature (or `--feature`), then cleanup. Evidence survives `run`.

Pass `--root` when the script is not inside `.grok/skills/verify-pstack/scripts/`. Pass `--run-id` to isolate concurrent runs. Do not pass `--checkout`.

## Refused paths

`verify.py` refuses these. Do not run them by hand during a verify run either.

- `--log` (sync-only fetch; not a verify path)
- `--apply-skills` (default dest is `~/.grok/skills`; live `reflect` may be a symlink)
- `scripts/release.sh` to completion when `__GROK_INSIDE_BWRAP` is set
- `mise use -g`
- `git worktree remove` of OPEN PR worktrees. Isolation reclaim is worktree-cleanup, not verify.
- creating plugin `.grok/workflows`
- `chmod` on overlay dests
- writes under `~/.grok/skills`

Hygiene `--host-script` and dry-run must pass `--skills` under `/tmp/verify-pstack-scratch-<runid>/`. Default `--skills` is live dest. Do not use the default.

## Red flags

Stop. Run `verify.py doctor`. Start over.

- Doctor log has validate, inspect, or pytest and no leftover-scanner `PASS`
- Evidence missing `doctor/leftover-scanner/stdout.txt`
- `--log` on `verify.py`
- `--apply-skills` without a tmp `--skills`
- dest path contains `/.grok/skills/`
- `scripts/release.sh` ran inside nested grok
- `mise use -g`
- `git worktree remove`
- `chmod` on an overlay dest
- cleanup deleted `/tmp/verify-pstack-evidence-*`
- a proof that only shows the process started

Keep the map honest with `/maintain-verification-skill`.
