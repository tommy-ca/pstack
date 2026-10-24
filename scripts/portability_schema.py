"""Typed validation and domain model for pstack portability.

Re-exports domain models, surface revisions, and evidence durability functions
statically for modular decomposition and backwards compatibility (#603).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.host_identity import (
    KNOWN_HOSTS,
    is_declared_host,
    is_valid_host_id,
    is_valid_receipt_host,
)

from scripts.portability_types import (
    ADAPTATION_MODES,
    ALLOWED_TOOL_MAPPINGS,
    CONDITIONAL_CAPABILITIES,
    CONFORMANCE_PLANES,
    DEFAULT_PLUGIN_MANIFESTS,
    DEFAULT_SKILLS_DIRS,
    ENFORCEMENT_LEVELS,
    FORBIDDEN_ORCHESTRATION_FIELDS,
    HOSTS,
    IMPLEMENTATION_STATUSES,
    MANDATORY_SUPPORT_FLOOR,
    PLANE_SURFACE_DEPENDENCIES,
    PORTABLE_CAPABILITY_UNIVERSE,
    REQUIRED_CAPABILITIES,
    REQUIRED_TOOL_MAPPINGS,
    SETTLEMENT_PROMOTIONS,
    SETUP_EFFORT_MODES,
    SETUP_SHAPES,
    SETUP_SOURCES,
    SKILLS_HASH_IGNORED_DIRS,
    SKILLS_HASH_IGNORED_SUFFIXES,
    SUPPORT_STATES,
    VERIFICATION_STATUSES,
    Adaptation,
    Binding,
    Capability,
    ChildSettlement,
    Evidence,
    HarnessProfile,
    PackageDescriptor,
    RuntimeConventions,
    ScenarioResult,
    SetupProjection,
    SkillOrderItem,
    SurfaceRevisions,
    ToolMapping,
    ValidationError,
    VerificationReceipt,
    _is_observed_settlement,
    reduce_verdicts,
    settle_planes,
    validate_profile_file,
)
from scripts.surface_revisions import (
    DOCSTRING_CONSUMED_DRIVERS,
    RecipeError,
    _DRIVER_CORE_CACHE_MAX_BYTES,
    _DRIVER_CORE_CACHE_MAX_RECORDS,
    _DRIVER_CORE_CACHE_VERSION,
    _DRIVER_CORE_MEMO,
    _driver_core,
    _driver_core_cache_dir,
    _module_docstring,
    _prune_driver_core_cache,
    _read_driver_core_cache,
    _strip_docstrings,
    _update_driver_digest,
    _write_driver_core_cache,
    compute_surface_revisions,
)
from scripts.evidence_durability import (
    _is_preservable_settlement,
    _row_level,
    _row_receipt,
    check_evidence_durability,
    check_scenario_pins,
    derive_support_state,
    preserve_observed_settlements,
)

__all__ = [
    "ADAPTATION_MODES",
    "ALLOWED_TOOL_MAPPINGS",
    "Adaptation",
    "Binding",
    "Capability",
    "ChildSettlement",
    "CONDITIONAL_CAPABILITIES",
    "CONFORMANCE_PLANES",
    "DEFAULT_PLUGIN_MANIFESTS",
    "DEFAULT_SKILLS_DIRS",
    "DOCSTRING_CONSUMED_DRIVERS",
    "ENFORCEMENT_LEVELS",
    "Evidence",
    "FORBIDDEN_ORCHESTRATION_FIELDS",
    "HOSTS",
    "HarnessProfile",
    "IMPLEMENTATION_STATUSES",
    "KNOWN_HOSTS",
    "MANDATORY_SUPPORT_FLOOR",
    "PLANE_SURFACE_DEPENDENCIES",
    "PORTABLE_CAPABILITY_UNIVERSE",
    "PackageDescriptor",
    "Path",
    "REQUIRED_CAPABILITIES",
    "REQUIRED_TOOL_MAPPINGS",
    "RecipeError",
    "RuntimeConventions",
    "SETTLEMENT_PROMOTIONS",
    "SETUP_EFFORT_MODES",
    "SETUP_SHAPES",
    "SETUP_SOURCES",
    "SKILLS_HASH_IGNORED_DIRS",
    "SKILLS_HASH_IGNORED_SUFFIXES",
    "SUPPORT_STATES",
    "ScenarioResult",
    "SetupProjection",
    "SkillOrderItem",
    "SurfaceRevisions",
    "ToolMapping",
    "VERIFICATION_STATUSES",
    "ValidationError",
    "VerificationReceipt",
    "_DRIVER_CORE_CACHE_MAX_BYTES",
    "_DRIVER_CORE_CACHE_MAX_RECORDS",
    "_DRIVER_CORE_CACHE_VERSION",
    "_DRIVER_CORE_MEMO",
    "_driver_core",
    "_driver_core_cache_dir",
    "_is_observed_settlement",
    "_is_preservable_settlement",
    "_module_docstring",
    "_prune_driver_core_cache",
    "_read_driver_core_cache",
    "_row_level",
    "_row_receipt",
    "_strip_docstrings",
    "_update_driver_digest",
    "_write_driver_core_cache",
    "check_evidence_durability",
    "check_scenario_pins",
    "compute_surface_revisions",
    "derive_support_state",
    "is_declared_host",
    "is_valid_host_id",
    "is_valid_receipt_host",
    "preserve_observed_settlements",
    "reduce_verdicts",
    "require_builtin_host_keys",
    "settle_planes",
    "validate_profile_file",
]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: python3 scripts/portability_schema.py validate <profile-path>", file=sys.stderr)
        return 2

    cmd = args[0]
    target = args[1] if len(args) > 1 else None
    if cmd == "validate" and target:
        profile_path = target
    elif cmd != "validate":
        profile_path = cmd
    else:
        print("Usage: python3 scripts/portability_schema.py validate <profile-path>", file=sys.stderr)
        return 2

    try:
        validate_profile_file(profile_path)
        print(f"PASS: {profile_path} is a valid harness profile")
        return 0
    except Exception as err:
        print(f"ERROR: Invalid harness profile at {profile_path}: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

