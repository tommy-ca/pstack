#!/usr/bin/env python3
"""P14b (#314): measured-context, bounded-output and overlay-capability contracts.

Offline control over the two authoring/context owners this unit extends plus the two
recorded task-work traces that measure what the capability gating costs and saves:

- ``skills/principle-guard-the-context-window/SKILL.md`` owns the measured-work rule
  (total work: loaded bytes, reads, re-reads, retried searches) and the positive
  capability predicate that admits an optional domain overlay pack;
- ``skills/technical-writing/SKILL.md`` owns the bounded-output contract for
  agent-facing prose and keeps UI, bilingual, upgrade, archival, recording and
  forge-stack guidance project-owned;
- ``tests/fixtures/context-overlays/task-work-traces.json`` records two real tasks run
  in both arms (ungated baseline versus capability-gated).

The byte components of a recorded trace are recomputed here from the repository, so a
trace cannot drift from the prose it charges. The tool-call counters come from observed
lane runs; their provenance is declared in the trace, and transcripts are session-scoped,
so this suite validates the recorded arithmetic and the no-worse-work claim rather than
replaying the runs. Nothing here executes a browser, a forge or a model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "context-overlays"
REGISTRY_PATH = FIXTURES / "domain-overlays.json"
CASES_PATH = FIXTURES / "cases.json"
TRACES_PATH = FIXTURES / "task-work-traces.json"
CHANGE = ROOT / "openspec" / "changes" / "2026-10-11-deepseek-skill-portability"
ATOM_TABLE = CHANGE / "atomic-patterns.md"

GUARD = ROOT / "skills" / "principle-guard-the-context-window" / "SKILL.md"
WRITING = ROOT / "skills" / "technical-writing" / "SKILL.md"
PRINCIPLES_DOC = ROOT / "docs" / "guide" / "08-principles.md"
AUTHORING_DOC = ROOT / "docs" / "guide" / "09-make-it-yours.md"

# The sections this unit adds to the two owners, addressed by their first heading.
OWNER_SECTIONS = {
    "guard-measured-work": (GUARD, "## Measure the work, not the opening tokens", "## Load an optional domain overlay only for a declared capability"),
    "guard-overlay-gating": (GUARD, "## Load an optional domain overlay only for a declared capability", None),
    "writing-bounded-output": (WRITING, "## Bound the output, and state its condition", "## Domain guidance is project-owned, never universal"),
    "writing-domain-ownership": (WRITING, "## Domain guidance is project-owned, never universal", "## Worked example"),
}
# The gated arm is charged the whole owner contract the lanes actually carried, for every
# task: both sections of both owners. Charging a task only the section its domain "needs"
# would understate what the recorded run loaded.


def gated_contract_bytes() -> int:
    return sum(section_bytes(handle) for handle in OWNER_SECTIONS)


# Overlay capability family -> the word the guard contract names it by.
# `dsh_theme_tokens` is absent on purpose: it is a project-owned pack gated by the project's
# own declaration, so the guard names the project-declared predicate, not a token family.
CAPABILITY_FAMILIES = {
    "perf_baseline": "performance",
    "web_ui": "UI",
    "browser_driver": "browser",
    "i18n": "i18n",
    "release_tags": "release",
    "archival_records": "archive",
    "forge_stack_api": "forge-stack",
}
# Work categories a trace MUST account for, including the two the spec calls out.
REQUIRED_WORK_KEYS = (
    "total_tool_calls",
    "file_reads",
    "distinct_paths_read",
    "re_reads",
    "search_calls",
    "retried_searches",
    "commands",
    "writes",
)


def flat(text: str) -> str:
    return " ".join(text.split())


def owner(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def section_bytes(handle: str) -> int:
    """Recomputed byte size of a section this unit adds to an owner."""
    path, start, end = OWNER_SECTIONS[handle]
    text = owner(path)
    begin = text.index(start)
    stop = text.index(end) if end else len(text)
    return len(text[begin:stop].encode("utf-8"))


def registry_pack_bytes() -> int:
    """Recomputed byte size of the whole overlay registry: the ungated-arm charge."""
    registry = load_json(REGISTRY_PATH)
    return sum(len(overlay["prose"].encode("utf-8")) for overlay in registry["overlays"])


def no_worse_work(after: Dict[str, int], before: Dict[str, int]) -> bool:
    """Every recorded work category is equal or lower in the gated arm."""
    return all(after[key] <= before[key] for key in REQUIRED_WORK_KEYS)


# --- B04: the measured-work rule -------------------------------------------


def measures_total_work(text: str) -> bool:
    body = flat(text)
    return (
        "total work is no worse" in body
        and "re-reads of a file already read" in body
        and "searches retried after an empty result" in body
    )


def rejects_opening_token_optimisation(text: str) -> bool:
    return "token reduction as efficiency evidence" in flat(text)


def keeps_the_retrieval_identifier(text: str) -> bool:
    body = flat(text)
    restores = "restores the payload in one call" in body or "restores the full text" in body
    return "retrieval identifier" in body and restores


def discloses_truncation(text: str) -> bool:
    return "disclose truncation" in flat(text).lower()


def test_the_context_owner_measures_total_work() -> None:
    body = owner(GUARD)
    assert measures_total_work(body), "the context owner optimises opening tokens only"
    assert rejects_opening_token_optimisation(body), (
        "a token reduction must not stand in for measured efficiency"
    )


def test_the_context_owner_keeps_the_retrieval_identifier_and_discloses_truncation() -> None:
    body = owner(GUARD)
    assert keeps_the_retrieval_identifier(body), "a deferred payload loses its retrieval id"
    assert discloses_truncation(body), "truncation is silent"


def test_the_authoring_owner_bounds_its_output() -> None:
    body = owner(WRITING)
    assert "## Bound the output, and state its condition" in body
    assert keeps_the_retrieval_identifier(body), "the bounded output drops its retrieval id"
    assert discloses_truncation(body), "the bounded output hides its truncation"
    assert "Cut prose nobody acts on." in body


def test_shortening_the_prompt_alone_fails_the_shipped_predicate() -> None:
    """Negative control: the measured-work predicate is not vacuous."""
    token_diet = flat(
        "Keep the opening prompt small. Shorten tool descriptors to reduce tokens; "
        "the first response is what the reader pays for."
    )
    assert not measures_total_work(token_diet)
    assert not rejects_opening_token_optimisation(token_diet)
    assert not keeps_the_retrieval_identifier(token_diet)
    assert not discloses_truncation(token_diet)


# --- B03/B20: the positive capability predicate ----------------------------


def gates_on_a_positive_capability(text: str) -> bool:
    body = flat(text)
    return (
        "positive predicate first" in body
        and "the project declares the capability" in body
        and "explicit request matches" in body
    )


def types_the_unsupported_response(text: str) -> bool:
    body = flat(text)
    return "`BLOCKED`" in body and "`UNTESTED`" in body and "never silently skipped" in body


def deactivates_on_a_prohibited_context(text: str) -> bool:
    body = flat(text)
    return (
        "prohibited context" in body
        and "deactivates the pack" in body
        and "even when the capability exists" in body
    )


def states_its_own_condition(text: str) -> bool:
    return "states its condition in its first line" in flat(text)


def test_the_context_owner_gates_overlays_on_a_positive_capability() -> None:
    body = owner(GUARD)
    assert gates_on_a_positive_capability(body), "an overlay loads without a predicate"
    assert types_the_unsupported_response(body), "an absent capability is silently skipped"
    assert deactivates_on_a_prohibited_context(body), "a prohibited context keeps the pack"
    assert states_its_own_condition(body), "a pack cannot be rejected without loading it"


def test_an_unconditional_overlay_fails_the_shipped_predicate() -> None:
    """Negative control: the gating predicate rejects the ungated baseline."""
    ungated = flat(
        "### UI overlay: always load the UI, bilingual and forge-stack checklists for every task; "
        "report a warning when the project has no such capability."
    )
    assert not gates_on_a_positive_capability(ungated)
    assert not types_the_unsupported_response(ungated)
    assert not deactivates_on_a_prohibited_context(ungated)


def test_the_owners_name_every_capability_family_the_registry_gates() -> None:
    """The gating prose covers the registry's families, so no pack is admitted by silence."""
    body = flat(owner(GUARD))
    registry = load_json(REGISTRY_PATH)
    families = {overlay["required_capability"] for overlay in registry["overlays"]}
    assert families - {"dsh_theme_tokens"} == set(CAPABILITY_FAMILIES), (
        "the registry gained a capability family; name it in the gating contract"
    )
    for capability, word in CAPABILITY_FAMILIES.items():
        assert word in body, f"the gating contract does not name the {capability} family"


def test_the_gating_contract_uses_the_registrys_typed_responses() -> None:
    """One vocabulary: the responses the owners promise are the ones the registry declares."""
    guard = owner(GUARD)
    registry = load_json(REGISTRY_PATH)
    responses = {overlay["unsupported_response"] for overlay in registry["overlays"]}
    for response in responses:
        assert f"`{response}`" in guard, f"the gating contract omits {response}"


def test_the_atom_table_still_names_these_owners() -> None:
    rows = flat(ATOM_TABLE.read_text(encoding="utf-8"))
    assert "B04 ContextBudget" in rows and "principle-guard-the-context-window" in rows
    assert "B03 SkillEligibility" in rows and "B20 DomainOverlay" in rows


# --- B20: project-owned domain guidance ------------------------------------


def keeps_domain_guidance_project_owned(text: str) -> bool:
    body = flat(text)
    return (
        "Domain guidance is project-owned, never universal" in body
        and "never state it as a common requirement" in body
    )


DOMAIN_TOPICS = ("UI copy, layout, colour", "Bilingual documentation", "Upgrade guides", "Archival notes", "Recorded demonstrations", "Forge and stack commands")


def test_the_authoring_owner_keeps_domain_guidance_project_owned() -> None:
    body = owner(WRITING)
    assert keeps_domain_guidance_project_owned(body), "domain guidance is written as universal"
    for topic in DOMAIN_TOPICS:
        assert f"**{topic}.**" in body, f"{topic} left the project-owned list"


def test_an_absent_facility_is_typed_not_approximated() -> None:
    body = flat(owner(WRITING))
    assert "absent facility is a stated gap" in body
    assert "`BLOCKED`" in body and "`UNTESTED`" in body


def test_universal_domain_guidance_fails_the_shipped_predicate() -> None:
    """Negative control: guidance stated as a common requirement is rejected."""
    universal = flat(
        "UI copy, bilingual pairs, upgrade guides and forge stack commands follow the pstack "
        "standard theme and the pstack translation table."
    )
    assert not keeps_domain_guidance_project_owned(universal)
    assert "**UI copy, layout, colour.**" not in universal


def test_the_docs_surfaces_name_the_contracts_they_describe() -> None:
    principles = flat(owner(PRINCIPLES_DOC))
    assert "measures the whole task's work" in principles
    assert "only for a capability the project declares" in principles
    authoring = flat(owner(AUTHORING_DOC))
    assert "bounds the output" in authoring
    assert "project-owned" in authoring


# --- the recorded task-work traces ----------------------------------------


def traces() -> Dict:
    assert TRACES_PATH.is_file(), "record the two task-work traces"
    return load_json(TRACES_PATH)


def test_two_tasks_are_recorded_with_both_arms() -> None:
    trace = traces()
    tasks = trace["tasks"]
    assert len(tasks) == 2, "two real task traces are the acceptance bar"
    for task in tasks:
        assert set(task["arms"]) == {"before", "after"}
        assert task["task_sha256"] == hashlib.sha256(task["goal"].encode()).hexdigest(), (
            f"{task['id']} is not pinned to the goal it records"
        )
        before, after = task["arms"]["before"], task["arms"]["after"]
        assert before["acceptance"]["command"] == after["acceptance"]["command"], (
            f"{task['id']} arms did not run the same acceptance check"
        )
        assert before["acceptance"]["passed"] and after["acceptance"]["passed"], (
            f"{task['id']} did not pass its acceptance check in both arms"
        )


@pytest.mark.parametrize("task_id", ["T1", "T2"])
def test_each_arm_accounts_for_re_reads_and_search_retries(task_id: str) -> None:
    """The spec's total cost is searches + reads + errors + tokens, not opening tokens."""
    task = next(t for t in traces()["tasks"] if t["id"] == task_id)
    for arm_name, arm in task["arms"].items():
        work = arm["work"]
        missing = [key for key in REQUIRED_WORK_KEYS if key not in work]
        assert not missing, f"{task_id}/{arm_name} leaves {missing} unaccounted"
        assert set(arm["work_source"]) >= {"counted_from", "cross_check"}
        assert arm["work_source"]["counted_from"], f"{task_id}/{arm_name} declares no source"


@pytest.mark.parametrize("task_id", ["T1", "T2"])
def test_the_gated_arm_charges_fewer_bytes_than_the_ungated_arm(task_id: str) -> None:
    task = next(t for t in traces()["tasks"] if t["id"] == task_id)
    before, after = task["arms"]["before"], task["arms"]["after"]
    assert before["charged_bytes"] == registry_pack_bytes(), (
        "the ungated arm is not charged the whole registry; regenerate the trace"
    )
    assert after["charged_bytes"] == gated_contract_bytes(), (
        "the gated arm is not charged the whole owner contract it carried; regenerate the trace"
    )
    assert after["charged_bytes"] < before["charged_bytes"]
    assert task["comparison"]["saving_bytes"] == registry_pack_bytes() - gated_contract_bytes()
    # The saving on these two bounded tasks is small, and the trace says so rather than
    # reporting the displacement of the registry as if it were the observed saving.
    assert task["comparison"]["saving_bytes"] < 0.02 * registry_pack_bytes()


@pytest.mark.parametrize("task_id", ["T1", "T2"])
def test_the_literal_payload_each_lane_carried_is_recorded(task_id: str) -> None:
    """The as-run payload is recorded next to the recomputed charge, so neither hides the other."""
    task = next(t for t in traces()["tasks"] if t["id"] == task_id)
    before, after = task["arms"]["before"], task["arms"]["after"]
    assert before["as_run_payload_bytes"] > 0 and after["as_run_payload_bytes"] > 0
    assert after["as_run_payload_bytes"] < before["as_run_payload_bytes"]


def test_the_contract_is_smaller_than_the_prose_it_displaces() -> None:
    """A gating contract that costs more context than the packs would be no bargain."""
    union = gated_contract_bytes()
    assert union < registry_pack_bytes(), (
        f"owner contracts add {union} bytes and displace {registry_pack_bytes()}"
    )


@pytest.mark.parametrize("task_id", ["T1", "T2"])
def test_the_gated_arm_does_no_more_work_than_the_ungated_arm(task_id: str) -> None:
    task = next(t for t in traces()["tasks"] if t["id"] == task_id)
    before, after = task["arms"]["before"]["work"], task["arms"]["after"]["work"]
    assert no_worse_work(after, before), f"{task_id}: gated arm does more work"
    assert task["comparison"]["work_no_worse"] is True


def test_both_arms_pass_the_same_acceptance_check() -> None:
    """No quality loss: the same check passes in both arms with the same artifact result."""
    for task in traces()["tasks"]:
        before, after = task["arms"]["before"], task["arms"]["after"]
        assert before["acceptance"]["passed"] == after["acceptance"]["passed"] is True
        assert task["comparison"]["quality_parity"] is True
        assert task["comparison"]["quality_evidence"], "parity is claimed without evidence"


def test_the_recorded_totals_match_the_recorded_tasks() -> None:
    trace = traces()
    for key in REQUIRED_WORK_KEYS:
        before = sum(task["arms"]["before"]["work"][key] for task in trace["tasks"])
        after = sum(task["arms"]["after"]["work"][key] for task in trace["tasks"])
        assert trace["totals"]["work"]["before"][key] == before
        assert trace["totals"]["work"]["after"][key] == after
    assert trace["totals"]["charged_bytes"]["before"] == 2 * registry_pack_bytes()
    assert trace["totals"]["charged_bytes"]["after"] == 2 * gated_contract_bytes()
    assert trace["totals"]["saving_bytes"] == 2 * (registry_pack_bytes() - gated_contract_bytes())
    assert trace["totals"]["as_run_payload_bytes"] == {
        "before": sum(t["arms"]["before"]["as_run_payload_bytes"] for t in trace["tasks"]),
        "after": sum(t["arms"]["after"]["as_run_payload_bytes"] for t in trace["tasks"]),
    }
    assert trace["totals"]["work_no_worse"] is True
    assert trace["totals"]["quality_parity"] is True


def test_the_trace_declares_what_it_did_not_measure() -> None:
    method = traces()["method"]
    assert method["not_measured"], "an unmeasured list is what keeps a trace honest"
    joined = " ".join(method["not_measured"]).lower()
    assert "token" in joined and "judge" in joined
    assert method["work_measure"], "the work measure must name its instrument"
    assert "transcript" in method["work_measure"]


def test_a_regressing_arm_fails_the_shipped_predicate() -> None:
    """Negative control: the no-worse-work predicate is not vacuous."""
    before = {key: 2 for key in REQUIRED_WORK_KEYS}
    equal = dict(before)
    worse = dict(before, re_reads=3)
    assert no_worse_work(equal, before)
    assert not no_worse_work(worse, before)


if __name__ == "__main__":
    raise SystemExit(
        "contract suite for the measured-context and bounded-output owners; "
        "run with pytest"
    )
