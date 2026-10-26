---
name: setup-pstack
description: Host-neutral setup entry. Resolves the active host, reads its profiles/<host>.json setup projection, and dispatches to the setup skill that host declares. A host with no setup block, or a candidate host, gets a named GAP, never another host's fallback. Use for /setup-pstack, "configure pstack models", or changing pstack's model or effort choices.
---

# Setup pstack

This skill is the host-neutral entry for pstack model and effort setup. It holds no host file path, no concrete model slug, and no effort enum. It resolves the active host, reads that host's declared setup projection, and hands off.

## 1. Resolve the active host

Identify the harness this session actually runs on from its native surface: the spawn, question, and progress primitives present in this session. Then load `profiles/<host>.json`. The profile is the only declaration of host layout, capabilities, and setup placement: observe the session, and never infer the host from a repository path or from a neighbouring skill.

The **poteto-mode** skill resolves the same active host for routing and skill order; use the same host it selected, together with that host's `references/<host>-tools.md`.

If no profile matches, or the profile declares no `setup` block, report a GAP naming the host and the missing declaration. A `support_state: candidate` host may declare a passive surface, but never a CLI-probing one: report that unproven state instead of probing. Do not run another host's setup steps and do not write another host's files.

## 2. Read the setup projection

`profiles/<host>.json#setup` is a typed block (`schemas/portability/setup-projection.schema.json`, parsed by `scripts/portability_types.py`):

| field | meaning |
|---|---|
| `source` | `host-cli`: the host CLI enumerates models and effort and a host-home config is written. `host-catalog`: role-to-model bindings ship in a repo-projected catalog, so there is nothing to write at runtime. `inherit`: children inherit the parent session model. `none`: this host exposes no model or effort setup surface. |
| `skill` | the skill that owns this host's steps, resolved as `skills/<skill>/SKILL.md`. Present only for `host-cli`. |
| `catalog` | the file the host reads role-to-model bindings from. A `~` path is a host-home write target that may not exist yet; a repo-relative path must exist. |
| `overlay` | per-role overlay directory the setup writes, or `null`. |
| `effort` | `live-enum`: probe the host CLI for its usable levels. `inherit-parent`: no per-role level. `none`: the host exposes no per-role effort. |

`python3 -c "from scripts.setup_pstack import resolve_setup_projection; print(resolve_setup_projection('<host>'))"` returns the same typed value, so a host-neutral caller never re-parses the profile by hand. `None` means that profile declares no setup block.

## 3. Dispatch on `source`

- `host-cli` → follow `skills/<setup.skill>/SKILL.md` exactly as written. That skill owns the probes, the question shape, the validation, and the writes. Report what it wrote.
- `host-catalog` → there is no runtime write. Report the catalog path, that the bindings are projected by `scripts/project_package.py`, and that re-running that projection is what changes them.
- `inherit` → no setup runs. Report that every role keeps the parent session model and the shipped per-role effort from its agent frontmatter.
- `none` → report BLOCKED for this host: no model or effort setup surface is declared. Name the profile key that would have to exist before this host could be configured.

Never substitute one host's setup for another. A missing `setup` block is a GAP to report, not a reason to reuse the nearest host's skill.

## 4. Shared contract

Every host branch obeys these; no host skill may restate or extend them.

**Roles.** `pstack.package.json#roles` is the only role registry (22 keys). A setup skill chooses a model and an effort per canonical role key; it never invents a role, and a panel role stays an array with one spawn per entry.

**Precedence.** `scripts/model_role_resolver.py` `resolve_role_source` owns the ladder: explicit, project, user, host-role, host-tier, inherit-parent, then fail-closed. A setup skill writes the rung its host actually reads (`setup.catalog`, `setup.overlay`); it does not reimplement the ladder.

**Honest status.** `plan_role` answers `PLANNED`, `DEGRADED`, or `BLOCKED` with `evidence_level: static-planning-only`, never VERIFIED. A catalog whose `discovery` is not live degrades an effort plan, and a slug absent from the catalog blocks with no silent substitution. Writing a config file, or reading a projected profile, is not observed host operation: say what was written, not that the host accepted it.

## 5. Spawn-site resolution

A skill that spawns a child resolves two values for its canonical role key, and it does neither by probing or writing itself.

- **Model.** The rung this host reads: `setup.catalog` first, then `setup.overlay`. A key that is missing, `inherit-parent`, or `auto` omits the model, so the child inherits the parent session. A real slug is sent only when this session confirmed it through the host setup skill or a host probe.
- **Effort.** From `setup.effort`. `live-enum` means the host setup skill wrote a per-role level after probing the host CLI. `inherit-parent` and `none` mean nothing per-role was written, so the role agent's frontmatter level is what applies.
- Never invent a slug or a level, and never send an effort field on the spawn call unless the host profile's `runtime_conventions.allowed_spawn_fields` names it.

## 6. Confirm

Name the host, `setup.source`, the skill that ran (if any), and the exact paths that host's steps wrote. If a step was skipped because a catalog, overlay, or CLI probe was unavailable, say which one. Do not name another host's paths.
