"""Tests for setup-pstack model/effort sheets, safe override precedence, and hook lifecycle (#438)."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import tomllib

from scripts.setup_pstack import (
    CANONICAL_ROLES,
    VALID_HOOK_EVENTS,
    effective_role_precedence,
    evaluate_hook_lifecycle,
    generate_pstack_models_toml,
    get_hook_opt_out,
    load_canonical_roles,
    parse_pstack_models_toml,
    set_hook_opt_out,
    sync_grok_role_overlays,
)


def test_canonical_roles_has_all_22_package_roles() -> None:
    pkg = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    assert len(CANONICAL_ROLES) == len(pkg["roles"]) == 22
    for r in pkg["roles"]:
        assert r["id"] in CANONICAL_ROLES
    assert "comment-sicko" in CANONICAL_ROLES
    assert "poteto-agent" in CANONICAL_ROLES


def test_grok_pstack_models_example_is_valid_and_complete() -> None:
    example_path = ROOT / "examples/portability/grok-pstack-models.example.toml"
    assert example_path.is_file()
    content = example_path.read_text(encoding="utf-8")
    models, effort, warnings = parse_pstack_models_toml(content)
    assert not warnings, f"example has unexpected warnings: {warnings}"
    assert len(models) == 22
    assert len(effort) == 22
    assert set(models.keys()) == set(CANONICAL_ROLES.keys())
    assert set(effort.keys()) == set(CANONICAL_ROLES.keys())


def test_grok_role_overlay_example_is_valid() -> None:
    example_path = ROOT / "examples/portability/grok-role-overlay.example.toml"
    assert example_path.is_file()
    data = tomllib.loads(example_path.read_text(encoding="utf-8"))
    assert data["description"] == "pstack feature role"
    assert data["reasoning_effort"] == "medium"
    assert "model" not in data


def test_deterministic_setup_and_rerun() -> None:
    example_path = ROOT / "examples/portability/grok-pstack-models.example.toml"
    content = example_path.read_text(encoding="utf-8")
    models, effort, warnings = parse_pstack_models_toml(content)
    assert not warnings

    generated_1 = generate_pstack_models_toml(models, effort)
    generated_2 = generate_pstack_models_toml(models, effort)
    assert generated_1 == generated_2

    # Round-trip parse gives identical model and effort dictionaries
    m2, e2, w2 = parse_pstack_models_toml(generated_1)
    assert not w2
    assert m2 == models
    assert e2 == effort


def test_invalid_row_and_retired_role_yields_targeted_warning() -> None:
    bad_toml = """
feature = "grok-4.6"
retired-legacy-role = "grok-4.5"
malformed-model = 12345

[effort]
feature = "medium"
retired-reviewer = "high"
empty-effort = ""
"""
    models, effort, warnings = parse_pstack_models_toml(bad_toml)
    assert "feature" in models
    assert "retired-legacy-role" in models
    assert "malformed-model" not in models
    assert "feature" in effort
    assert "empty-effort" not in effort

    warnings_text = "\n".join(warnings)
    assert "unrecognized or retired role 'retired-legacy-role'" in warnings_text
    assert "invalid model value for 'malformed-model'" in warnings_text
    assert "unrecognized or retired role 'retired-reviewer'" in warnings_text
    assert "invalid effort value for 'empty-effort'" in warnings_text


def test_sync_grok_role_overlays_preserves_user_files(tmp_path: Path) -> None:
    roles_dir = tmp_path / ".grok" / "roles"
    roles_dir.mkdir(parents=True)

    # User-owned custom role file (not managed by pstack)
    user_file = roles_dir / "custom-agent.toml"
    user_file.write_text('description = "User custom agent"\nreasoning_effort = "high"\n', encoding="utf-8")

    # Stale pstack overlay
    stale_pstack = roles_dir / "pstack:feature.toml"
    stale_pstack.write_text('description = "old"\n', encoding="utf-8")

    effort_map = {
        "feature": "high",              # Should update
        "how-explorer": "medium",        # Should write
        "refactoring": "inherit-parent", # Should NOT write (and remove if existed)
    }

    written, removed = sync_grok_role_overlays(effort_map, roles_dir)
    assert (roles_dir / "pstack:feature.toml").is_file()
    assert (roles_dir / "pstack:how-explorer.toml").is_file()
    assert not (roles_dir / "pstack:refactoring.toml").is_file()

    # User file must be strictly preserved untouched
    assert user_file.is_file()
    assert user_file.read_text(encoding="utf-8") == 'description = "User custom agent"\nreasoning_effort = "high"\n'

    # Re-running with same effort map is idempotent (no writes, no removals)
    written_2, removed_2 = sync_grok_role_overlays(effort_map, roles_dir)
    assert not written_2
    assert not removed_2


def test_effective_config_and_source_precedence_visibility() -> None:
    host_config = {
        "tier_defaults": {
            "strongest": ["host-tier-model"],
        },
        "fallback": "fail-closed",
    }
    role_cfg = {
        "models": ["host-role-model"],
    }

    # 1. Host-tier default
    choices, src = effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg={})
    assert choices == ["host-tier-model"] and src == "host-tier"

    # 2. Host-role override wins over host-tier
    choices, src = effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg)
    assert choices == ["host-role-model"] and src == "host-role"

    # 3. User override (~/.grok/pstack-models.toml) wins over host-role and host-tier
    choices, src = effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"])
    assert choices == ["user-custom-model"] and src == "user"

    # 4. Project override wins over user override
    choices, src = effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"])
    assert choices == ["project-model"] and src == "project"

    # 5. Explicit invocation wins over everything
    choices, src = effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"], explicit="cli-model")
    assert choices == ["cli-model"] and src == "explicit"


def test_hook_opt_out_is_host_scoped_and_idempotent(tmp_path: Path) -> None:
    config_dir = tmp_path / "host-config"

    assert get_hook_opt_out("grok", config_dir) is False
    assert get_hook_opt_out("codex", config_dir) is False

    # Opt-out grok
    changed = set_hook_opt_out("grok", True, config_dir)
    assert changed is True
    assert get_hook_opt_out("grok", config_dir) is True
    assert get_hook_opt_out("codex", config_dir) is False  # host-scoped!

    # Idempotent re-opt-out returns False (no change)
    changed_again = set_hook_opt_out("grok", True, config_dir)
    assert changed_again is False

    # Clear opt-out
    cleared = set_hook_opt_out("grok", False, config_dir)
    assert cleared is True
    assert get_hook_opt_out("grok", config_dir) is False


def test_evaluate_hook_lifecycle_events_idempotence_and_honest_negatives(tmp_path: Path) -> None:
    config_dir = tmp_path / "host-config"

    # 1. Supported events: startup, resume, compact
    assert VALID_HOOK_EVENTS == {"startup", "resume", "compact"}
    for event in ("startup", "resume", "compact"):
        active, msg = evaluate_hook_lifecycle("codex", event, config_dir)
        assert active is True
        assert msg == f"hook active for codex on {event}"

        # Idempotence: repeated evaluation yields identical output without side effects
        active2, msg2 = evaluate_hook_lifecycle("codex", event, config_dir)
        assert (active2, msg2) == (active, msg)

    # 2. Opt-out behavior across events
    set_hook_opt_out("codex", True, config_dir)
    for event in ("startup", "resume", "compact"):
        active, msg = evaluate_hook_lifecycle("codex", event, config_dir)
        assert active is False
        assert msg == "routing hooks opted-out for codex"

    # Clear opt-out
    set_hook_opt_out("codex", False, config_dir)

    # 3. Missing trust fails honestly
    active, msg = evaluate_hook_lifecycle("codex", "startup", config_dir, trust_verified=False)
    assert active is False
    assert "host environment trust unverified for codex" in msg

    # 4. Conflicting hook fails honestly
    active, msg = evaluate_hook_lifecycle("codex", "startup", config_dir, conflicting_hook=True)
    assert active is False
    assert "conflicting hook detected for codex" in msg

    # 5. Unrecognized event fails honestly
    active, msg = evaluate_hook_lifecycle("codex", "arbitrary-event", config_dir)
    assert active is False
    assert "unsupported hook event: 'arbitrary-event'" in msg

