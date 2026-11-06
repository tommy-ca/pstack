# System design: harness-agnostic model setup without a second setup engine

## Responsibility architecture

~~~text
Official Cursor PStack setup semantics (source of engineering intent)
       |
       v
skills/setup-pstack/SKILL.md    (one public entry, neutral process)
       |
       +-> pstack.package.json#roles  (one role registry)
       +-> scripts/model_role_resolver.py (one precedence planner)
       +-> skills/setup-pstack/profiles/<host>.json
                | setup.source, setup.reference, catalog, overlay, effort
                v
       skills/setup-pstack/references/<host>.md
                |
       +--------+-------------------+-----------------------+
       |                            |                       |
    host-cli                     host-catalog            inherit/none
    e.g. Grok                   Codex/Antigravity       candidate or GAP
    native probe/write          projected native file   no host writes
       |                            |                       |
       +----------------------------+-----------------------+
                                    |
                         confirm exact outcome + proof tier

poteto-mode/references/<host>-tools.md: separate playbook tool/spawn consumption
External agent orchestrators / qorch: no setup ownership or reverse imports
~~~

## Semantic building blocks
| Atom | Owner | Contract |
| --- | --- | --- |
| Scope and host identity | setup-pstack + typed profile | Match installed active host, not path/stem guess |
| Role taxonomy | pstack.package.json#roles | No new role list; preserve scalar/panel shape |
| Availability discovery | selected native reference | Only observed entitled slugs; no model guesses |
| Budget and effort | Cursor setup intent + host reference | Offer choices supported by actual host enum; no cross-host tokens |
| Precedence | scripts/model_role_resolver.py | Explicit > project > user > host-role > host-tier > inherit; fail closed |
| Persist or project | typed setup.source | Host-cli isolated write; host-catalog reports projection; inherit/none no write |
| Verification status | existing verification skills | Static plan/config write is NOT native-run evidence |
| Safe recovery | selected host reference | Idempotent changes, user ownership preserved, changes reported |

## Typed delta to existing SetupProjection (proposal only)
`SetupProjection` already has `source`, `effort`, `skill?`, `catalog?`, `overlay?`. Add an optional relative `reference` in the existing schema/dataclass; do not create a new model or provider registry.

~~~ts
type SetupSource = "host-cli" | "host-catalog" | "inherit" | "none";
interface SetupProjectionVNext {
  source: SetupSource;
  effort: "live-enum" | "inherit-parent" | "none";
  reference?: string | null; // "references/grok.md", relative to skills/setup-pstack/
  skill?: string | null;     // legacy only while migrating readers
  catalog?: string | null;   // existing declared native path
  overlay?: string | null;   // existing declared native overlay
}
~~~

**Migration:** first accept `skill` or `reference` (exactly one) for `host-cli`, but do NOT silently fall back from an invalid reference to the legacy skill; migrate Grok profile, all callers and tests; then remove `skill` from the schema and profile after packaging succeeds. Non-host-cli source values must have neither field. Validate relative paths: no `..`, absolute path, symlink escape, directory, or missing file. A candidate host cannot declare CLI probing.

## Code flow
1. Observe active host capability (as poteto-mode already does); resolve exact declared profile `host` ID from the same packaged profile source.
2. Parse and validate the `setup` block using existing `scripts/portability_types.py` and `scripts/setup_pstack.py` helpers.
3. For `host-cli`, read its validated local reference; for `host-catalog`, report the existing projected file; for `inherit` and `none`, make no writes and report the relevant status.
4. Use `pstack.package.json#roles` and the existing pure model resolver to build available, correctly shaped role/panel choices. Preserve upstream budget intent without assuming that every host accepts Cursor's `max/xhigh` slugs.
5. Validate observed model/effort availability, user choice, host support status and write destination. Invalid/unknown/denied -> BLOCKED/GAP and zero writes.
6. Execute only the active host's native config operation. Grok remains limited to `~/.grok/pstack-models.toml` plus pstack-namespaced role overlays; never rewrite user-owned unrelated files.
7. Confirm what was actually written/projected, how to reload, and what was NOT proven. Optional project-local verification skill offer stays in the common setup process, with no duplicate generator.

## Grok effort alias nuance
On the existing Grok adapter, model `inherit-parent`/`auto` omits `task.model` and uses the parent's model. But `[effort].<role> = inherit-parent` or `auto` removes only the managed role overlay; the plugin agent's shipped frontmatter `effort` still applies. It must not be described as guaranteed inheritance of parent-session effort. The host reference owns this clarification and its negative test, not the neutral SKILL body.

## Profile data flow
~~~text
skills/setup-pstack/profiles/*.json (canonical editable input)
  -> validate HarnessProfile / SetupProjection
  -> existing package projection or staging emits root profiles/ compatibility mirror
  -> packaged plugin includes canonical setup profiles (and temporary root copy where required)
  -> resolve_profiles_dir reads canonical path, or validated legacy mirror only in compatibility mode
  -> installed and repo consumers observe identical declared data
~~~
Guard against stale mirrors by byte parity and fail closed rather than silently preferring whichever directory happens to exist. Do not remove the root mirror until `scripts/drivers/base.py`, `verify_portable.py` callers, `tests/test_setup_projection.py`, Antigravity proof/staging and live package consumers are reconciled.

## Migration impact
- Move `skills/setup-pstack-grok/SKILL.md` to `skills/setup-pstack/references/grok.md`, preserving live CLI detection, question order, role overlays and Grok-specific constants only there.
- Move its four reference assets to `skills/setup-pstack/references/grok/`; revise relative links and all Grok-only skill citations.
- Update existing `SetupProjection`, schema, `resolve_setup_projection`, profile `grok.json` in source and mirror, compatibility projectors and package manifests.
- Update `tests/test_setup_projection.py`, `tests/test_verify_harness.py`, `tests/test_scan_host_boundary.py`, `tests/test_harness_profiles_sync.py`, `scripts/verify_harness.py`, scanner exemptions, README/README.zh-CN, TEST-PLAN, and relevant source/fixture hashes. Delete old skill only after consumers pass.
- Retain historical audit docs and old closed issues; do not rewrite historical evidence or report tests not run.
- If `scripts/setup_pstack.py` still mixes host-neutral policy with Grok-only file writes, move the already-existing writer to a narrow Grok-native helper **only if needed**, without inventing a generic adapter interface.

## Reversibility and proof
Use a reviewable stack: spec change -> reference migration -> canonical profile convergence -> final verification. Retain exact-head rollback instructions and restore packaging before removal. CI must distinguish typed/offline proof from observed host execution and separate missing host binaries as NOT_RUN/BLOCKED.
