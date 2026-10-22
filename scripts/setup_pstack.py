"""setup-pstack model/effort sheet unification, host setup projection, precedence, and hook lifecycle (#438, #703).

Provides:
- Resolution of a host's declared setup projection from profiles/<host>.json.
- Deterministic parsing and generation of the top-level role model sheet.
- Targeted warnings for invalid rows or retired/unrecognized roles.
- Safe synchronization of Grok role overlays (~/.grok/roles/pstack:<key>.toml)
  while strictly preserving user-owned files.
- Effective config and source precedence inspection across canonical roles.
- Host-scoped, idempotent hook opt-out lifecycle management.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence
import tomllib

from scripts.model_role_resolver import resolve_role_source
from scripts.portability_schema import SetupProjection, ValidationError

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "pstack.package.json"
PROFILES_DIR = ROOT / "profiles"


def resolve_setup_projection(
    host: str, profiles_dir: Path = PROFILES_DIR, root: Path = ROOT
) -> Optional[SetupProjection]:
    """Return the host's declared setup projection, or None when it declares none.

    `None` is a GAP to report, never a reason to reuse another host's setup. The
    structural matrix (source/effort/field coherence) lives on the typed model;
    this resolver adds the repo-level checks the profile cannot make on its own:
    a declared skill must exist, and a repo-relative catalog must be projected.
    """
    profile_path = profiles_dir / f"{host}.json"
    if not profile_path.is_file():
        raise ValidationError(f"No harness profile for host {host!r}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    raw = profile.get("setup")
    if raw is None:
        return None
    # A CLI-probing surface writes host-home config, so it needs proven bindings.
    # A passive declaration (inherit/none/host-catalog) is layout, not capability.
    if raw.get("source") == "host-cli" and profile.get("support_state") == "candidate":
        raise ValidationError(
            f"Candidate host {host!r} must not declare a CLI-probing setup surface before native evidence"
        )
    projection = SetupProjection(**raw)
    projection.validate()
    skill_path = root / "skills" / str(projection.skill) / "SKILL.md"
    if projection.skill and not skill_path.is_file():
        raise ValidationError(
            f"setup skill {projection.skill!r} for {host!r} has no skills/{projection.skill}/SKILL.md"
        )
    catalog = projection.catalog
    if catalog and not catalog.startswith("~") and not Path(catalog).is_absolute():
        if not (root / catalog).exists():
            raise ValidationError(f"setup catalog {catalog!r} for {host!r} is not projected")
    return projection


def load_canonical_roles(package_path: Path = PACKAGE_JSON) -> dict[str, dict[str, Any]]:
    """Load canonical roles registry from pstack.package.json."""
    data = json.loads(package_path.read_text(encoding="utf-8"))
    roles: dict[str, dict[str, Any]] = {}
    for r in data.get("roles", []):
        roles[r["id"]] = r
    return roles


CANONICAL_ROLES = load_canonical_roles()


def parse_pstack_models_toml(
    content: str, canonical_roles: Mapping[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, str], list[str]]:
    """Parse pstack-models.toml, returning (models, effort, warnings).

    Emits targeted warnings for unrecognized or retired roles, rather than
    silently normalizing or crashing.
    """
    valid_roles = set(canonical_roles.keys()) if canonical_roles is not None else set(CANONICAL_ROLES.keys())
    warnings: list[str] = []

    try:
        data = tomllib.loads(content)
    except Exception as exc:
        raise ValueError(f"malformed TOML syntax in pstack-models.toml: {exc}") from exc

    models: dict[str, Any] = {}
    effort_table: dict[str, str] = {}

    for key, value in data.items():
        if key == "effort":
            if not isinstance(value, dict):
                warnings.append("invalid [effort] section: expected a table of role = 'level'")
                continue
            for ekey, evalue in value.items():
                if not isinstance(evalue, str) or not evalue.strip():
                    warnings.append(f"invalid effort value for '{ekey}': expected non-empty string, got {evalue!r}")
                    continue
                if ekey not in valid_roles:
                    warnings.append(f"unrecognized or retired role '{ekey}' in [effort]")
                effort_table[ekey] = evalue.strip()
            continue

        if not isinstance(value, (str, list)):
            warnings.append(f"invalid model value for '{key}': expected string or list of strings, got {type(value).__name__}")
            continue

        if isinstance(value, list) and not all(isinstance(v, str) and v.strip() for v in value):
            warnings.append(f"invalid model array for '{key}': all items must be non-empty strings")
            continue

        if key not in valid_roles:
            warnings.append(f"unrecognized or retired role '{key}' in model mappings")

        models[key] = value

    return models, effort_table, warnings


def generate_pstack_models_toml(
    models: Mapping[str, Any],
    effort: Mapping[str, str],
    canonical_roles: Mapping[str, Any] | None = None,
) -> str:
    """Generate deterministic, canonical pstack-models.toml.

    Roles are formatted in deterministic alphabetical order.
    """
    role_order = sorted(canonical_roles.keys()) if canonical_roles is not None else sorted(CANONICAL_ROLES.keys())
    lines = [
        "# pstack-models.toml: pstack model and reasoning effort overrides.",
        "# Managed by /setup-pstack. Manual edits are preserved.",
        "# Missing keys default to shipped defaults; inherit-parent omits model on task.",
        "",
    ]

    # Models section (top-level keys)
    for role in role_order:
        val = models.get(role)
        if val is None:
            continue
        if isinstance(val, list):
            items_str = ", ".join(f'"{item}"' for item in val)
            lines.append(f"{role} = [{items_str}]")
        else:
            lines.append(f'{role} = "{val}"')

    # Effort section
    lines.append("")
    lines.append("[effort]")
    for role in role_order:
        eval_ = effort.get(role)
        if eval_ is None:
            continue
        lines.append(f'{role} = "{eval_}"')

    lines.append("")
    return "\n".join(lines)


def sync_grok_role_overlays(
    effort_map: Mapping[str, str],
    roles_dir: Path,
    canonical_roles: Mapping[str, Any] | None = None,
) -> tuple[list[Path], list[Path]]:
    """Synchronize ~/.grok/roles/pstack:<role>.toml files.

    - If effort is inherit-parent, auto, or empty, removes pstack:<role>.toml if present.
    - If effort is a real token, writes description + reasoning_effort.
    - Retains user-owned non-pstack files (files not starting with 'pstack:').

    Returns (written_paths, removed_paths).
    """
    roles_dir.mkdir(parents=True, exist_ok=True)
    valid_roles = set(canonical_roles.keys()) if canonical_roles is not None else set(CANONICAL_ROLES.keys())

    written: list[Path] = []
    removed: list[Path] = []

    for role in sorted(valid_roles):
        overlay_path = roles_dir / f"pstack:{role}.toml"
        val = effort_map.get(role, "").strip()

        if not val or val in ("inherit-parent", "auto"):
            if overlay_path.is_file():
                overlay_path.unlink()
                removed.append(overlay_path)
        else:
            content = f'description = "pstack {role} role"\nreasoning_effort = "{val}"\n'
            if not overlay_path.is_file() or overlay_path.read_text(encoding="utf-8") != content:
                overlay_path.write_text(content, encoding="utf-8")
                written.append(overlay_path)

    return written, removed


def effective_role_precedence(
    role: str,
    *,
    tier: str,
    host_config: Mapping[str, Any],
    role_cfg: Mapping[str, Any],
    explicit: str | Sequence[str] | None = None,
    project: str | Sequence[str] | None = None,
    user: str | Sequence[str] | None = None,
) -> tuple[list[str], str]:
    """Report effective models and winning precedence rung for a role."""
    return resolve_role_source(
        role,
        tier=tier,
        host_config=host_config,
        role_cfg=role_cfg,
        explicit=explicit,
        project=project,
        user=user,
    )


def get_hook_opt_out(host: str, config_dir: Path) -> bool:
    """Read host-scoped hook opt-out state from host config directory."""
    opt_out_file = config_dir / f".pstack-hooks-disabled-{host}"
    return opt_out_file.is_file()


def set_hook_opt_out(host: str, opt_out: bool, config_dir: Path) -> bool:
    """Set host-scoped hook opt-out state idempotently.

    Returns True if state changed, False otherwise.
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    opt_out_file = config_dir / f".pstack-hooks-disabled-{host}"
    currently_opted_out = opt_out_file.is_file()

    if opt_out and not currently_opted_out:
        opt_out_file.write_text(
            f"# Host-scoped hook routing disabled for {host} (pstack #438)\n",
            encoding="utf-8",
        )
        return True
    elif not opt_out and currently_opted_out:
        opt_out_file.unlink()
        return True
    return False


VALID_HOOK_EVENTS = frozenset({"startup", "resume", "compact"})


def evaluate_hook_lifecycle(
    host: str,
    event: str,
    config_dir: Path,
    *,
    trust_verified: bool = True,
    conflicting_hook: bool = False,
) -> tuple[bool, str]:
    """Evaluate host-local routing hook eligibility for session lifecycle events.

    Guarantees:
    - Supported events: startup, resume, compact (idempotent evaluation)
    - Reversible opt-out via host-scoped marker file (.pstack-hooks-disabled-{host})
    - Fails honestly on unverified host environment trust
    - Fails honestly when a conflicting hook is detected (prevents double-injection / overwrite)
    - Fails honestly on unrecognised events
    """
    if event not in VALID_HOOK_EVENTS:
        return False, f"unsupported hook event: {event!r} (must be one of {sorted(VALID_HOOK_EVENTS)})"

    if get_hook_opt_out(host, config_dir):
        return False, f"routing hooks opted-out for {host}"

    if conflicting_hook:
        return False, f"conflicting hook detected for {host}; refusing to overwrite or double-inject"

    if not trust_verified:
        return False, f"host environment trust unverified for {host}; refusing hook injection"

    return True, f"hook active for {host} on {event}"

