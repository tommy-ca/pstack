# SetupProjection data schema and migration contract (proposed; NOT shipped)

**One authoritative JSON Schema:** `schemas/portability/setup-projection.schema.json` (Draft 2020-12), with the existing Python `SetupProjection.validate()` enforcing the identical source-state matrix. This file is a design fixture, NOT a second JSON schema registry or implementable schema file. In the implementation PR, modify the existing JSON schema and Python typed model in place.

## Final JSON Schema shape

The following is a proposed **replacement** for the current loose existing setup-projection schema. Schema clients MUST still validate the enclosing `HarnessProfile.support_state` and the resolved catalog/reference file existence.

~~~json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://pstack.dev/schemas/portability/setup-projection.schema.json",
  "title": "SetupProjection",
  "type": "object",
  "additionalProperties": false,
  "required": ["source", "effort"],
  "properties": {
    "source": {
      "type": "string",
      "enum": ["host-cli", "host-catalog", "inherit", "none"]
    },
    "effort": {
      "type": "string",
      "enum": ["live-enum", "inherit-parent", "none"]
    },
    "catalog": { "type": ["string", "null"] },
    "overlay": { "type": ["string", "null"] }
  },
  "oneOf": [
    {
      "properties": {
        "source": { "const": "host-cli" },
        "effort": { "const": "live-enum" },
        "catalog": { "type": "string", "minLength": 3, "pattern": "^~/" },
        "overlay": {
          "anyOf": [
            { "type": "null" },
            { "type": "string", "minLength": 3, "pattern": "^~/" }
          ]
        }
      },
      "required": ["catalog"]
    },
    {
      "properties": {
        "source": { "const": "host-catalog" },
        "effort": { "const": "none" },
        "catalog": { "type": "string", "minLength": 2, "pattern": "^[^~/]" },
        "overlay": { "const": null }
      },
      "required": ["catalog"]
    },
    {
      "properties": {
        "source": { "const": "inherit" },
        "effort": { "const": "inherit-parent" },
        "catalog": { "const": null },
        "overlay": { "const": null }
      }
    },
    {
      "properties": {
        "source": { "const": "none" },
        "effort": { "const": "none" },
        "catalog": { "const": null },
        "overlay": { "const": null }
      }
    }
  ]
}
~~~

This schema is intentionally small and imposes no speculative model-catalog schema. Host-home and repo path checks additionally require the current host's allowed destinations, no `..`/symlink escapes and existing projected file checks at the **boundary**; a regex on its own is not security proof. `candidate` restrictions apply at the enclosing `HarnessProfile` layer. Reject `skill` and `reference` as unknown fields in the *final* schema; do not add `reference` to the object just to locate a predictable filename.

## Migration-impact proof: six profiles have an explicit legacy skill key

Current packaged profiles (also mirrored under root `profiles/`):

| profile | existing setup.skill | required action |
| --- | --- | --- |
| grok.json | "setup-pstack-grok" | remove after native reference and caller migration |
| antigravity.json | null | remove legacy key |
| codex.json | null | remove legacy key |
| droid.json | null | remove legacy key |
| omp.json | null | remove legacy key |
| opencode.json | null | remove legacy key |
| pstack-pi.json | absent | preserve |
| claude.json | setup absent | preserve GAP |
| copilot.json | setup absent | preserve GAP |

It is a migration defect to update *only* `grok.json`: five non-Grok profiles would still carry `"skill": null` and fail the final closed schema. Update **all six packaged profiles and all six generated mirror copies** atomically with schema/type/parser/readers. Do not rewrite profile values unrelated to setup.

## Validate both native surfaces and typed claims

| Invariant | Negative fixture | Enforcement owner |
| --- | --- | --- |
| `host-cli` => `live-enum` and nonempty host-home catalog | `catalog: ../models.toml`, effort none | existing JSON Schema + typed SetupProjection; runtime path safety |
| `host-catalog` => projected catalog, no overlay | `overlay: ~/.grok/roles` | schema + `resolve_setup_projection` |
| `inherit` => parent model/no paths | non-null catalog or effort high | schema + typed SetupProjection |
| `none` => no paths | any native write target | schema + writer gates |
| `candidate` cannot prove `host-cli` | candidate Grok-like host | HarnessProfile boundary |
| No `skill` or `reference` | legacy `skill: null` still present | strict `additionalProperties:false` |
| Active host is exact declared ID | `copilot` vs `github:copilot` | scripts/host_identity.py + profile resolver |
| Native ref comes only from validated profile filename | host mismatch / symlinked `grok.md` | one small setup helper |
| root/packaged profile data identical | stale root mirror preferred | parity check and package resolver |
| Setup model and effort aliases are not interchangeable | `[effort].feature = inherit-parent` while frontmatter effort present | Grok native proof / honest status |

## Schema and tests single-source policy
The schema is implemented in `schemas/portability/setup-projection.schema.json` only, and validated through existing `tests/test_setup_projection.py`, `tests/test_harness_profiles_sync.py` and portability-schema tests. The Python type remains in `scripts/portability_types.py`. This document and OpenSpec are engineering requirements; do not generate an unrelated runtime schema, interface or provider module.

## Test inputs after implementation
~~~json
[
  { "source": "host-cli", "effort": "live-enum", "catalog": "~/.grok/pstack-models.toml", "overlay": "~/.grok/roles" },
  { "source": "host-catalog", "effort": "none", "catalog": ".codex-plugin/models.json", "overlay": null },
  { "source": "inherit", "effort": "inherit-parent" },
  { "source": "none", "effort": "none" }
]
~~~

Negative fixtures must include `skill:null` even for non-CLI setup, `reference:"references/grok.md"`, absent host-cli catalog, mistaken host ID, invalid source-effort combinations and path/symlink escaping. The known six-profile migration is explicit acceptance scope for #951/#952.
