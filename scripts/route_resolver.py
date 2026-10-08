#!/usr/bin/env python3
"""Pure typed exact route resolution for pstack harness adapters.

Provides deterministic, side-effect-free route resolution for profile skill_order
entries against canonical skills, playbooks, agents, and declared fallbacks.
Matching is exact (never arbitrary substring), handling ambiguity, canonical
skill identifiers, agent definitions, and three-tier fallback resolution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

_DROID_DEFINITION_ID = re.compile(r"^pstack-[a-z0-9-]+$")


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

        if query in candidates:
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
    mode: str = "shadow",
) -> RouteResolution:
    """Resolve one advisory skill_order row with zero-behavior-change shadow provider hook.

    Always computes the baseline deterministic route first. When a provider is
    passed and mode is 'shadow', queries the provider in advisory shadow mode over
    semantic candidates in references/decision-routing.json. Provider failures,
    timeouts, or errors are caught safely and never alter the resolved baseline route.
    """
    baseline = resolve_skill_order(profile, query_str, root)
    if provider is None or mode != "shadow":
        return baseline

    try:
        import json
        from scripts.decision_adapter import (
            ChoiceOption,
            ChoiceRequest,
            EgressClass,
            validate_and_create_safe_context,
        )

        routing_file = root / "references" / "decision-routing.json"
        if not routing_file.is_file():
            return baseline

        data = json.loads(routing_file.read_text(encoding="utf-8"))
        candidates: List[ChoiceOption] = []
        for route in data.get("routes", []):
            if route.get("selection") == "semantic_candidate":
                playbook_id = str(route.get("playbook", "")).strip()
                label = str(route.get("class_label", playbook_id)).strip()
                if playbook_id and label:
                    candidates.append(ChoiceOption(id=playbook_id, label=label))

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
    except Exception:
        # Strict fail-open: no provider exception escapes to caller
        pass

    return baseline

