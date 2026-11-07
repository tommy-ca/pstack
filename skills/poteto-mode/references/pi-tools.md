# Standalone Pi 1.5.0 candidate tool mapping for PStack

Status: **candidate, STATIC-ONLY**. Candidate host identity is declared in the safe profile filename `profiles/pstack-pi.json`. This is not the OMP adapter. It does not claim actual native Pi child or sandbox execution.

## Skill discovery

The repository-local `.pi/settings.json` uses Pi's **native** `skills: ["../skills"]` resource list to load canonical PStack skills and the pi-subagents `agentScanDirs: ["../agents"]` to load existing canonical role definitions without copying them. Both paths resolve relative to `.pi/`; `projectRootResolution: "git-root"` holds in worktrees. Project resource settings load after project trust; no npm package is auto-installed. `.pi/skills/` additionally contains Pi-specific verification skills. Open `/skill:poteto-mode`, `/skill:swarm`, `/skill:arena`, `/skill:interrogate` directly. If the existing `@zenspc/pi-pstack` exposes colliding skills, disable its skills; do not silently run two PStack policies.

## Tool and role mapping

| PStack operation | Pi runtime / extension | Evidence |
| --- | --- | --- |
| Read/edit/write/shell | native `read`, `edit`, `write`, `bash` | documented, no local Pi binary run |
| Skill/role discovery | native Pi skills from `.pi/settings.json` | static config only; check project trust and skill listing |
| MCP and codemode | built-in Pi extensions | documented, not a separate installed package |
| Spawn/join/cancel | `pi-subagents@0.86.0`, requires `subagent_launch` permission | version-gated; no observed child |
| Schedule/monitor | same pi-subagents missions and schedules | version-gated; restart/catch-up proof missing |
| Worktree isolated writers | pi-subagents worktree mode, when enabled | version-gated; not kernel isolation |
| Hard readonly | explicitly enabled pi-better-sandbox OS confinement | NOT PROVEN; tool-only restrictions are advisory |
| Tool-call autonomous approval | pi-verdict@0.16.0 `tool_call` rules/classifier | version-gated; not an OS or non-bypassable hard gate |
| Ask human | pi-ask-user@0.17.2 `ask_user` sequential choices | version-gated; does not authorize effects |
| Human gate | independent action authorization + separate tool gate | GAP: neither model allow nor ask_user proves a hard gate |
| Research fetch/search | pi-web-access, only when profile authorizes | optional research profile |
| Evidence/verification | existing PStack verifier + project-local Pi verification skills | offline checks only |

## Subagent and sandbox rules

Use **one** delegate engine and **one** sandbox owner. Freeze child roles and run bounds before dispatch. Parent owns spawn, status, join, cancellation and synthesis. Treat `subagent_launch` refusal, expired deadline, cancelled child or unobserved model slug as BLOCKED/UNTESTED rather than PASS. Never claim multi-model diversity without actual resolved model identities. Verify Main, Subagents and Background sandbox profiles are actually ON; configure stored credentials and outside-project accesses to Deny or narrow read explicitly. Extension code itself remains trusted process code and may bypass sandboxed file tool rules. Source: https://pi.dev/packages/pi-better-sandbox and https://github.com/nicobailon/pi-subagents/releases/tag/v0.86.0 .

## Verification

```sh
python3 scripts/verify_pi_candidate.py check
python3 scripts/verify_pi_candidate.py model
python3 scripts/verify_pi_candidate.py smoke # Tier 2; BLOCKED if Pi not installed
bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive # Tier 3 BLOCKED until real driver
```

Source evidence is **not** runtime parity. For validation see issue #897; for security/formal proof see issue #898. Do not use the OMP RPC paths, receipt names or `task` invocation as a standalone Pi primitive.

## Authorization semantics for PStack

`pi-verdict@0.16.0` is the single chosen semantic tool-call adjudicator; `pi-better-sandbox` is a separate OS isolation owner, not a competing approval engine. The Pi permission hook is conditional on the extension being loaded and on its `/automode` switch. The example in `references/pi-verdict-pstack.example.json` is not an installed policy. Model classifier `allow` means an opinion, not proof of safety or human approval; `ask` asks through native Pi UI and denies headless. `pi-ask-user` collects independent requirement/selection responses and cannot enforce subsequent side effects.

Use PStack's `low-risk reversible` / `ambiguous` / `privileged` risk classes. Independently block privileged tools, child launch permissions and out-of-policy filesystem/network effects even when a model votes allow. Validate that `pi-verdict` has not been switched off, deterministic floor is enabled, `ignoreTools` does not exclude sensitive custom/MCP/subagent calls, and an unavailable primary classifier is not rescued by an unreviewed fallback. Its native audit records gray-zone decisions, not every action or OS effect. Sandbox switches, denied credentials and detached actors require separate observed receipts. See #897 and #898.

## 2026-11-07 Pi native package and evidence correction

The repository checkout `.pi/settings.json` is **not** an installable Pi package manifest. The separate `references/pi-essential-extensions.json` is a reviewed PStack policy/inventory, **not read by Pi**. The proposed thin Pi-native package would declare only `package.json#pi.skills: ["./skills"]`, with no bundled executable Pi extensions. Its skill discovery and `pi-subagents.agentScanDirs` role discovery require independent native package smoke checks before claiming distribution parity. Keep the existing root six host adapters unchanged. Source contract: [Pi native package documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md).

**Version drift:** `pi-subagents@0.86.0` remains the pinned candidate. [v0.87.0 (2026-11-07)](https://github.com/nicobailon/pi-subagents/releases/tag/v0.87.0) is an *unverified upgrade candidate*, with drain stop, strict `provider/id` and multi-session fixes. Do not silently switch installed or pinned versions. A source release is not an observed native result.

**Proof correction:** `scripts/prove_pi_vertical_slice.py --live` currently checks binary/version, `pi list`, and a `pi -p --no-session --no-tools` probe; it does **not** launch a child or enforce/test OS sandbox. Even with matching packages and successful echo, the **runtime plane remains BLOCKED**, never `observed_live`. The `cleanup` helper also returns BLOCKED if it has not tracked and verified actual child/worktree cleanup. See `.pi/skills/verify-pi-pstack/features/extension-package.md` and [follow-on epic #973](https://github.com/tommy-ca/pstack/issues/973). Source contracts and 53 bounded negative mutants remain only offline evidence. No mandatory human.gate is proved by pi-verdict.
