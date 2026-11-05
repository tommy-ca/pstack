# Standalone Pi 1.5.0 candidate tool mapping for PStack

Status: **candidate, STATIC-ONLY**. Candidate host ID `pstack:pi`, safe profile filename `profiles/pstack-pi.json`. This is not the OMP adapter. It does not claim actual native Pi child or sandbox execution.

## Skill discovery

The repository-local `.pi/settings.json` uses Pi's **native** `skills: ["../skills"]` resource list to load this repository's canonical PStack `skills/` directory (relative to `.pi/`). Project resource settings load after project trust; no npm package is auto-installed. `.pi/skills/` additionally contains Pi-specific verification skills. Open `/skill:poteto-mode`, `/skill:swarm`, `/skill:arena`, `/skill:interrogate` directly. If the existing `@zenspc/pi-pstack` exposes colliding skills, disable its skills; do not silently run two PStack policies.

## Tool and role mapping

| PStack operation | Pi runtime / extension | Evidence |
| --- | --- | --- |
| Read/edit/write/shell | native `read`, `edit`, `write`, `bash` | documented, no local Pi binary run |
| Skill/role discovery | native Pi skills from `.pi/settings.json` | static config only; check project trust and skill listing |
| MCP and codemode | built-in Pi extensions | documented, not a separate installed package |
| Spawn/join/cancel | `pi-subagents@0.85.0`, requires `subagent_launch` permission | version-gated; no observed child |
| Schedule/monitor | same pi-subagents missions and schedules | version-gated; restart/catch-up proof missing |
| Worktree isolated writers | pi-subagents worktree mode, when enabled | version-gated; not kernel isolation |
| Hard readonly | explicitly enabled pi-better-sandbox OS confinement | NOT PROVEN; tool-only restrictions are advisory |
| Ask human | pi-ask-user `ask_user` | version-gated; does not authorize effects |
| Human gate | independent action authorization | GAP: ask_user alone cannot enforce approval |
| Research fetch/search | pi-web-access, only when profile authorizes | optional research profile |
| Evidence/verification | existing PStack verifier + project-local Pi verification skills | offline checks only |

## Subagent and sandbox rules

Use **one** delegate engine and **one** sandbox owner. Freeze child roles and run bounds before dispatch. Parent owns spawn, status, join, cancellation and synthesis. Treat `subagent_launch` refusal, expired deadline, cancelled child or unobserved model slug as BLOCKED/UNTESTED rather than PASS. Never claim multi-model diversity without actual resolved model identities. Verify Main, Subagents and Background sandbox profiles are actually ON; configure stored credentials and outside-project accesses to Deny or narrow read explicitly. Extension code itself remains trusted process code and may bypass sandboxed file tool rules. Source: https://pi.dev/packages/pi-better-sandbox and https://github.com/nicobailon/pi-subagents/releases/tag/v0.85.0 .

## Verification

```sh
python3 scripts/verify_pi_candidate.py check
python3 scripts/verify_pi_candidate.py model
python3 scripts/verify_pi_candidate.py smoke # Tier 2; BLOCKED if Pi not installed
bash .pi/skills/verify-pi-pstack/scripts/driver.sh drive # Tier 3 BLOCKED until real driver
```

Source evidence is **not** runtime parity. For validation see issue #897; for security/formal proof see issue #898. Do not use the OMP RPC paths, receipt names or `task` invocation as a standalone Pi primitive.
