# System, code and data design — one PStack setup skill

## Layering / ownership

~~~text
Pinned cursor/plugins/pstack setup semantics (UPSTREAM @88d47514)
    |
    v
skills/setup-pstack/SKILL.md      single human-invocable setup skill
    |  observe active host (same host identity as poteto-mode)
    |  read typed host profile from canonical packaged directory
    +--> pstack.package.json#roles          canonical 22 role IDs/panels
    +--> scripts/model_role_resolver.py     canonical model precedence
    +--> scripts/setup_pstack.py            existing setup/profile helpers
              |
              v
       SetupProjection.source
         host-cli (currently Grok) -> references/<matched-profile-stem>.md
                                   -> host-only detect/ask/validate/write
         host-catalog             -> report existing native projected catalog
         inherit                  -> no override write
         none / absent / candidate -> named BLOCKED or GAP
              |
       confirm exact action and evidence tier

poteto-mode/references/<host>-tools.md : host tool/spawn syntax only
QStack -> independently installed poteto-mode : one-way downstream overlay
No orchestration engine, agent scheduler, provider gateway, or duplicate router
~~~

## Semantic atoms and source of truth
| Atom | Owner | Invariant |
| --- | --- | --- |
| Upstream role/budget intent | pinned Cursor setup skill | Adapt to proven host surface, do not copy Cursor slugs as Grok defaults |
| Exact active host ID | scripts/host_identity.py + validated HarnessProfile | `github:copilot` is not `copilot`; filename never grants capabilities |
| Setup state/source | existing SetupProjection + setup-projection.schema.json | no `skill` or `reference` field after caller migration |
| Setup reference selection | validated profile path + small existing setup helper | `references/<matched-profile-stem>.md`; no user path |
| Role taxonomy | pstack.package.json#roles | 22 keys, scalar/panel topology preserved |
| Override precedence | scripts/model_role_resolver.py | explicit > project > user > host-role > host-tier > inherit or BLOCKED |
| Grok model/effort discovery | setup-pstack/references/grok.md | only slugs / effort tokens proven on live host |
| Writes | host-specific native reference + current scoped helper | only managed files; idempotent and user-safe |
| Profile source | skills/setup-pstack/profiles/ | edit once, generate root compatibility copy |
| Proof | verification skills / offline contracts / native smoke | static config write != live host model acceptance |

## Minimal existing data schemas — no new registry

### SetupProjection: final typed shape
The current `scripts/portability_types.py::SetupProjection` and `schemas/portability/setup-projection.schema.json` are the **only** implementation carriers. Change them in place; this is a specification of their eventual shape, not a new schema file.

~~~python
@dataclass(frozen=True)
class SetupProjection:
    source: Literal["host-cli", "host-catalog", "inherit", "none"]
    effort: Literal["live-enum", "inherit-parent", "none"]
    catalog: str | None = None
    overlay: str | None = None
# NO "skill" field; NO "reference" field. The native reference is derived.
~~~

| source | effort | catalog | overlay | host-specific instructions | allowed action |
| --- | --- | --- | --- | --- | --- |
| host-cli | live-enum | required host-home path | optional host-home path | derived by matched profile filename | scoped native probe/write |
| host-catalog | none | required repo-projected path | forbidden | none | report project-time projection; no runtime write |
| inherit | inherit-parent | forbidden | forbidden | none | omit model override; no runtime write |
| none | none | forbidden | forbidden | none | report BLOCKED; no runtime write |
| absent `setup` | n/a | n/a | n/a | none | explicit GAP, no fallback |

Candidate `support_state` MUST reject `host-cli`. Each setup object MUST reject unknown keys and disallowed source-field combinations (JSON Schema Draft 2020-12 `oneOf`/conditionals, with current `SetupProjection.validate` checking the same semantic matrix). A catalog string must not be used as a native path until the selected host declares that layout; project-relative values require projected-file existence, and host-home values must stay in the selected host's allowed subtree.

### Canonical host example (existing grok.json, proposed field removal)
~~~json
{
  "host": "grok",
  "support_state": "packaged",
  "setup": {
    "source": "host-cli",
    "catalog": "~/.grok/pstack-models.toml",
    "overlay": "~/.grok/roles",
    "effort": "live-enum"
  }
}
~~~
Only the `setup` block is a proposed delta; all other existing HarnessProfile fields remain as shipped. Both packaged and generated root copies MUST be byte-identical. `profiles/copilot.json` has `host: github:copilot`; resolve the real filename by exact profile ID match first.

### Reference convention is a path derived from validated data, not a field
~~~python
# Conceptual behavior inside existing scripts/setup_pstack.py; not shipped code.
profile_path, typed_profile = load_exact_declared_profile(active_host)
projection = validate_setup(typed_profile.setup, typed_profile.support_state)
if projection.source == "host-cli":
    # Use profile_path.stem, not the untrusted host string and not a new field.
    reference = SETUP_SKILL / "references" / (profile_path.stem + ".md")
    require_regular_file_inside(reference, SETUP_SKILL / "references")
    read_only_selected_host_reference(reference)
# Other source modes never resolve or load a host-specific setup reference.
~~~
Inputs to `load_exact_declared_profile` MUST be validated IDs from `scripts/host_identity.py`, and match the JSON `host` value exactly. Both the profile and the reference must be in the trusted package and not an escaping symlink; invalid/missing reference -> GAP/BLOCKED without defaulting to another host. Keep this a small utility, not a general adapter abstraction. A test must reject host-ID filename mismatches and attempting to select `references/grok.md` while running as Codex.

## Code flow (runtime)
1. **Identify** active harness by actually available host primitives; validate the ID and locate the one matching packaged profile (allow root mirror only after parity check).
2. **Parse** and validate raw JSON at the boundary into existing `HarnessProfile` and `SetupProjection`; reject invalid source shapes, candidate `host-cli`, unsafe paths or extra fields.
3. **Select** a host-local setup reference only if `source=host-cli`. Select by validated profile filename stem; do not fall back to `setup-pstack-grok` or a guessed different host.
4. **Discover** available models/effort via native declared interface; load current configured state, use 22 canonical roles plus existing pure precedence. For `host-catalog` report the already projected catalog; for `inherit`, `none`, missing setup no runtime write.
5. **Offer** host-supported budget/role/panel choices and validate against actual available slugs/tokens before writing. Missing catalog/invalid token -> BLOCKED, no silent family/host substitution.
6. **Persist** only managed native targets, with idempotent replacement and safe user-owned file preservation. Grok: `~/.grok/pstack-models.toml` + `~/.grok/roles/pstack:<key>.toml` only, never Cursor rules.
7. **Report** host, source mode, exact paths modified (or no-write), effort/model provenance, degraded or blocked state, and evidence tier. A written file is not proof a child ran.
8. **Offer optionally** `create-verification-skill` and `create-formal-verification-skill` when the project lacks the respective verification skill. These are distinct explicit follow-up invocations, not setup-file writes; avoid `verify-pstack` name collision or automatic generation.

## Data flow / source distribution
~~~text
skills/setup-pstack/profiles/*.json  [canonical machine-readable data]
       -> validate schema / host IDs / complete set
       -> existing packaging/projection code generates profiles/*.json mirror
       -> assert byte-for-byte parity in tests and packaging
       -> distribute packaged skills and required mirror without extra edit authority
       -> resolve host by validated ID and profile filename
       -> consume setup.source and only matching native reference
       -> report native state/evidence, not fake model availability
~~~
Current `resolve_profiles_dir` prefers root if it exists, while tests designate packaged as canonical. Converge by explicitly changing the resolver to prefer the packaged source; when *both* are present, verify full mirror parity before any setup target is selected. Installed plugin without root continues to function. Do not remove root until the current `package_lifecycle`, `prove_antigravity_native_package`, `sync_antigravity_plugin`, `adapt_harness`, driver/test and `verify_harness` consumers have all migrated; recent `main` modifies several of those files, so no implementation wave may discard them.

## Grok aliases, model/effort shape and exact budget limits
- Model `inherit-parent`/`auto` -> omit `task.model`; Grok plugin agent inherits the parent model.
- Grok `[effort].role = inherit-parent/auto` -> remove the **managed role overlay only**. Shipped agent-frontmatter `effort` still wins when present; do NOT falsely claim the parent session's effort is directly inherited.
- Array/panel role choices preserve cardinality and provenance. Multiple entries in one identical model family are multiple requests, not proof of independent model diversity or completed worker executions.
- Grok uses its live `use one of:` CLI enum, not reserved parser tokens or Cursor budget strings. Defaults and effort ladder remain in native setup references. Static presets are labeled ship-time snapshots, not live discovery.
- Original Grok skill's `Write only ~/.grok...` statement governs the **setup mutation phase**, while optional verification authoring is a separate requested action and must be described as such. Do not silently generate app skills during model setup.

## Migration sequence and failure containment
**Single coordinated internal migration wave** (separate reviewable implementation PRs may stack; no intermediate publicly released broken state):
1. Freeze pinned source and complete caller inventory (#949).
2. Accept this OpenSpec MODIFIED requirements change (#950); verify schema conditional design before execution.
3. Move Grok 15KB body to `skills/setup-pstack/references/grok.md`, its four refs to `references/grok/`, update relative links, and keep neutral SKILL under host path/slug boundary scans.
4. Migrate all `setup.skill` readers, two `grok.json` copies, existing typed model/schema, tests, `scripts/verify_harness.py`, `scripts/scan_host_boundary.py`, `scripts/adapt_harness.py`, package verifier and manifests. Delete old public skill **in the same wave**, not after shipping a permanent dual-mode shim (#951).
5. Make packaged profiles editable authority, generate root mirror using current packaging helpers, update resolver preference/parity, regression and stale-mirror tests (#952). Only remove root in a later explicit compatibility decision.
6. Run targeted and full offline tests, OpenSpec CLI when available, exact SHA package proofs, and real-host smoke where available. Independent Swarm/Arena/Interrogate and Thermos review require real outputs/receipts (#953).

Rollback restores previous skill, projection and generated data consistently; never restore only one half of the schema/reader pair. Classify native checks unrun as NOT_RUN/BLOCKED, not a blanket PASS.
