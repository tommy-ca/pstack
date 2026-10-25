"""P9 + P7: parity invariants shared by the swarm, arena and interrogate playbooks.

P9: each playbook must name (1) a bounded join deadline whose expiry is a reported
dropout, (2) an evidence binding that replaces prose-only verdicts, and (3) the
declared host census source read through ``get_declared_hosts``.

P7 (#293): each playbook is recomposed over the host's native dispatch routes —
frozen briefs, isolated writers, a bounded join, gap-preserving synthesis — so no
playbook can turn a dropped or cancelled lane into a pass, and none may present a
reused keep-alive worker context as independent. The native routes themselves
(`task` batch and eval ``agent()``, with their cancel paths) are exercised by
``scripts/prove-omp-vertical-slice.py`` (#292); these cases hold the playbook and
host-reference contract around that lever instead of re-proving spawn/join.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS = ("swarm", "arena", "interrogate")

BINDINGS = ("receipt scenario id", "file hash", "head sha", "commit sha")
CENSUS_TOKENS = ("pstack.package.json#host_targets", "get_declared_hosts")


from scripts.evidence_index import get_declared_hosts

def playbook(name: str) -> str:
    path = ROOT / "skills" / name / "SKILL.md"
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def declared_hosts() -> list[str]:
    return get_declared_hosts()


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_playbook_names_a_bounded_join_deadline(name: str) -> None:
    text = playbook(name)
    assert "bounded join deadline named before spawn" in text, f"{name} names no bounded join deadline"
    assert re.search(r"join deadline: \d", text), f"{name} never bounds the deadline"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_playbook_binds_evidence_not_prose(name: str) -> None:
    text = playbook(name)
    assert "prose-only" in text, f"{name} allows prose-only verdicts"
    assert any(token in text.lower() for token in BINDINGS), f"{name} names no evidence binding"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_playbook_names_the_declared_census_source(name: str) -> None:
    text = playbook(name)
    for token in CENSUS_TOKENS:
        assert token in text, f"{name} does not name {token}"
    assert "missing host is a stated gap" in text, f"{name} hides missing hosts"


def test_swarm_deadline_miss_is_a_reported_dropout() -> None:
    text = playbook("swarm")
    assert "has not returned by the deadline is a reported dropout, never a pass" in text
    assert "The report names the deadline it enforced and which lanes it dropped." in text


def test_census_source_matches_the_declared_manifest() -> None:
    manifest = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    hosts = declared_hosts()
    assert hosts == manifest["host_targets"]
    assert hosts, "no declared hosts to report parity against"


# --- P7 (#293): native dispatch, dropout and cancellation negatives -----------

REFERENCE = ROOT / "skills" / "poteto-mode" / "references" / "omp-tools.md"
LEVER = ROOT / "scripts" / "prove-omp-vertical-slice.py"
ORCHESTRATE = ROOT / "skills" / "poteto-mode" / "playbooks" / "orchestrate.md"

FREEZE_CLAUSE = {
    "swarm": "Freeze each brief before dispatch",
    "arena": "Freeze the task and the rubric before any candidate spawns",
    "interrogate": "The pack is frozen before spawn",
}
DISPATCH_CLAUSE = (
    "fan-out route the active harness profile binds",
    "host reference names the concrete mechanism",
)
INDEPENDENCE_CLAUSE = ("warm or keep-alive worker", "adaptation or a gap")
GAP_CLAUSE = {
    "swarm": "keeps its gap in the table and in the report",
    "arena": "keeps its gap in the synthesis record",
    "interrogate": "keeps its gap",
}
CANCEL_NEGATIONS = ("never becomes a pass", "never a pass", "not a pass")
NATIVE_ROUTES = {
    "task batch": ("tasks[]", "task.batch", "write proc://<id>/kill"),
    "eval agent()": ("agent()", "wait(handles, timeout)", "handle.cancel()"),
}


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def cancel_clause(text: str) -> str:
    match = re.search(r"[^.]*you cancel[^.]*\.", text)
    assert match is not None, "no clause covers cancelling a lane"
    return match.group(0)


def reports_cancel_as_dropout(text: str) -> bool:
    clause = re.search(r"[^.]*you cancel[^.]*\.", " ".join(text.split()))
    if clause is None:
        return False
    return "dropout" in clause.group(0) and any(n in clause.group(0) for n in CANCEL_NEGATIONS)


def gates_reuse_on_observed_fresh_agents(text: str) -> bool:
    flat_text = " ".join(text.split())
    return (
        "`eval.workpool.freshAgents=true`" in flat_text
        and "observed in the run's effective settings" in flat_text
        and "MUST NOT be presented as a blinded independent context" in flat_text
    )


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_playbook_freezes_its_brief_before_dispatch(name: str) -> None:
    assert FREEZE_CLAUSE[name] in playbook(name), f"{name} dispatches an unfrozen brief"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_playbook_names_the_dispatch_route_it_used(name: str) -> None:
    text = playbook(name)
    for token in DISPATCH_CLAUSE:
        assert token in text, f"{name} does not name the {token!r} route"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_reused_keep_alive_context_is_not_independent(name: str) -> None:
    """Negative: a warm reused worker may never be reported as a fresh lane."""
    text = playbook(name)
    for token in INDEPENDENCE_CLAUSE:
        assert token in text, f"{name} hides reuse instead of reporting it as {token!r}"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_cancelled_lane_is_a_reported_dropout_and_never_a_pass(name: str) -> None:
    text = playbook(name)
    clause = cancel_clause(text)
    assert "dropout" in clause, f"{name} lets a cancelled lane vanish: {clause}"
    assert any(n in clause for n in CANCEL_NEGATIONS), f"{name} lets a cancelled lane pass: {clause}"


@pytest.mark.parametrize("name", PLAYBOOKS)
def test_dropout_keeps_its_gap_in_synthesis(name: str) -> None:
    assert GAP_CLAUSE[name] in playbook(name), f"{name} backfills a dropped lane"


def test_cancel_dropout_predicate_rejects_a_lane_absorbing_playbook() -> None:
    """Negative control: the cancellation check is not vacuous."""
    text = playbook("swarm")
    assert reports_cancel_as_dropout(text)
    absorbed = text.replace("never becomes a pass", "counts as a pass")
    assert not reports_cancel_as_dropout(absorbed)


def test_host_reference_names_both_native_routes_and_their_cancel_paths() -> None:
    text = flat(REFERENCE)
    assert "not interchangeable" in text, "the two dispatch routes are presented as one"
    for route, tokens in NATIVE_ROUTES.items():
        for token in tokens:
            assert token in text, f"the {route} route does not name {token}"
    for token in (
        "lane still running at the deadline is a dropout",
        "`wait(handles, timeout)` raises `TimeoutError`",
        "a cancelled lane settles as `cancelled`",
    ):
        assert token in text, f"the host reference does not settle {token}"


def test_host_reference_gates_reuse_independence_on_observed_fresh_agents() -> None:
    """Negative: keep-alive reuse counts as independence only when freshAgents is observed."""
    reference = REFERENCE.read_text(encoding="utf-8")
    assert gates_reuse_on_observed_fresh_agents(reference)
    ungated = reference.replace(
        "unless `eval.workpool.freshAgents=true` was\n  observed in the run's effective settings",
        "because",
    )
    assert not gates_reuse_on_observed_fresh_agents(ungated)


def test_orchestrate_labels_flat_depth_adapted_and_nested_parity_a_gap() -> None:
    text = flat(ORCHESTRATE)
    assert "classified `adapted`" in text, "flat depth is not labelled adapted"
    assert "`gap` for nested track sub-coordinator ownership, cancellation and terminal joins" in text
    assert "no run here has observed" in text, "nested depth is claimed without observation"


def test_playbook_cases_reference_the_p6_lever_instead_of_respawning_it() -> None:
    assert LEVER.is_file(), "the P6 spawn/join lever these cases rest on is missing"
