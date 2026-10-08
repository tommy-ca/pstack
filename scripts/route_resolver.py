#!/usr/bin/env python3
"""Pure typed exact route resolution for pstack harness adapters.

Provides deterministic, side-effect-free route resolution for profile skill_order
entries against canonical skills, playbooks, agents, and declared fallbacks.
Matching is exact (never arbitrary substring), handling ambiguity, canonical
skill identifiers, agent definitions, and three-tier fallback resolution.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    EgressClass,
    validate_and_create_safe_context,
)
from scripts.evidence_receipts import (
    check_receipt_staleness,
    create_decision_receipt,
)

_DROID_DEFINITION_ID = re.compile(r"^pstack-[a-z0-9-]+$")
DEFAULT_ADVISORY_CONFIDENCE_THRESHOLD = 0.70


@lru_cache(maxsize=8)
def _load_decision_routing(routing_path_str: str) -> Dict[str, Any]:
    path = Path(routing_path_str)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class RouteResolution:
    """Result of resolving a route query against a profile's skill_order."""

    need: str = ""
    kind: str = "no-route"  # "skill", "playbook", "agent", "droid-definition", "declared-fallback", "no-route"
    target: Optional[str] = None
    artifact: Optional[Path] = None
    notes: str = ""
    status: str = "unmatched"  # "matched", "unmatched", "ambiguous"
    matched_rows: List[Dict[str, Any]] = field(default_factory=list)
    error_reason: str = ""
    shadow_observation: Optional[Any] = None
    advisory_promoted: bool = False

    @property
    def is_matched(self) -> bool:
        return self.status == "matched"

    @property
    def artifact_exists(self) -> bool:
        return self.artifact is not None and self.artifact.exists()


# Backwards-compatible alias for Droid and existing consumers
SkillRoute = RouteResolution


def resolve_primary_artifact(target: str, root: Path) -> Optional[Path]:
    """Resolve an identifier to its canonical filesystem artifact path if present."""
    identifier = target.strip()

    # Slash command or skill prefix
    if identifier.startswith("/"):
        skill_name = identifier.lstrip("/")
        skill_dir = root / "skills" / skill_name
        if skill_dir.is_dir():
            return skill_dir
        skill_file = root / "skills" / "poteto-mode" / "playbooks" / f"{skill_name}.md"
        if skill_file.is_file():
            return skill_file
        return None

    # Agent role identifier
    if identifier.startswith("pstack:"):
        agent_name = identifier.split(":", 1)[1]
        agent_file = root / "agents" / f"{agent_name}.md"
        if agent_file.is_file():
            return agent_file
        return None

    # Droid definition identifier
    if _DROID_DEFINITION_ID.match(identifier):
        droid_file = root / "droids" / f"{identifier}.md"
        if droid_file.is_file():
            return droid_file
        # Check agents fallback for pstack-<name> -> agents/<name>.md
        agent_name = identifier.removeprefix("pstack-")
        agent_file = root / "agents" / f"{agent_name}.md"
        if agent_file.is_file():
            return agent_file
        return None

    # Playbook path or stem
    if identifier.endswith(".md"):
        playbook_path = root / "skills" / "poteto-mode" / identifier
        if playbook_path.is_file():
            return playbook_path
        playbook_nested = root / "skills" / "poteto-mode" / "playbooks" / identifier
        if playbook_nested.is_file():
            return playbook_nested
        return None

    # Playbook bare stem
    stem_file = root / "skills" / "poteto-mode" / "playbooks" / f"{identifier}.md"
    if stem_file.is_file():
        return stem_file

    # Canonical skill without slash prefix
    canon_skill = root / "skills" / identifier
    if canon_skill.is_dir():
        return canon_skill

    # Direct relative file
    direct_file = root / identifier
    if direct_file.exists():
        return direct_file

    return None


def resolve_skill_order(profile: Dict[str, Any], query_str: str, root: Path) -> RouteResolution:
    """Resolve one advisory skill_order row for a query.

    Matching is exact, never substring:
    - Matches need (case-insensitive)
    - Matches primary_pstack identifier (case-insensitive)
    - Matches slash command stem (/foo -> foo)
    - Matches playbook stem (playbooks/foo.md -> foo)
    - Matches agent/droid stem (pstack:foo -> foo, pstack-foo -> foo)
    - Parses comma-separated primary entries without aliasing
    """
    raw_query = query_str.strip()
    if not raw_query:
        return RouteResolution(
            status="unmatched",
            kind="no-route",
            need="",
            target=None,
            artifact=None,
            error_reason="Empty query",
        )

    query = raw_query.lower()
    first_token = query.split()[0] if query.split() else query
    is_command_prefix = raw_query.startswith("/") or raw_query.startswith("pstack:")
    matches: List[Dict[str, Any]] = []

    for item in profile.get("skill_order", []):
        need = str(item.get("need", "")).strip()
        primary = item.get("primary_pstack")
        candidates: Set[str] = {need.lower()}

        if primary is not None:
            raw_primary = str(primary).strip()
            # Handle comma-separated primaries
            primaries = [p.strip() for p in raw_primary.split(",") if p.strip()]
            for p in primaries:
                candidates.add(p.lower())
                if p.startswith("/"):
                    candidates.add(p.lstrip("/").lower())
                if p.startswith("pstack:"):
                    candidates.add(p.split(":", 1)[1].lower())
                if p.startswith("pstack-"):
                    candidates.add(p.removeprefix("pstack-").lower())
                stem = p.rsplit("/", 1)[-1]
                if stem.endswith(".md"):
                    candidates.add(stem[:-3].lower())

        fallback = item.get("secondary_user") or item.get("fallback_builtin")
        if fallback is not None:
            raw_fallback = str(fallback).strip()
            candidates.add(raw_fallback.lower())
            if raw_fallback.startswith("/"):
                candidates.add(raw_fallback.lstrip("/").lower())

        if query in candidates or (is_command_prefix and first_token in candidates):
            matches.append(item)

    if not matches:
        return RouteResolution(
            status="unmatched",
            kind="no-route",
            need="",
            target=None,
            artifact=None,
            error_reason=f"No skill_order row matched query '{query_str}'",
        )

    if len(matches) > 1:
        return RouteResolution(
            status="ambiguous",
            kind="no-route",
            need="",
            target=None,
            artifact=None,
            matched_rows=matches,
            error_reason=f"Ambiguous query '{query_str}' matched {len(matches)} skill_order rows",
        )

    matched_row = matches[0]
    need = str(matched_row.get("need", "")).strip()
    notes = str(matched_row.get("notes", ""))
    primary = matched_row.get("primary_pstack")

    if primary is None:
        # Declared tier order: secondary_user (tier 2) wins over fallback_builtin (tier 3)
        fallback = matched_row.get("secondary_user") or matched_row.get("fallback_builtin")
        return RouteResolution(
            status="matched",
            kind="declared-fallback",
            need=need,
            target=str(fallback) if fallback else None,
            artifact=None,
            notes=notes,
            matched_rows=[matched_row],
        )

    target_str = str(primary).strip()
    artifact = resolve_primary_artifact(target_str, root)

    # Determine kind
    if target_str.startswith("/"):
        kind = "skill"
    elif target_str.startswith("pstack:"):
        kind = "agent"
    elif _DROID_DEFINITION_ID.match(target_str):
        kind = "droid-definition"
    else:
        kind = "playbook"

    return RouteResolution(
        status="matched",
        kind=kind,
        need=need,
        target=target_str,
        artifact=artifact,
        notes=notes,
        matched_rows=[matched_row],
    )


def resolve_skill_order_with_shadow(
    profile: Dict[str, Any],
    query_str: str,
    root: Path,
    provider: Optional[Any] = None,
    mode: Optional[str] = None,
) -> RouteResolution:
    """Resolve one skill_order row with shadow or advisory decision hook.

    Always computes the baseline deterministic route first.
    When mode is 'none' (or PSTACK_JEV_MODE is 'none'/'off'), returns baseline directly.
    When mode is 'shadow' (default), queries provider for observation without modifying
    the acting route (zero behavior change).
    When mode is 'advisory', promotes provider recommendation ONLY when:
    - Target is a verified low-risk semantic candidate in references/decision-routing.json
    - Provider outcome is decided with confidence >= 0.70
    - Fresh evidence receipt check passes (no staleness, known provider/model)
    - Deterministic baseline route is not an explicit bypass command or System-Two gate.
    All exceptions, timeouts, and failures fail open safely to the baseline route.
    """
    baseline = resolve_skill_order(profile, query_str, root)

    effective_mode = mode
    if effective_mode is None:
        effective_mode = os.environ.get("PSTACK_JEV_MODE", "shadow").strip().lower()
    else:
        effective_mode = str(effective_mode).strip().lower()

    if provider is None or effective_mode in ("none", "off", "0", "disabled"):
        return baseline

    try:
        routing_file = root / "references" / "decision-routing.json"
        data = _load_decision_routing(str(routing_file.resolve()))
        if not data:
            return baseline
        semantic_candidates: Dict[str, Dict[str, Any]] = {}
        bypass_playbooks: Set[str] = set()

        for route in data.get("routes", []):
            pb = str(route.get("playbook", "")).strip()
            sel = route.get("selection")
            if sel == "semantic_candidate":
                semantic_candidates[pb] = route
            elif sel in ("direct", "direct_command_bypass", "system_two"):
                bypass_playbooks.add(pb)

        candidates: List[ChoiceOption] = []
        for pb, r in semantic_candidates.items():
            label = str(r.get("class_label", pb)).strip()
            if pb and label:
                candidates.append(ChoiceOption(id=pb, label=label))

        if not candidates:
            return baseline

        # Attempt to build safe context from query
        safe_ctx = validate_and_create_safe_context(query_str, EgressClass.SAFE_TO_SEND)
        req = ChoiceRequest(
            question_id="route_selection",
            context=safe_ctx,
            choices=tuple(candidates[:32]),
        )
        obs = provider.decide(req)
        baseline.shadow_observation = obs

        if effective_mode != "advisory":
            return baseline

        # --- Advisory Promotion Policy Gate ---
        # 1. Deterministic baseline safety invariant: explicit direct commands,
        # system-two playbooks, and slash commands cannot be overridden.
        if baseline.status == "matched":
            raw_target = str(baseline.target or "").strip()
            norm_target = (
                raw_target.lstrip("/")
                .replace("playbooks/", "")
                .removesuffix(".md")
                .strip()
            )
            if (
                norm_target in bypass_playbooks
                or raw_target.startswith("/")
                or baseline.kind in ("agent", "droid-definition")
            ):
                return baseline

        # 2. Provider judgment status
        if not obs.is_decided() or obs.outcome.kind != "choice":
            return baseline

        # 3. Class-specific confidence threshold (>= 0.70)
        confidence = obs.confidence if obs.confidence is not None else 0.0
        if confidence < DEFAULT_ADVISORY_CONFIDENCE_THRESHOLD:
            return baseline

        # 4. Scope gate: proposed choice must be an eligible semantic candidate
        recommended_pb = str(obs.outcome.value).strip()
        if recommended_pb not in semantic_candidates:
            return baseline

        # 5. Mechanical staleness gate: verify evidence receipt freshness
        if obs.provider_identity in ("unknown", "none", "") or obs.model_identity in ("unknown", "none", ""):
            return baseline

        receipt = create_decision_receipt(
            root=root,
            source="semantic_provider",
            mode="advisory",
            provider_identity=obs.provider_identity,
            model_identity=obs.model_identity,
            outcome_status=obs.outcome.status,
            outcome_value=recommended_pb,
            confidence=confidence,
        )
        is_stale, _ = check_receipt_staleness(
            receipt,
            current_root=root,
            expected_provider=obs.provider_identity,
            expected_model=obs.model_identity,
        )
        if is_stale:
            return baseline

        # All gates passed: promote candidate
        promoted_artifact = resolve_primary_artifact(recommended_pb, root)
        return RouteResolution(
            status="matched",
            kind="playbook",
            need=baseline.need or f"advisory-{recommended_pb}",
            target=recommended_pb,
            artifact=promoted_artifact,
            notes=f"Advisory decision promoted via {obs.provider_identity}:{obs.model_identity} (confidence: {confidence:.2f})",
            matched_rows=baseline.matched_rows,
            shadow_observation=obs,
            advisory_promoted=True,
        )
    except Exception:
        # Strict fail-open: no provider exception escapes to caller
        pass

    return baseline

