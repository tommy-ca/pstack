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
from typing import Any, Dict, List, Optional, Set, Union

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    EgressClass,
    SafeContext,
    validate_and_create_safe_context,
)
from scripts.evidence_receipts import (
    check_receipt_staleness,
    create_decision_receipt,
    load_calibrated_evidence_receipt,
    validate_calibrated_evidence,
)

_DROID_DEFINITION_ID = re.compile(r"^pstack-[a-z0-9-]+$")

# Class-specific confidence calibration thresholds per openspec/specs/pstack-jev-decisions/spec.md
# Calibration is specific to class and consequence of error; universal thresholds are prohibited.
CLASS_CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "defect": 0.85,
    "explain": 0.75,
    "performance": 0.80,
    "prototype": 0.70,
    "refactor": 0.80,
    "runtime_diagnosis": 0.85,
    "trace_diagnosis": 0.85,
}


@lru_cache(maxsize=16)
def _get_applied_canonical_pin(root_str: str) -> Optional[str]:
    root_path = Path(root_str)
    pkg_path = root_path / "pstack.package.json"
    if pkg_path.is_file():
        try:
            obj = json.loads(pkg_path.read_text(encoding="utf-8"))
            pin = obj.get("upstream_pin")
            if pin and isinstance(pin, str) and len(pin.strip()) == 40:
                return pin.strip().lower()
        except Exception:
            pass
    upstream_file = root_path / "UPSTREAM"
    if upstream_file.is_file():
        try:
            for line in upstream_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("tree "):
                    return line.split()[1].strip().lower()
        except Exception:
            pass
    return None


@lru_cache(maxsize=8)
def _load_decision_routing(routing_path_str: str) -> Dict[str, Any]:
    path = Path(routing_path_str)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


def _contained_artifact(root: Path, candidate: Path) -> Optional[Path]:
    """Return candidate only when its resolved path stays inside resolved root.

    Identifiers are caller-supplied, so every join must be re-anchored: a
    ``..`` segment or an absolute identifier otherwise escapes the repository.
    """
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved == resolved_root or resolved_root in resolved.parents:
        return candidate
    return None


def resolve_primary_artifact(target: str, root: Path) -> Optional[Path]:
    """Resolve an identifier to its canonical filesystem artifact path if present."""
    identifier = target.strip()

    # Slash command or skill prefix
    if identifier.startswith("/"):
        skill_name = identifier.lstrip("/")
        skill_dir = _contained_artifact(root, root / "skills" / skill_name)
        if skill_dir is not None and skill_dir.is_dir():
            return skill_dir
        skill_file = _contained_artifact(
            root, root / "skills" / "poteto-mode" / "playbooks" / f"{skill_name}.md"
        )
        if skill_file is not None and skill_file.is_file():
            return skill_file
        return None

    # Agent role identifier
    if identifier.startswith("pstack:"):
        agent_name = identifier.split(":", 1)[1]
        agent_file = _contained_artifact(root, root / "agents" / f"{agent_name}.md")
        if agent_file is not None and agent_file.is_file():
            return agent_file
        return None

    # Droid definition identifier
    if _DROID_DEFINITION_ID.match(identifier):
        droid_file = _contained_artifact(root, root / "droids" / f"{identifier}.md")
        if droid_file is not None and droid_file.is_file():
            return droid_file
        # Check agents fallback for pstack-<name> -> agents/<name>.md
        agent_name = identifier.removeprefix("pstack-")
        agent_file = _contained_artifact(root, root / "agents" / f"{agent_name}.md")
        if agent_file is not None and agent_file.is_file():
            return agent_file
        return None

    # Playbook path or stem
    if identifier.endswith(".md"):
        playbook_path = _contained_artifact(root, root / "skills" / "poteto-mode" / identifier)
        if playbook_path is not None and playbook_path.is_file():
            return playbook_path
        playbook_nested = _contained_artifact(
            root, root / "skills" / "poteto-mode" / "playbooks" / identifier
        )
        if playbook_nested is not None and playbook_nested.is_file():
            return playbook_nested
        return None

    # Playbook bare stem
    stem_file = _contained_artifact(
        root, root / "skills" / "poteto-mode" / "playbooks" / f"{identifier}.md"
    )
    if stem_file is not None and stem_file.is_file():
        return stem_file

    # Canonical skill without slash prefix
    canon_skill = _contained_artifact(root, root / "skills" / identifier)
    if canon_skill is not None and canon_skill.is_dir():
        return canon_skill

    # Direct relative file
    direct_file = _contained_artifact(root, root / identifier)
    if direct_file is not None and direct_file.exists():
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


def _is_egress_bypassed(
    baseline: RouteResolution,
    query_str: str,
    safe_summary: Optional[Union[SafeContext, str]],
    bypass_playbooks: Optional[Set[str]] = None,
) -> bool:
    """Determine if query or baseline must bypass provider egress entirely (Issue #658)."""
    # 1. Explicit slash command query
    if query_str.strip().startswith("/"):
        return True

    # 2. Baseline agent, droid, or direct slash targets
    if baseline.status == "matched":
        raw_target = str(baseline.target or "").strip()
        if raw_target.startswith("/") or baseline.kind in ("agent", "droid-definition"):
            return True
        if bypass_playbooks:
            norm_target = (
                raw_target.lstrip("/")
                .replace("playbooks/", "")
                .removesuffix(".md")
                .strip()
            )
            if norm_target in bypass_playbooks:
                return True

    # 3. Privacy guard: safe_summary required, no raw query egress
    if not safe_summary:
        return True
    if isinstance(safe_summary, SafeContext) and safe_summary.egress_class in (
        EgressClass.LOCAL_ONLY,
        EgressClass.PROHIBITED,
    ):
        return True

    return False


def _load_semantic_candidates(root: Path) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """Load, validate canonical pins, and extract semantic candidates from references/decision-routing.json."""
    routing_file = root / "references" / "decision-routing.json"
    data = _load_decision_routing(str(routing_file.resolve()))
    if not data or not isinstance(data, dict):
        return {}, set()

    # Canonical mapping freshness verification (Issue #663)
    source_info = data.get("source", {})
    applied_pin = _get_applied_canonical_pin(str(root.resolve()))
    if applied_pin and source_info.get("revision") != applied_pin:
        return {}, set()
    if source_info.get("router_blob") != "21993f546032ca37671d5f1caf39c9a82ab4fa9d":
        return {}, set()

    semantic_candidates: Dict[str, Dict[str, Any]] = {}
    bypass_playbooks: Set[str] = set()

    for route in data.get("routes", []):
        pb = str(route.get("playbook", "")).strip()
        sel = route.get("selection")
        if sel == "semantic_candidate":
            semantic_candidates[pb] = route
        elif sel in ("direct", "direct_command_bypass", "system_two"):
            bypass_playbooks.add(pb)

    return semantic_candidates, bypass_playbooks


def _evaluate_advisory_promotion(
    baseline: RouteResolution,
    obs: Any,
    semantic_candidates: Dict[str, Dict[str, Any]],
    root: Path,
    calibrated_evidence_path: Optional[Union[Path, str]] = None,
) -> Optional[RouteResolution]:
    """Evaluate all promotion gates for an advisory decision (Issue #659, #660, #663)."""
    # 1. Provider judgment status
    if not obs.is_decided() or obs.outcome.kind != "choice":
        return None

    # 2. Scope gate: proposed choice must be an eligible semantic candidate
    recommended_pb = str(obs.outcome.value).strip()
    if recommended_pb not in semantic_candidates:
        return None

    candidate_route = semantic_candidates[recommended_pb]
    candidate_class = str(candidate_route.get("class", "")).strip()
    if not candidate_class or candidate_class not in CLASS_CONFIDENCE_THRESHOLDS:
        return None

    # 3. Class-specific confidence calibration threshold
    required_threshold = CLASS_CONFIDENCE_THRESHOLDS[candidate_class]
    confidence = obs.confidence if obs.confidence is not None else 0.0
    if confidence < required_threshold:
        return None

    # 4. Margin check: require winner matches top choice with margin >= 0.10
    if obs.probabilities and len(obs.probabilities) > 1:
        sorted_probs = sorted(obs.probabilities.values(), reverse=True)
        winner_prob = obs.probabilities.get(recommended_pb)
        if winner_prob is None or winner_prob != sorted_probs[0]:
            return None
        if sorted_probs[0] - sorted_probs[1] < 0.10:
            return None

    # 5. Persisted Calibrated Evidence Gate (#659)
    if obs.provider_identity in ("unknown", "none", "") or obs.model_identity in ("unknown", "none", ""):
        return None

    cal_path: Optional[Path] = None
    if calibrated_evidence_path:
        cal_path = Path(calibrated_evidence_path)
    elif "PSTACK_JEV_CALIBRATED_EVIDENCE" in os.environ:
        cal_path = Path(os.environ["PSTACK_JEV_CALIBRATED_EVIDENCE"])
    else:
        cal_path = root / "references" / "calibrated-evidence.json"

    cal_receipt = load_calibrated_evidence_receipt(cal_path)
    if cal_receipt is None:
        return None

    is_valid, _ = validate_calibrated_evidence(
        receipt=cal_receipt,
        current_root=root,
        expected_provider=obs.provider_identity,
        expected_model=obs.model_identity,
        candidate_class=candidate_class,
        confidence=confidence,
    )
    if not is_valid:
        return None

    # Staleness and receipt persistence hook
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
        return None

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


def resolve_skill_order_with_shadow(
    profile: Dict[str, Any],
    query_str: str,
    root: Path,
    provider: Optional[Any] = None,
    mode: Optional[str] = None,
    safe_summary: Optional[Union[SafeContext, str]] = None,
    calibrated_evidence_path: Optional[Union[Path, str]] = None,
) -> RouteResolution:
    """Resolve one skill_order row with shadow or advisory decision hook.

    Always computes the baseline deterministic route first.
    When mode is 'none' (or PSTACK_JEV_MODE is 'none'/'off'), returns baseline directly.
    When mode is 'shadow' (default), queries provider for observation without modifying
    the acting route (zero behavior change).
    When mode is 'advisory', promotes provider recommendation ONLY when:
    - Target is a verified low-risk semantic candidate in references/decision-routing.json
    - Provider outcome meets class-specific confidence threshold and margin separation
    - Persisted calibrated evidence receipt exists, is valid, unexpired, and matches provider/model
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

    # Early bypass & privacy guards: query or target bypass without I/O
    if _is_egress_bypassed(baseline, query_str, safe_summary):
        return baseline

    try:
        semantic_candidates, bypass_playbooks = _load_semantic_candidates(root)
        if not semantic_candidates or _is_egress_bypassed(baseline, query_str, safe_summary, bypass_playbooks):
            return baseline

        candidates: List[ChoiceOption] = []
        for pb, r in semantic_candidates.items():
            label = str(r.get("class_label", pb)).strip()
            if pb and label:
                candidates.append(ChoiceOption(id=pb, label=label))

        if not candidates:
            return baseline

        if isinstance(safe_summary, SafeContext):
            safe_ctx = safe_summary
        else:
            safe_ctx = validate_and_create_safe_context(str(safe_summary), EgressClass.SAFE_TO_SEND)

        req = ChoiceRequest(
            question_id="route_selection",
            context=safe_ctx,
            choices=tuple(candidates[:32]),
        )
        obs = provider.decide(req)
        baseline.shadow_observation = obs

        if effective_mode != "advisory":
            return baseline

        promoted = _evaluate_advisory_promotion(
            baseline=baseline,
            obs=obs,
            semantic_candidates=semantic_candidates,
            root=root,
            calibrated_evidence_path=calibrated_evidence_path,
        )
        return promoted or baseline
    except Exception:
        # Strict fail-open: no provider exception escapes to caller
        pass

    return baseline

