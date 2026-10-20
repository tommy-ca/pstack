# Upstream pstack 0.15.29 reconciliation — 2026-10-20

## Source of truth and intentionally unfinished status

- Canonical source: [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack) at monorepo commit `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (upstream `pstack/plugin.json` version `0.15.29`).
- Last **applied** upstream source: `1dcc2bacde73ddd284803b7af28164d0436198fc`, pinned by `UPSTREAM` and `pstack.package.json#upstream_pin` (`0.15.21-grokbuild.0`).
- Port main at audit: `0c63bf6bb258f1026710b4c2c65e9863d17e5f21`.
- **Do not change applied pins or claim complete sync** on this PR. Four isolated source-identical semantic leaf skills are being ported ahead of the higher-risk reconciling changes. Formal program: [#622](https://github.com/tommy-ca/pstack/issues/622); [import leaf #624](https://github.com/tommy-ca/pstack/issues/624).

## Baseline measurements

At this frozen target, local tree contains 816 blob paths and upstream `pstack/` contains 172. The SHA/path comparison finds 63 identical shared blobs, 94 differently-contented shared paths, 15 upstream-only paths (including excluded assets, manifests, images and Cursor-specific references), and 659 port-only paths. **These are whole-tree comparisons, not the amount of work or new behavior introduced by 0.15.29.** Comparing `1dcc2bac..88d47514` in the whole Cursor monorepo counts 76 commits; isolate `-- pstack/` to determine this plugin's actual changed paths.

The port-only paths include native harness descriptors, profiles, drivers, issues/specs, evidence and tests. Overwriting shared path names or replacing the whole tree is not a valid sync strategy.

## Classification of this reviewable slice

| Source file | Decision | Evidence / caveat |
| --- | --- | --- |
| `skills/create-formal-verification-skill/SKILL.md` | preserve canonical | Host-independent guidance about model checks, code-aligned invariants and negative controls; no hardcoded Cursor tool calls |
| `skills/maintain-formal-verification-skill/SKILL.md` | preserve canonical | Drift lifecycle and fail-first truthfulness; reports bug vs verification drift without editing product code |
| `skills/in-your-own-words/SKILL.md` | preserve canonical | Small semantic prompt with no runtime binding |
| `skills/sharpen/SKILL.md` | preserve canonical | Prompt-improvement utility with no runtime binding |

`create-formal-verification-skill` is **not** a replacement for existing `create-verification-skill`: one models program properties, the other scaffolds observable app verification. Existing shared skills discovery should find the new leaves directly without a new host router.

## Intentionally deferred / excluded surfaces

- **Adapt:** `poteto-mode` router and triggers; changed principle leaves; Interrogate/Arena/Swarm adjudication; shipping, autopilot, orchestration playbooks; `orch/store.ts` / `orch.ts` and their tests; `watch-pr`; `worktree-audit.sh`. They carry state/behavior or host protocol differences. See [#625](https://github.com/tommy-ca/pstack/issues/625), [#626](https://github.com/tommy-ca/pstack/issues/626), [#627](https://github.com/tommy-ca/pstack/issues/627).
- **Decide adapter/documentation:** new upstream `docs/harness/claude-code.md`. The port already has a `.claude-plugin`; copying the Cursor mapping as six-host parity proof would be wrong. See [#628](https://github.com/tommy-ca/pstack/issues/628).
- **Exclude with rationale:** `.cursor-plugin/plugin.json`, branding asset/screenshots and Cursor-only `make-bot-ui` under existing policy. Do not copy upstream `plugin.json` over host descriptor generator output.
- **Keep truthful metadata:** no bump of `UPSTREAM`, package pin or canonical inventory while unclassified/untested semantic deltas remain. See [#623](https://github.com/tommy-ca/pstack/issues/623) and [#629](https://github.com/tommy-ca/pstack/issues/629).
- **Final gate:** independent exact-head Swarm / Interrogate, conditional Arena, evidence by harness at [#630](https://github.com/tommy-ca/pstack/issues/630). An offline contract pass never certifies native spawn/join.

## Verification and acceptance

Run from a checkout of the candidate PR:

```sh
python3 scripts/verify-harness.py
python3 scripts/project-package.py --check
python3 scripts/canonical-index.py --check
python3 -m pytest -q tests/test_skill_frontmatter.py tests/test_canonical_index.py tests/test_project_package.py
```

Check that all four files have the correct frontmatter `name`, appear under shared `skills/`, and contain no literal Cursor task/ask-user primitives or model-role bindings. Build the additional test/proof slices in their respective issues. **No CI or runtime proof is claimed in this document.**

## Graph

`#623` (frozen source classification) → `#624` (this import); `#625` (principles/router); `#626` (orchestration); `#627` (shipping); `#628` (packages/docs). After all: `#629` (pin/inventory) → `#630` (final exact-head review) → epic `#622` closure.

Principles: Build the Lever, Model the Domain, Boundary Discipline, Test Behavior Not Implementation, Sequence Work into Verifiable Units, Prove It Works. Avoid duplicating a sync framework or accepting an unverified PASS.
