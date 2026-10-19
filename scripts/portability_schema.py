"""Typed validation and domain model for pstack portability.

Re-exports domain models, surface revisions, and evidence durability functions
statically for modular decomposition and backwards compatibility (#603).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from scripts.host_identity import (
    KNOWN_HOSTS,
    is_declared_host,
    is_valid_host_id,
    is_valid_receipt_host,
    require_builtin_host_keys,
)

SUPPORT_STATES = ("candidate", "mapped", "packaged", "verified", "supported")
IMPLEMENTATION_STATUSES = ("native", "shim", "version-gated", "gap")
ENFORCEMENT_LEVELS = ("hard", "soft", "advisory")
VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")
ADAPTATION_MODES = ("preserve", "adapt", "exclude", "gap")
HOSTS = KNOWN_HOSTS
CONFORMANCE_PLANES = ("canonical", "adapter", "package", "runtime")

SKILLS_HASH_IGNORED_DIRS = frozenset({"__pycache__", "node_modules"})
SKILLS_HASH_IGNORED_SUFFIXES = (".pyc", ".pyo")

MANDATORY_SUPPORT_FLOOR = (
    "agent.spawn",
    "agent.join",
    "workspace.shared",
    "workspace.isolated",
    "workspace.readonly",
    "human.ask",
    "plan.update",
    "verify",
    "evidence.capture",
)

CONDITIONAL_CAPABILITIES: Dict[str, str] = {
    "schedule": "orchestrate, overnight, autopilot-full",
    "monitor": "orchestrate, monitor-watcher, loop",
    "session.persist": "pause-safely",
    "session.resume": "session-pickup",
    "agent.message": "interactive multi-agent collaboration",
    "agent.cancel": "task cancellation and kill",
    "agent.resume": "subagent resume from checkpoint",
    "human.gate": "irreversible action confirmation",
}

PORTABLE_CAPABILITY_UNIVERSE = MANDATORY_SUPPORT_FLOOR + tuple(sorted(CONDITIONAL_CAPABILITIES.keys()))

SETTLEMENT_PROMOTIONS: Dict[str, tuple] = {
    "agent.cancel": ("cancelled",),
}

REQUIRED_CAPABILITIES = MANDATORY_SUPPORT_FLOOR

FORBIDDEN_ORCHESTRATION_FIELDS = (
    "spawn_topology",
    "fan_out_policy",
    "scheduler_behavior",
    "verifier_logic",
    "session_database",
)

REQUIRED_TOOL_MAPPINGS = (
    "file_read",
    "file_edit",
    "shell_run",
    "agent_spawn",
    "agent_join",
    "plan_update",
    "human_ask",
)

ALLOWED_TOOL_MAPPINGS = (
    "file_read",
    "file_edit",
    "file_write",
    "shell_run",
    "web_fetch",
    "web_search",
    "agent_spawn",
    "agent_fanout",
    "agent_join",
    "agent_message",
    "task_background",
    "tool_mcp",
    "plan_update",
    "human_ask",
)

DEFAULT_SKILLS_DIRS = {
    "grok": ".grok/skills",
    "codex": ".codex/skills",
    "omp": ".omp/skills",
    "opencode": ".opencode/skills",
    "antigravity": ".agents/skills",
    "droid": ".factory/skills",
}

DEFAULT_PLUGIN_MANIFESTS = {
    "grok": ".grok-plugin/plugin.json",
    "codex": ".codex-plugin/plugin.json",
    "omp": ".omp-plugin/package.json",
    "opencode": ".opencode-plugin/package.json",
    "antigravity": ".antigravity-plugin/plugin.json",
    "droid": ".factory-plugin/plugin.json",
}

require_builtin_host_keys(DEFAULT_SKILLS_DIRS, "DEFAULT_SKILLS_DIRS")
require_builtin_host_keys(DEFAULT_PLUGIN_MANIFESTS, "DEFAULT_PLUGIN_MANIFESTS")

from scripts.portability_types import (
    Adaptation,
    Binding,
    Capability,
    ChildSettlement,
    Evidence,
    HarnessProfile,
    PLANE_SURFACE_DEPENDENCIES,
    PackageDescriptor,
    RuntimeConventions,
    ScenarioResult,
    SkillOrderItem,
    SurfaceRevisions,
    ToolMapping,
    ValidationError,
    VerificationReceipt,
    _is_observed_settlement,
    reduce_verdicts,
    settle_planes,
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
    "SKILLS_HASH_IGNORED_DIRS",
    "SKILLS_HASH_IGNORED_SUFFIXES",
    "SUPPORT_STATES",
    "ScenarioResult",
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
]
