## 1. Regression coverage

- [x] 1.1 Add static assertions that babysit uses host `monitor` fields and no local watcher path.
- [x] 1.2 Add static assertions that orchestrate uses canonical host state and no `scripts/orch` store.
- [x] 1.3 Add subprocess coverage for compound `git merge` followed by plain `git push` and force-with-lease denial.
- [x] 1.4 Add manifest parity assertions for root and `.grok-plugin/plugin.json` component paths.

## 2. Host-boundary implementation

- [x] 2.1 Replace babysit watcher instructions with the host `monitor` contract and recurring scheduler mapping.
- [x] 2.2 Replace orchestrate local-store instructions with the canonical host and Gas City/Beads boundary.
- [x] 2.3 Extend the optional Benny guard for compound merge-and-push commands without denying Slack tools.
- [x] 2.4 Align `.grok-plugin/plugin.json` with the root manifest component paths.

## 3. Verification

- [x] 3.1 Run the repository harness scanner and host-boundary pytest selection.
- [x] 3.2 Run direct Grok plugin manifest validation from the repository root.
- [x] 3.3 Run `openspec validate pstack-grok-host-boundary --type change --strict` before archive.
