"""Pure pstack role/model *planning*, never host-native model dispatch.

The planner composes a canonical role registry, host-specific model catalog,
per-role topology, optional overrides, and *reported* capability bindings.
No use of this planner proves a model is available, an agent spawned, or a
read-only/isolation boundary was enforced by a live host.

Library module: from scripts.model_role_resolver import plan_role. No CLI entry point; python -m exits silently. Direct script run is unsupported (package-relative imports).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from scripts.model_role_policy import (
    INHERIT,
    PANEL_SEAT_MAX,
    check_choice_list,
    check_model_role_policy,
    unproven_catalog_reason,
)
from scripts.portability_schema import IMPLEMENTATION_STATUSES, ENFORCEMENT_LEVELS


@dataclass(frozen=True)
class ModelSeat:
    """Planned independent invocation; ordinal is not a live agent ID."""
    ordinal: int
    model: str | None
    family: str | None
    provider: str | None


@dataclass(frozen=True)
class ModelPlan:
    host: str
    role: str
    selection: str
    source: str
    status: str  # PLANNED, DEGRADED, BLOCKED; NEVER runtime VERIFIED.
    seats: tuple[ModelSeat, ...]
    reasons: tuple[str, ...]
    effort: str | None
    evidence_level: str = "static-planning-only"


def _blocked(host: str, role: str, selection: str, source: str, reason: str) -> ModelPlan:
    return ModelPlan(host, role, selection, source, "BLOCKED", (), (reason,), None)


def _seat(ordinal: int, slug: str, models: dict[str, dict[str, Any]]) -> ModelSeat:
    """Inherited slugs carry no fabricated model identity."""
    if slug in INHERIT:
        return ModelSeat(ordinal, None, None, None)
    model = models[slug]
    return ModelSeat(ordinal, slug, model["family"], model["provider"])


@dataclass(frozen=True)
class CompiledPolicy:
    """Validated policy and descriptor pair for decoupled evaluation."""
    policy: dict[str, Any]
    descriptor: dict[str, Any]


def compile_policy(policy: dict[str, Any], descriptor: dict[str, Any]) -> CompiledPolicy:
    """Validate policy against schema and descriptor once for repeated queries."""
    check_model_role_policy(policy, descriptor)
    return CompiledPolicy(policy, descriptor)


def resolve_role_source(
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
    if explicit is not None:
        raw, source = explicit, "explicit"
    elif project is not None:
        raw, source = project, "project"
    elif user is not None:
        raw, source = user, "user"
    elif "models" in role_cfg:
        raw, source = role_cfg["models"], "host-role"
    elif tier in host_config.get("tier_defaults", {}):
        raw, source = host_config["tier_defaults"][tier], "host-tier"
    elif host_config.get("fallback") == "inherit-parent":
        raw, source = "inherit-parent", "inherit-parent"
    else:
        return [], "fail-closed"

    return check_choice_list(source, raw), source


def _resolve_source(
    host: str, role: str, selection: str, *, tier: str, config: Mapping[str, Any],
    role_cfg: Mapping[str, Any], explicit: str | Sequence[str] | None,
    project: str | Sequence[str] | None, user: str | Sequence[str] | None,
) -> tuple[list[str], str] | ModelPlan:
    """Caller precedence, then host/tier config, then parent inheritance."""
    choices, source = resolve_role_source(
        role,
        tier=tier,
        host_config=config,
        role_cfg=role_cfg,
        explicit=explicit,
        project=project,
        user=user,
    )
    if source == "fail-closed":
        return _blocked(host, role, selection, "none",
                        f"role {role} has no model mapping and fallback=fail-closed")
    return choices, source


def _gate_capabilities(
    host: str, role: str, selection: str, source: str, contract: Mapping[str, Any],
    capabilities: Mapping[str, Mapping[str, str]] | None,
) -> tuple[bool, list[str]] | ModelPlan:
    """Capability binding availability is explicit: unknown != supported."""
    degraded = False
    reasons: list[str] = []
    for capability in contract.get("required_capabilities", []):
        data = (capabilities or {}).get(capability)
        if not isinstance(data, Mapping) or data.get("implementation_status") in (None, "gap"):
            return _blocked(host, role, selection, source,
                            f"missing/unsupported required capability: {capability}")
        if data.get("implementation_status") not in IMPLEMENTATION_STATUSES:
            return _blocked(host, role, selection, source, f"unknown binding type for {capability}")
        if data.get("enforcement") not in ENFORCEMENT_LEVELS:
            return _blocked(host, role, selection, source, f"unknown enforcement for {capability}")
        if data["enforcement"] != "hard":
            degraded = True
            reasons.append(f"{capability} enforcement is {data['enforcement']}, not hard")
    return degraded, reasons


def _members_for(
    host: str, role: str, selection: str, source: str, contract: Mapping[str, Any],
    role_cfg: Mapping[str, Any], choices: list[str], models: dict[str, dict[str, Any]],
    parent_family: str | None,
) -> tuple[list[ModelSeat], bool, list[str]] | ModelPlan:
    """Seat topology for the three selection modes; blockers short-circuit."""
    degraded = False
    reasons: list[str] = []
    if selection == "single":
        members = [_seat(1, choices[0], models)]
    elif selection == "cross-judge":
        # One judge, selected from a configured pool where possible.
        different = [slug for slug in choices if
                     slug not in INHERIT and models[slug]["family"] != parent_family]
        if parent_family and different:
            picked = different[0]
        else:
            picked = choices[0]
        members = [_seat(1, picked, models)]
        if not parent_family or members[0].family == parent_family or members[0].family is None:
            if contract.get("require_distinct_model_families", False):
                return _blocked(host, role, selection, source,
                                "cross-judge model family independence is unproven")
            degraded = True
            reasons.append("cross-judge family diversity unproven; cannot label independent model review")
    else:
        minimum = contract.get("minimum_independent_workers", 1)
        configured_seats = role_cfg.get("seats")  # None until the policy sets a seat override
        count = max(minimum, configured_seats if configured_seats is not None else 0, len(choices))
        if count > PANEL_SEAT_MAX:
            return _blocked(host, role, selection, source,
                            f"panel exceeds max {PANEL_SEAT_MAX} planned seats")
        members = [_seat(i + 1, choices[i % len(choices)], models) for i in range(count)]
        unique_families = {s.family for s in members if s.family is not None}
        if len(members) > 1 and len(unique_families) < 2:
            degraded = True
            reasons.append("independent seats do not prove diverse model families")
        if contract.get("require_distinct_model_families", False) and len(unique_families) < 2:
            return _blocked(host, role, selection, source, "required model-family diversity missing")
    return members, degraded, reasons


def plan_role(
    policy: dict[str, Any] | CompiledPolicy,
    descriptor: dict[str, Any] | None = None,
    *,
    host: str,
    role: str,
    explicit: str | Sequence[str] | None = None,
    project: str | Sequence[str] | None = None,
    user: str | Sequence[str] | None = None,
    parent_family: str | None = None,
    capabilities: Mapping[str, Mapping[str, str]] | None = None,
    validate_policy: bool = True,
) -> ModelPlan:
    """Prepare a static plan, preserving explicit failures and honest gaps.

    A caller must separately prove native discovery, spawn/join, family identity,
    independent context, and enforcement before executing or claiming parity.
    Caller-supplied capability metadata is *advisory input*, never a receipt.
    """
    if isinstance(policy, CompiledPolicy):
        actual_policy = policy.policy
        actual_descriptor = policy.descriptor if descriptor is None else descriptor
    else:
        if descriptor is None:
            raise ValueError("descriptor is required when policy is a dict")
        actual_policy = policy
        actual_descriptor = descriptor
        if validate_policy:
            check_model_role_policy(actual_policy, actual_descriptor)

    registry = {r["id"]: r for r in actual_descriptor["roles"]}
    if role not in registry:
        return _blocked(host, role, "unknown", "none", f"unknown canonical role: {role}")
    if host not in actual_policy["hosts"]:
        return _blocked(host, role, "unknown", "none", f"unmapped host: {host}")

    config = actual_policy["hosts"][host]
    contract = actual_policy.get("role_constraints", {}).get(role, {})
    selection = contract.get("selection", "single")
    tier = registry[role]["default_model_role"]
    role_cfg = config.get("role_overrides", {}).get(role, {})

    resolved = _resolve_source(host, role, selection, tier=tier, config=config, role_cfg=role_cfg,
                               explicit=explicit, project=project, user=user)
    if isinstance(resolved, ModelPlan):
        return resolved
    choices, source = resolved
    if selection == "single" and len(choices) != 1:
        return _blocked(host, role, selection, source, "single role requires exactly one model entry")

    models = {m["id"]: m for m in config["model_catalog"]}
    for slug in choices:
        if slug not in INHERIT and slug not in models:
            return _blocked(host, role, selection, source,
                            f"model {slug!r} absent from {host} catalog; no silent substitution")

    effort = role_cfg.get("effort")
    if effort is not None:
        for slug in choices:
            if slug not in INHERIT and effort not in models[slug].get("supported_efforts", []):
                return _blocked(host, role, selection, source,
                                f"effort {effort!r} unsupported on model {slug!r}")
        if config["discovery"] != "live":
            return _blocked(host, role, selection, source,
                            "model-specific effort requires a live-observed catalog")

    gated = _gate_capabilities(host, role, selection, source, contract, capabilities)
    if isinstance(gated, ModelPlan):
        return gated
    degraded, reasons = gated

    built = _members_for(host, role, selection, source, contract, role_cfg, choices, models,
                         parent_family)
    if isinstance(built, ModelPlan):
        return built
    members, seat_degraded, seat_reasons = built

    # A stale/unverified catalog claim is planning-grade only: it may degrade a
    # plan, never yield a clean PLANNED. Blocker paths above already returned
    # BLOCKED, so this gate can only lower PLANNED to DEGRADED.
    unproven = unproven_catalog_reason(config)
    catalog_reason = (unproven,) if unproven is not None else ()

    # 'PLANNED' is deliberately not 'VERIFIED': actual independence and
    # supported native model IDs are proven by an external runtime driver.
    return ModelPlan(
        host=host, role=role, selection=selection, source=source,
        status="DEGRADED" if degraded or seat_degraded or catalog_reason else "PLANNED",
        seats=tuple(members), reasons=tuple(reasons + seat_reasons + list(catalog_reason)),
        effort=effort,
    )


def model_plan_to_wire(plan: ModelPlan) -> dict[str, Any]:
    """Convert frozen planning tuples into JSON-compatible arrays.

    This is a static planning artifact, NOT a verified runtime receipt.
    """
    data = asdict(plan)  # asdict already recurses into seats; only tuples must become arrays
    data["seats"] = list(data["seats"])
    data["reasons"] = list(data["reasons"])
    return data
