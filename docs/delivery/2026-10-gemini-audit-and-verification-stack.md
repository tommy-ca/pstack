# Verification audit and delivery record

The original four-PR stack covers executable shims, Antigravity plugin hygiene, skill metadata, and durable verification receipts. The resumed audit found concrete gaps in that stack and in verification scaffolding. The user's current instruction authorizes corrective PRs, independent verification, and bottom-up merges.

This record supersedes the earlier proposed lane counts, screenshot requirements, unmeasured performance baselines, and operator-only landing protocol. Those were planned steps, not completed evidence. CLI behavior is proved with retained commands, output, exit codes, and observable file state.

## Existing stack

| PR | Scope | Audit result and correction |
| --- | --- | --- |
| #210 | Preserve executable shim identity | Relative PATH entries failed after changing execution directories. Selected paths now become absolute without dereferencing symlinks. Regression fixtures execute the actual drivers. |
| #211 | Remove foreign plugin directories | Independent exact-commit verification passed. A pre-existing dry-run write is tracked in the corrective sync PR. |
| #212 | Validate matching kebab-case skill names | The original parser accepted malformed delimiters and rewrote body examples. A bounded shared frontmatter reader validates selected scalars, rejects duplicates and continuations, and preserves body examples and line endings. |
| #213 | Refresh the five-host receipt matrix | The original Codex receipt had a stale package fingerprint. Receipts must be regenerated from the corrected source and checked before landing. |

## Corrective stack

Each behavioral slice keeps its regression tests with its implementation.

1. Make Antigravity dry-run read-only and check managed skills, agents, commands, manifests, and models for content drift. Copy and check the same directory-symlink contents. Ignore generated dependencies and bytecode.
2. Refuse unsafe application names and occupied or symlink scaffold targets before writing. Preserve authored drafts on rerun.
3. Validate complete ordered feature maps and their regular sibling files. Document all six scaffold destinations and distinguish structural validity from runtime proof.
4. Fingerprint verification tool dependencies, align OpenSpec coverage target in doctor (#214), handle candidate host staleness safety, and regenerate the durable 6-harness receipt matrix. Changing verifier logic must invalidate earlier evidence.

The scaffold's six destinations include Droid. The portable conformance sweep covers all declared harnesses: Grok, Codex, OMP, OpenCode, Antigravity, and Droid.

## Verification and landing gates

- Run focused regression tests and the actual operator CLIs.
- Run the Python suite, Bun tool tests and TypeScript checks, package projections, and host-boundary checks on the integrated source.
- Run plugin doctor and every feature in its maintained verification map. Keep evidence after cleanup.
- Give every PR an independent verdict with its exact head, base, and stable patch ID. Re-verify changed patches.
- Inspect review threads, checks, and mergeability. Use GitHub CLI because Origin is unavailable.
- Merge only the contiguous passing run, squash one PR at a time, and reconcile only the next bottom PR against trunk after each merge.
- Confirm the final merged source and receipt freshness.

No host monitor or scheduler is available in this Codex session. Forge status is checked during the bounded shipping run.

## Evidence boundaries

Passing native CLI discovery and static spawn bindings do not prove that a model-backed child ran on every host. Receipt claims are interpreted within the scenarios actually executed. Draft scaffold checks assess structure only; application runtime proof requires a tailored driver and real user-path evidence.

The arena selected one bounded shared metadata reader over duplicate local parsers. Separate worktrees protect concurrent writers. Sequence Work into Verifiable Units determines PR boundaries; Prove It Works determines the regression and CLI gates.

Correctness defects are tracked in [issue #217](https://github.com/tommy-ca/pstack/issues/217). Independent verdicts and final validation summaries are posted on the PRs so they survive this session.
