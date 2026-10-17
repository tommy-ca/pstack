#!/usr/bin/env python3
"""Offline gating harness for agent-facing domain overlays (#314, B03/B04/B20).

Enforces the committed contract from
``openspec/changes/archive/2026-10-11-deepseek-skill-portability/specs/pstack-reusable-skill-patterns/spec.md``:

- every conditional domain overlay declares a positive applicability predicate,
  prohibited contexts and a typed unsupported-capability response;
- an overlay loads its agent-facing prose **only** when the project declares the
  required capability and the task domain matches;
- non-applicable archetypes (docs-only, backend-only, read-only, forges without a
  stack API) load zero overlay prose;
- the total context work of a case (overlay prose bytes) is measured and recorded.

The corpus is pinned to the committed qualification document; the recorded trace
lives in ``tests/fixtures/context-overlays/context-work-trace.json`` and is
regenerated with ``python tests/test_context_overlays.py --write-trace``.

Nothing here executes project code, browsers, network or forge commands: it is an
offline behavior control, not observed-live evidence.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "context-overlays"
REGISTRY_PATH = FIXTURES / "domain-overlays.json"
CASES_PATH = FIXTURES / "cases.json"
TRACE_PATH = FIXTURES / "context-work-trace.json"
QSTACK_ROUTING_PATH = Path(__file__).resolve().parent / "fixtures" / "qstack-overlay-routing.json"
QUALIFICATION_DOC = (
    ROOT
    / "openspec/changes/archive/2026-10-11-deepseek-skill-portability/qualification-and-eval.md"
)

# Typed responses allowed for an overlay whose capability is absent.
UNSUPPORTED_RESPONSES = ("BLOCKED", "UNTESTED")
# Token estimate is a deterministic proxy: 4 bytes per token (measurement is bytes).
BYTES_PER_TOKEN = 4

# Vocabulary that MUST NOT appear as an unconditional common-pstack requirement
# in shared agent-facing prose (#314 acceptance / spec "relevance and host conditionality").
FORBIDDEN_UNCONDITIONAL = (
    r"gh stack",
    r"\bpnpm\b",
    r"\bvitest\b",
    r"\bcordis\b",
    r"\bdsh\b",
)
# A line carrying one of those terms is fine only when it also states a condition.
CONDITIONAL_MARKERS = (
    "when ",
    "only if",
    "if the",
    "unless",
    "capability",
    "where the project",
    "supported ",
)


def _load(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


REGISTRY = _load(REGISTRY_PATH)
OVERLAYS: List[Dict] = REGISTRY["overlays"]
OVERLAY_INDEX: Dict[str, Dict] = {overlay["id"]: overlay for overlay in OVERLAYS}
CASES: List[Dict] = _load(CASES_PATH)["cases"]


@dataclass(frozen=True)
class Activation:
    """Result of gating the registry against one case."""

    activated: Tuple[str, ...]
    blocked: Tuple[Tuple[str, str], ...]
    inactive: Tuple[str, ...]


def select_overlays(
    registry: Sequence[Dict],
    *,
    capabilities: Iterable[str],
    domain: str,
    contexts: Iterable[str] = (),
    requested: Iterable[str] = (),
) -> Activation:
    """Gate every overlay pack on capability, domain and prohibited contexts.

    An overlay fires only when its required capability is declared, its domain
    matches (or the task explicitly requests it) and no prohibited context is
    present. A requested overlay whose capability is absent is typed BLOCKED /
    UNTESTED -- never silently skipped and never PASS.
    """
    caps = set(capabilities)
    ctxs = set(contexts)
    reqs = set(requested)
    activated, blocked, inactive = [], [], []
    for overlay in registry:
        overlay_id = overlay["id"]
        if ctxs & set(overlay["prohibited_contexts"]):
            inactive.append(overlay_id)
            continue
        if overlay["domain"] != domain and overlay_id not in reqs:
            inactive.append(overlay_id)
            continue
        if overlay["required_capability"] not in caps:
            if overlay_id in reqs:
                blocked.append((overlay_id, overlay["unsupported_response"]))
            else:
                inactive.append(overlay_id)
            continue
        activated.append(overlay_id)
    return Activation(tuple(activated), tuple(blocked), tuple(inactive))


def prose_bytes(overlay_ids: Iterable[str]) -> int:
    """Measured agent-facing context loaded by the given overlay packs."""
    return sum(len(OVERLAY_INDEX[overlay_id]["prose"].encode("utf-8")) for overlay_id in overlay_ids)


def ungated_bytes() -> int:
    """Naive no-gating baseline: every registered pack loads for every task."""
    return prose_bytes(OVERLAY_INDEX)


def measure_case(case: Dict) -> Dict:
    """Activation plus measured context work for one corpus case."""
    activation = select_overlays(
        OVERLAYS,
        capabilities=case["capabilities"],
        domain=case["domain"],
        contexts=case["contexts"],
        requested=case["requested"],
    )
    loaded = prose_bytes(activation.activated)
    baseline = ungated_bytes()
    return {
        "id": case["id"],
        "archetype": case["archetype"],
        "domain": case["domain"],
        "capabilities": sorted(case["capabilities"]),
        "contexts": sorted(case["contexts"]),
        "requested": sorted(case["requested"]),
        "activated": list(activation.activated),
        "blocked": [list(item) for item in activation.blocked],
        "inactive_count": len(activation.inactive),
        "loaded_artifacts": list(activation.activated),
        "measured_bytes": loaded,
        "estimated_tokens": loaded // BYTES_PER_TOKEN,
        "ungated_bytes": baseline,
        "saved_bytes": baseline - loaded,
    }


def overlay_costs() -> Dict[str, Dict[str, int]]:
    """Measured agent-facing cost of each overlay pack."""
    return {
        overlay["id"]: {
            "bytes": len(overlay["prose"].encode("utf-8")),
            "estimated_tokens": len(overlay["prose"].encode("utf-8")) // BYTES_PER_TOKEN,
        }
        for overlay in OVERLAYS
    }


def build_trace() -> Dict:
    records = [measure_case(case) for case in CASES]
    ungated_per_case = ungated_bytes()
    gated_total = sum(record["measured_bytes"] for record in records)
    return {
        "source": "tests/fixtures/context-overlays/cases.json",
        "baseline_definition": _load(CASES_PATH)["baseline_definition"],
        "token_estimate": f"bytes // {BYTES_PER_TOKEN}",
        "measured": ["overlay_prose_bytes", "activated_packs", "inactive_packs", "typed_unsupported_response"],
        "not_measured_offline": [
            "tool_call_tokens",
            "re_reads",
            "search_retries",
            "wall_clock",
            "missed_verification",
        ],
        "not_measured_note": (
            "Total task work beyond overlay prose (tool tokens, re-reads, search retries, wall clock, "
            "missed verification) needs the blinded candidate phase of #310; this trace MUST NOT be "
            "reported as observed-live evidence."
        ),
        "overlay_count": len(OVERLAYS),
        "case_count": len(records),
        "overlay_costs": overlay_costs(),
        "ungated_bytes": ungated_per_case,
        "ungated_total_bytes": ungated_per_case * len(records),
        "gated_total_bytes": gated_total,
        "saved_total_bytes": ungated_per_case * len(records) - gated_total,
        "cases": records,
    }


def write_trace() -> Path:
    TRACE_PATH.write_text(json.dumps(build_trace(), indent=2) + "\n", encoding="utf-8")
    return TRACE_PATH


def _case_ids() -> List[str]:
    return [case["id"] for case in CASES]


def _corpus_case(case_id: str) -> Dict:
    return next(case for case in CASES if case["id"] == case_id)


# --- registry completeness -------------------------------------------------


def test_registry_is_non_empty_and_ids_are_unique() -> None:
    assert len(OVERLAYS) >= 6, "domain overlay corpus must cover the B20 domains"
    assert len(OVERLAY_INDEX) == len(OVERLAYS)


@pytest.mark.parametrize("overlay", OVERLAYS, ids=[o["id"] for o in OVERLAYS])
def test_overlay_declares_predicate_prohibition_and_typed_response(overlay: Dict) -> None:
    assert overlay["required_capability"], "overlay needs a positive applicability predicate"
    assert overlay["prohibited_contexts"], "overlay needs explicit prohibited contexts"
    assert overlay["unsupported_response"] in UNSUPPORTED_RESPONSES
    prose = overlay["prose"]
    assert "Applies only when" in prose, "agent-facing prose must state its condition"
    assert f"`{overlay['required_capability']}`" in prose, "prose must name the gating capability"


# --- corpus grounding ------------------------------------------------------


def test_corpus_ids_are_unique_and_expectations_reference_known_overlays() -> None:
    ids = _case_ids()
    assert len(ids) == len(set(ids))
    for case in CASES:
        named = list(case["expect_activated"]) + [pair[0] for pair in case["expect_blocked"]]
        unknown = sorted(set(named) - set(OVERLAY_INDEX))
        assert not unknown, f"{case['id']} references unknown overlays {unknown}"


def test_every_registered_overlay_is_exercised_by_a_case() -> None:
    covered = {
        overlay_id
        for case in CASES
        for overlay_id in list(case["expect_activated"]) + [pair[0] for pair in case["expect_blocked"]]
    }
    assert covered == set(OVERLAY_INDEX)


def test_corpus_is_pinned_to_the_committed_qualification_document() -> None:
    doc = QUALIFICATION_DOC.read_text(encoding="utf-8")
    for case in CASES:
        if not re.fullmatch(r"[EN]\d{2}", case["id"]):
            continue
        row = f"| {case['id']} |"
        assert row in doc, f"{case['id']} is not part of the committed corpus"
        assert f"| {case['archetype']} |" in doc, f"{case['id']} archetype drifted from the corpus"
        assert f"| {case['task']} |" in doc, f"{case['id']} task drifted from the corpus"


# --- gating behavior -------------------------------------------------------


@pytest.mark.parametrize("case_id", _case_ids())
def test_case_activates_only_matching_domain_overlays(case_id: str) -> None:
    case = _corpus_case(case_id)
    activation = select_overlays(
        OVERLAYS,
        capabilities=case["capabilities"],
        domain=case["domain"],
        contexts=case["contexts"],
        requested=case["requested"],
    )
    assert list(activation.activated) == case["expect_activated"]
    assert [list(pair) for pair in activation.blocked] == case["expect_blocked"]
    activated_names = set(activation.activated)
    assert not (activated_names & set(case["contexts"]))


@pytest.mark.parametrize("case_id", [c["id"] for c in CASES if not c["expect_activated"]])
def test_non_trigger_case_loads_zero_overlay_prose(case_id: str) -> None:
    record = measure_case(_corpus_case(case_id))
    assert record["activated"] == []
    assert record["loaded_artifacts"] == []
    assert record["measured_bytes"] == 0
    assert record["saved_bytes"] == record["ungated_bytes"] > 0


@pytest.mark.parametrize("overlay", OVERLAYS, ids=[o["id"] for o in OVERLAYS])
def test_overlay_never_fires_without_its_capability(overlay: Dict) -> None:
    gated = select_overlays(
        OVERLAYS,
        capabilities=[],
        domain=overlay["domain"],
        contexts=(),
        requested=[overlay["id"]],
    )
    assert overlay["id"] not in gated.activated
    assert (overlay["id"], overlay["unsupported_response"]) in gated.blocked


@pytest.mark.parametrize("overlay", OVERLAYS, ids=[o["id"] for o in OVERLAYS])
def test_prohibited_context_deactivates_the_overlay(overlay: Dict) -> None:
    for context in overlay["prohibited_contexts"]:
        gated = select_overlays(
            OVERLAYS,
            capabilities=[overlay["required_capability"], "web_ui", "i18n", "release_tags"],
            domain=overlay["domain"],
            contexts=[context],
            requested=[overlay["id"]],
        )
        assert overlay["id"] not in gated.activated, f"{overlay['id']} fired in prohibited context {context}"
        assert overlay["id"] not in [pair[0] for pair in gated.blocked]


# --- qstack overlay boundary (#444) ----------------------------------------


def test_qstack_overlay_stays_post_routing_and_leaves_routes_unchanged() -> None:
    """qstack is a post-router domain overlay, never a second router.

    Two of the three halves here are production-bound and one is a declaration, stated
    so the pin is not read as more than it is:

    - production: every harness resolves the recorded route for one fixed need, so a
      profile/`skill_order` drift reddens it;
    - production: no file under `scripts/` or `profiles/` may mention qstack at all —
      the overlay is external, and the day it is wired into pstack routing (or into a
      profile's model namespace) this reddens;
    - declaration: the fixture's own contract fields, and its activation table run
      through this repo's overlay-gating semantics (`select_overlays`), which pin the
      declared contract rather than executing the external pack.
    """
    from scripts.route_resolver import resolve_skill_order

    fixture = _load(QSTACK_ROUTING_PATH)
    contract, overlay, route = fixture["contract"], fixture["overlay"], fixture["route"]

    assert contract["stage"] == "post-routing"
    assert contract["owns_router"] is False
    assert contract["owns_model_namespace"] is False
    assert overlay["unsupported_response"] in UNSUPPORTED_RESPONSES

    for host in route["hosts"]:
        resolved = resolve_skill_order(_load(ROOT / "profiles" / f"{host}.json"), route["need"], ROOT)
        observed = {"status": resolved.status, "kind": resolved.kind, "target": resolved.target}
        assert observed == route["expect"], host

    coupled = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (*ROOT.glob("scripts/**/*.py"), *ROOT.glob("profiles/*.json"))
        if "qstack" in path.read_text(encoding="utf-8", errors="ignore")
    )
    assert not coupled, f"pstack must not own a qstack router or model namespace: {coupled}"

    for case in fixture["cases"]:
        activation = select_overlays(
            [overlay],
            capabilities=case["capabilities"],
            domain=case["domain"],
            contexts=case["contexts"],
            requested=case["requested"],
        )
        if overlay["id"] in activation.activated:
            observed = "activated"
        elif overlay["id"] in [pair[0] for pair in activation.blocked]:
            observed = "blocked"
            assert dict(activation.blocked)[overlay["id"]] == overlay["unsupported_response"]
        else:
            observed = "inactive"
        assert observed == case["expect"], case["id"]


# --- measured context work -------------------------------------------------


def test_context_work_trace_is_recorded_and_matches_measurement() -> None:
    assert TRACE_PATH.exists(), "record the per-case context work trace"
    recorded = _load(TRACE_PATH)
    recomputed = build_trace()
    assert recorded == recomputed, (
        "recorded context work drifted; regenerate with "
        "`python tests/test_context_overlays.py --write-trace`"
    )


def test_gated_context_work_stays_below_the_ungated_baseline() -> None:
    trace = build_trace()
    assert trace["ungated_bytes"] > 0
    assert trace["gated_total_bytes"] < trace["ungated_total_bytes"]
    assert trace["saved_total_bytes"] > 0
    for record in trace["cases"]:
        assert 0 <= record["measured_bytes"] <= record["ungated_bytes"]
        if not record["activated"]:
            assert record["saved_bytes"] == record["ungated_bytes"]


# --- shared agent-facing prose guard --------------------------------------


def test_shared_agent_prose_has_no_unconditional_domain_tooling() -> None:
    surfaces = sorted(ROOT.glob("skills/*/SKILL.md")) + sorted(ROOT.glob("agents/*.md"))
    assert surfaces, "expected shared agent-facing prose surfaces to exist"
    pattern = re.compile("|".join(FORBIDDEN_UNCONDITIONAL), re.IGNORECASE)
    offenders: List[str] = []
    for surface in surfaces:
        for line in surface.read_text(encoding="utf-8").splitlines():
            if not pattern.search(line):
                continue
            if any(marker in line.lower() for marker in CONDITIONAL_MARKERS):
                continue
            offenders.append(f"{surface.relative_to(ROOT)}: {line.strip()[:120]}")
    assert not offenders, "unconditional domain tooling in shared prose: " + "; ".join(offenders)


if __name__ == "__main__":
    if "--write-trace" in sys.argv[1:]:
        print(f"wrote {write_trace().relative_to(ROOT)}")
    else:
        raise SystemExit("usage: python tests/test_context_overlays.py --write-trace")
