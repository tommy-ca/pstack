## Context

Essential entries already lists router, build, how, Benny, spawn, overnight, workflow, and host. HARNESS Skill order already says pstack then user then bundled. Ponytail is a separate enabled plugin on this host (`inspect` skills `ponytail`, `ponytail-review`, `ponytail-audit`). pstack `plugin.json` does not load it. Catalog v1 is pstack only.

In-force ADRs 0001-0005 constrain Benny and Rhai. None of them name ponytail. They still forbid plugin hooks and playbook-to-Rhai clones.

## Goals / Non-Goals

**Goals:** Teach `/ponytail` as the user-layer YAGNI slash after `/poteto-mode`. Lock that in setup, HARNESS, spec, and tests.

**Non-Goals:** Vendoring ponytail. Catalog listing. `commands/` clones. Replacing `/interrogate` with `/ponytail-review`. Auto-entering `/ponytail`. Help/debt/gain on the first-session table.

## Decisions

1. **Modify `pstack-quickstart`, do not add `pstack-ponytail`.** Ponytail is not a pstack capability. A new spec would imply ownership.
2. **Both ledgers, one slash.** Setup Kind `Lazy` with `/ponytail`. HARNESS Need `YAGNI / smallest coding change`: column 1 Laziness Protocol, column 2 `/ponytail` if inspect lists it, column 3 none. Setup-only would teach a slash playbooks never pick. HARNESS-only would hide it from first session.
3. **Skip satellite skills on the table.** `/ponytail-review` and `/ponytail-audit` stay off Essential entries. Do not add them to the Review row. `/interrogate` stays correctness review.
4. **Negative contract on the manifest.** Tests assert `plugin.json` has no `ponytail`. Enable pstack does not grow a ponytail skills path.

Alternatives considered: vendor into `plugin.json` (rejected, Benny pattern is for in-plugin packs). New spec (rejected, false ownership). Setup-only row (rejected, playbooks would not pick it).

## Risks / Trade-offs

- [CI does not install ponytail] -> Docs say skip if inspect does not list it. Tests lock the string in docs, not a live invoke.
- [Operators start from `/ponytail`] -> Keep "Type `/poteto-mode` for rigor. Do not start from `/workflow` or `/goal`." Add that `/ponytail` is after the router.
- [Drift vs HARNESS] -> Tests lock `/ponytail` in both files.

## Migration Plan

Docs and tests only. Reinstall is not required. Operators who already enabled ponytail see the same slash.

## Open Questions

None.
