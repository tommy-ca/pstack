# Leftover Cursor harness scan

Leftover scan walks this plugin tree for live Cursor harness call sites and checks that the grok port still has 22 named playbooks, `opening-a-pr`, 23 principle skills, and a kebab `plugin.json` name.

## Sub-features

- `leftover-tree-walk` fails on live Cursor harness call sites in walked `.md`, `.toml`, `.json`, and `.mjs` files, including `docs/`, plugin `skills/`, and project-local `.grok/skills/`.
- `leftover-playbooks` requires 22 named playbooks plus `opening-a-pr.md`.
- `leftover-principles` requires 23 `principle-*` skill directories.
- `leftover-plugin-json` requires `plugin.json` name `pstack` and skills paths `./skills/` plus `./automations/benny-grok/skills/`. It must not list `.grok/skills`.
- `leftover-pass-line` prints `PASS` and exits 0.

## How to get to it (user POV)

- From the plugin checkout, run `python3 scripts/verify-harness.py`.
- Run `python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .`.
- Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature leftover-scanner`.

## Driving it with verify.py

Preconditions:

- cwd is the pstack plugin checkout.
- `python3` is on `PATH`.
- Doctor for this run has not yet been skipped.

- **Required doctor.** Run leftover scanner before any other feature. Run `python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .`. Exit code `0`. Evidence `doctor/leftover-scanner/stdout.txt` contains a line `PASS`, `playbooks: 22 named + opening-a-pr`, `principles: 23`, and `plugin.json name: pstack`. Evidence `doctor/plugin-validate/stdout.txt` contains `Plugin manifest is valid.`
- **Operator entry.** Drive the same scanner as a mapped feature. Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature leftover-scanner`. Exit code `0`. Feature evidence repeats leftover `PASS`.
- **Direct CLI.** Run the operator command itself. Run `python3 scripts/verify-harness.py`. Exit code `0`. First stdout line is `PASS`.
- **Proof.** Read `doctor/leftover-scanner/stdout.txt` and `doctor/leftover-scanner/exit.txt`. The exit file is `0`. The stdout file is not pytest `-q` output and is not `grok inspect` JSON.

## Gotchas

- `grok plugin validate .` and `grok inspect --json` are not leftover scanner. Validate is doctor companion only. Inspect `enabled` is trust.
- `uv run --with pytest pytest tests/test_verify_harness.py` is not leftover scanner. The tree walk is `scripts/verify-harness.py`.
- TEST-PLAN.md says verify-harness is not an EDITH pass gate. This map still requires leftover `PASS` as doctor.
- Scanner skip dirs are `.git`, `automations`, `scripts`, `.superpowers`, `.worktrees`, `openspec`, and `.audit`. A leftover `PASS` does not mean skipped dirs are clean. Skills markdown is not a skip dir. `docs/` is walked. `.grok` is not a skip dir. Project-local skill markdown stays scanned. Doctor still fails if `.grok/workflows` exists.
- Scanner skip files are `HARNESS.md`, `UPSTREAM`, `TEST-PLAN.md`, `README.md`, `README.zh-CN.md`, `codex-tools.md`, `provider-dispatch.md`, and `classification.tsv`. Those names may mention Cursor leftovers. Skills markdown must not keep them as call sites.
- Allowed mentions such as `There is no cursor-team-kit` and `classification.tsv` notes must not be treated as live hits.
- leftover-scanner is not leftover-clone and not leftover_count from worktree-drop. Isolation reclaim is worktree-cleanup.
- Later `drive` on the same `--run-id` for other features refuses if leftover scanner did not PASS.
- `HARNESS.md`, `scripts/`, and `automations/benny` may name Cursor leftovers. Skills markdown must not keep them as call sites.
