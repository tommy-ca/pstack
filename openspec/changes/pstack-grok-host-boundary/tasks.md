## 1. Regression coverage

- [ ] 1.1 Add static assertions that babysit uses host `monitor` fields and no local watcher path.
- [ ] 1.2 Add static assertions that orchestrate uses canonical host state and no `scripts/orch` store.
- [ ] 1.3 Add subprocess coverage for compound `git merge` followed by plain `git push` and force-with-lease denial.
- [ ] 1.4 Add manifest parity assertions for root and `.grok-plugin/plugin.json` component paths.

## 2. Host-boundary implementation

- [ ] 2.1 Replace babysit watcher instructions with the host `monitor` contract and recurring scheduler mapping.
- [ ] 2.2 Replace orchestrate local-store instructions with the canonical host and Gas City/Beads boundary.
- [ ] 2.3 Extend the optional Benny guard for compound merge-and-push commands without denying Slack tools.
- [ ] 2.4 Align `.grok-plugin/plugin.json` with the root manifest component paths.

## 3. Verification

- [ ] 3.1 Run the repository harness scanner and focused pytest module.
- [ ] 3.2 Run direct Grok plugin manifest validation from the repository root.
- [ ] 3.3 Run `openspec validate pstack-grok-host-boundary --type change --strict` before archive.
