"""Pure pstack role/model *planning*, never host-native model dispatch.

The planner composes a canonical role registry, host-specific model catalog,
per-role topology, optional overrides, and *reported* capability bindings.
No use of this planner proves a model is available, an agent spawned, or a
read-only/isolation boundary was enforced by a live host.

Library module: from scripts.model_role_resolver import plan_role. No CLI entry point; python -m exits silently. Direct script run is unsupported (package-relative imports).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from scripts.model_role_policy import INHERIT, check_model_role_policy
from scripts.portability_schema import IMPLEMENTATION_STATUSES, ENFORCEMENT_LEVELS, ValidationError


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


def _choices(value: str | Sequence[str], source: str) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        raise ValidationError(f"{source}: choices must be str/list/tuple")
    if not values or not all(isinstance(c, str) and c for c in values):
        raise ValidationError(f"{source}: choices must be nonempty model aliases or slugs")
    return values


def plan_role(
    policy: dict[str, Any],
    descriptor: dict[str, Any],
    *,
    host: str,
    role: str,
    explicit: str | Sequence[str] | None = None,
    project: str | Sequence[str] | None = None,
    user: str | Sequence[str] | None = None,
    parent_family: str | None = None,
    capabilities: Mapping[str, Mapping[str, str]] | None = None,
) -> ModelPlan:
    """Prepare a static plan, preserving explicit failures and honest gaps.

    A caller must separately prove native discovery, spawn/join, family identity,
    independent context, and enforcement before executing or claiming parity.
    Caller-supplied capability metadata is *advisory input*, never a receipt.
    """
    check_model_role_policy(policy, descriptor)
    registry = {r["id"]: r for r in descriptor["roles"]}
    if role not in registry:
        return _blocked(host, role, "unknown", "none", f"unknown canonical role: {role}")
    if host not in policy["hosts"]:
        return _blocked(host, role, "unknown", "none", f"unmapped host: {host}")

    config = policy["hosts"][host]
    contract = policy.get("role_constraints", {}).get(role, {})
    selection = contract.get("selection", "single")
    tier = registry[role]["default_model_role"]
    role_cfg = config.get("role_overrides", {}).get(role, {})

    if explicit is not None:
        raw, source = explicit, "explicit"
    elif project is not None:
        raw, source = project, "project"
    elif user is not None:
        raw, source = user, "user"
    elif "models" in role_cfg:
        raw, source = role_cfg["models"], "host-role"
    elif tier in config["tier_defaults"]:
        raw, source = config["tier_defaults"][tier], "host-tier"
    elif config["fallback"] == "inherit-parent":
        raw, source = "inherit-parent", "inherit-parent"
    else:
        return _blocked(host, role, selection, "none",
                        f"role {role} has no model mapping and fallback=fail-closed")

    choices = _choices(raw, source)
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

    # Capability binding availability is explicit: unknown != supported.
    reasons: list[str] = []
    degraded = False
    for capability in contract.get("required_capabilities", []):
        data = (capabilities or {}).get(capability)
        if not isinstance(data, Mapping) or data.get("implementation_status") in (None, "gap"):
            return _blocked(host, role, selection, source,
                            f"missing/unsupported required capability: {capability}")
        if data.get("implementation_status") not in IMPLEMENTATION_STATUSES or data.get("implementation_status") == "gap":
            return _blocked(host, role, selection, source, f"unknown binding type for {capability}")
        if data.get("enforcement") not in ENFORCEMENT_LEVELS:
            return _blocked(host, role, selection, source, f"unknown enforcement for {capability}")
        if data["enforcement"] != "hard":
            degraded = True
            reasons.append(f"{capability} enforcement is {data['enforcement']}, not hard")

    def seat(slot: int, slug: str) -> ModelSeat:
        if slug in INHERIT:
            return ModelSeat(slot, None, None, None)
        model = models[slug]
        return ModelSeat(slot, slug, model["family"], model["provider"])

    if selection == "single":
        members = [seat(1, choices[0])]
    elif selection == "cross-judge":
        # One judge, selected from a configured pool where possible.
        different = [slug for slug in choices if
                     slug not in INHERIT and models[slug]["family"] != parent_family]
        if parent_family and different:
            picked = different[0]
        else:
            picked = choices[0]
        members = [seat(1, picked)]
        if not parent_family or members[0].family == parent_family or members[0].family is None:
            if contract.get("require_distinct_model_families", False):
                return _blocked(host, role, selection, source,
                                "cross-judge model family independence is unproven")
            degraded = True
            reasons.append("cross-judge family diversity unproven; cannot label independent model review")
    else:
        minimum = contract.get("minimum_independent_workers", 1)
        configured_seats = role_cfg.get("seats", 0)
        count = max(minimum, configured_seats, len(choices))
        if count > 16:
            return _blocked(host, role, selection, source, "panel exceeds max 16 planned seats")
        members = [seat(i + 1, choices[i % len(choices)]) for i in range(count)]
        unique_families = {s.family for s in members if s.family is not None}
        if len(members) > 1 and len(unique_families) < 2:
            degraded = True
            reasons.append("independent seats do not prove diverse model families")
        if contract.get("require_distinct_model_families", False) and len(unique_families) < 2:
            return _blocked(host, role, selection, source, "required model-family diversity missing")

    # 'PLANNED' is deliberately not 'VERIFIED': actual independence and
    # supported native model IDs are proven by an external runtime driver.
    return ModelPlan(
        host=host, role=role, selection=selection, source=source,
        status="DEGRADED" if degraded else "PLANNED",
        seats=tuple(members), reasons=tuple(reasons), effort=effort,
    )



def model_plan_to_wire(plan: ModelPlan) -> dict[str, Any]:
    """Convert frozen planning tuples into JSON-compatible arrays.

    This is a static planning artifact, NOT a verified runtime receipt.
    """
    data = asdict(plan)
    data["seats"] = [asdict(seat) for seat in plan.seats]
    data["reasons"] = list(plan.reasons)
    return data
