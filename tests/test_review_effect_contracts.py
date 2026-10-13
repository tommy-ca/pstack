"""P13 (#313): review, failure-ownership and simplification contracts.

The DeepSeek atoms B06/B11/B12/B13/B17/B18/B19 are composed into owners that already
exist — `thermo-nuclear-code-quality-review`, `interrogate`, `fix-ci` and `how` — never
into a second `dsh-*` namespace. These cases hold that composition:

- the atom table maps each scoped atom to a real pstack owner, and no `dsh-*` skill exists;
- each owner states its contract in prose the check can read;
- the negative controls are not vacuous: a log-and-retry observer, a style-nit-only
  review, and a zero-reference deletion each fail the shipped predicate;
- a read-only audit mutates nothing.

The predicates are intentionally small text contracts, the same shape
`tests/test_playbook_parity.py` uses for the swarm/arena/interrogate playbooks.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT / "openspec" / "changes" / "archive" / "2026-10-11-deepseek-skill-portability"
ATOM_TABLE = CHANGE / "atomic-patterns.md"
SPEC = CHANGE / "specs" / "pstack-reusable-skill-patterns" / "spec.md"

SCANNER = ROOT / "scripts" / "scan-host-boundary.py"
_scanner_spec = importlib.util.spec_from_file_location("p13_scan_host_boundary", SCANNER)
assert _scanner_spec is not None and _scanner_spec.loader is not None
scan_host_boundary = importlib.util.module_from_spec(_scanner_spec)
sys.modules["p13_scan_host_boundary"] = scan_host_boundary
_scanner_spec.loader.exec_module(scan_host_boundary)

# The atoms this unit owns, and the owners this unit extends. `bug-fix`, `refactoring`,
# `perf-issue` and `shipping` are poteto-mode playbooks; `review` is the host's bundled
# single-reviewer command (the fallback named in `interrogate`), not a skill to duplicate.
SCOPED_ATOMS = ("B06", "B11", "B12", "B13", "B17", "B18", "B19")
UNIT_OWNERS = ("thermo-nuclear-code-quality-review", "interrogate", "fix-ci", "how")
NON_SKILL_OWNERS = {"review": "host-bundled single-reviewer command, not a skill"}
EFFECT_STATUSES = ("none", "partial", "committed", "unknown")


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def owner(name: str) -> str:
    path = ROOT / "skills" / name / "SKILL.md"
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def resolves(token: str) -> bool:
    return (
        (ROOT / "skills" / token / "SKILL.md").is_file()
        or (ROOT / "skills" / "poteto-mode" / "playbooks" / f"{token}.md").is_file()
        or token in NON_SKILL_OWNERS
    )


def atom_rows() -> dict[str, list[str]]:
    """Table rows keyed by atom id, as their cells."""
    rows: dict[str, list[str]] = {}
    for line in ATOM_TABLE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| B"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows[cells[0].split()[0]] = cells
    return rows


# --- the composition: existing owners, no second namespace --------------------


def test_no_dsh_skill_namespace_is_created() -> None:
    """A DSH-derived behavior extends an existing owner; it is not a new `dsh-*` skill."""
    offenders = sorted(
        p.name for p in (ROOT / "skills").iterdir() if p.is_dir() and p.name.startswith("dsh")
    )
    assert offenders == []
    assert not (ROOT / "dsh").exists()


def test_every_scoped_atom_maps_to_a_real_owner() -> None:
    rows = atom_rows()
    missing = [atom for atom in SCOPED_ATOMS if atom not in rows]
    assert missing == [], f"atom table lost rows: {missing}"

    for atom in SCOPED_ATOMS:
        owner_cell = rows[atom][-1]
        assert owner_cell, f"{atom} names no owner"
        named = re.findall(r"`([^`]+)`", owner_cell)
        unresolved = [token for token in named if not resolves(token)]
        assert unresolved == [], f"{atom} points at owners that do not exist: {unresolved}"
        # B06's owner cell is prose ("Existing adapter/security boundary"), not a token.
        assert named or "boundary" in owner_cell, f"{atom} names no owner: {owner_cell}"


def test_the_unit_extends_owners_the_atom_table_already_names() -> None:
    """No invented owner: each of the four files is a declared target somewhere in the table."""
    declared = {
        token
        for cells in atom_rows().values()
        for token in re.findall(r"`([^`]+)`", cells[-1])
    }
    assert set(UNIT_OWNERS) <= declared, f"undeclared owner: {set(UNIT_OWNERS) - declared}"


def test_the_unit_owners_exist() -> None:
    for name in UNIT_OWNERS:
        assert resolves(name), name


# --- B12/B13/B18: reachability and behavior evidence before deletion ----------


def requires_consumer_reachability(text: str) -> bool:
    flat_text = " ".join(text.split())
    return (
        "consumer reachability" in flat_text.lower()
        and "not evidence of deletability" in flat_text
    )


def requires_behavior_pin(text: str) -> bool:
    flat_text = " ".join(text.split())
    return "behavior pin" in flat_text and "never exercised the path" in flat_text


def reduces_maintained_obligation(text: str) -> bool:
    flat_text = " ".join(text.split()).lower()
    return "maintained obligation" in flat_text and (
        "is not the measure" in flat_text or "rather than how many lines" in flat_text
    )


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "how", "interrogate"])
def test_deletion_needs_consumer_reachability_not_absence_of_references(name: str) -> None:
    assert requires_consumer_reachability(owner(name)), f"{name} allows reference-free deletion"


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "how"])
def test_a_moved_or_deleted_seam_needs_a_behavior_pin(name: str) -> None:
    assert requires_behavior_pin(owner(name)), f"{name} accepts a compile as equivalence"


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "how"])
def test_simplification_is_measured_in_removed_obligations(name: str) -> None:
    assert reduces_maintained_obligation(owner(name)), f"{name} measures deleted lines"


def test_a_protected_seam_is_only_removed_as_a_migration() -> None:
    """A reachable seam is a breaking change with a migration, never cleanup."""
    assert (
        "A protected seam is removed only as an explicit breaking change with a migration; never as cleanup."
        in flat(ROOT / "skills" / "thermo-nuclear-code-quality-review" / "SKILL.md")
    )


def test_zero_reference_deletion_is_rejected_by_the_shipped_predicate() -> None:
    """Negative control: the reachability and behavior-pin predicates are not vacuous."""
    shipped = owner("thermo-nuclear-code-quality-review")
    assert requires_consumer_reachability(shipped) and requires_behavior_pin(shipped)

    unsafe = shipped.replace(
        "No in-repo reference is not evidence of deletability",
        "No in-repo reference proves the identifier is dead",
    )
    assert not requires_consumer_reachability(unsafe)
    assert requires_consumer_reachability(shipped), "the mutation must be the only difference"

    compile_only = shipped.replace(
        "that never exercised the path is", "that is the pin and"
    )
    assert not requires_behavior_pin(compile_only)


# --- B11/B19: typed effect status, recovery owner, honest report --------------


def classifies_typed_effect(text: str) -> bool:
    flat_text = " ".join(text.split())
    return (
        "`none | partial | committed | unknown`" in flat_text
        and "Only the state owner declares recovery" in flat_text
    )


def blocks_blind_retry(text: str) -> bool:
    flat_text = " ".join(text.split()).lower()
    return (
        "blind retry" in flat_text
        and "forbidden" in flat_text
        and all(status in flat_text for status in ("partial", "unknown"))
    )


def reports_without_a_success_claim(text: str) -> bool:
    flat_text = " ".join(text.split())
    return (
        "partial" in flat_text
        and "success" in flat_text
        and ("safe next step" in flat_text or "safe next action" in flat_text)
    )


@pytest.mark.parametrize("name", ["interrogate", "fix-ci"])
def test_failures_carry_typed_identity_and_effect_status(name: str) -> None:
    assert classifies_typed_effect(owner(name)), f"{name} has no typed effect status"


@pytest.mark.parametrize("name", ["interrogate", "fix-ci"])
def test_partial_or_unknown_effects_block_a_blind_retry(name: str) -> None:
    assert blocks_blind_retry(owner(name)), f"{name} allows a blind retry"


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "interrogate", "fix-ci"])
def test_unresolved_effects_are_reported_without_a_success_claim(name: str) -> None:
    assert reports_without_a_success_claim(owner(name)), f"{name} claims success on a partial effect"


def test_log_and_retry_fails_the_shipped_predicate() -> None:
    """Negative control: catching, logging and retrying is not recovery."""
    shipped = owner("fix-ci")
    assert classifies_typed_effect(shipped) and blocks_blind_retry(shipped)

    log_and_retry = shipped.replace(
        "Only the state owner declares recovery",
        "The agent that caught the error declares recovery",
    ).replace("a blind retry is forbidden", "an immediate retry is the default")
    assert not classifies_typed_effect(log_and_retry)
    assert not blocks_blind_retry(log_and_retry)


def test_the_spec_keeps_the_status_vocabulary_the_owners_use() -> None:
    """One vocabulary: the spec's effect statuses are the ones the owners state."""
    spec = flat(SPEC)
    assert "document effect status as none, partial, committed or unknown" in spec
    assert "Only the state owner MAY declare recovery, rollback or retry safety" in spec
    for name in ("interrogate", "fix-ci"):
        flat_owner = flat(ROOT / "skills" / name / "SKILL.md").lower()
        for status in EFFECT_STATUSES:
            assert status in flat_owner, f"{name} drops the {status!r} effect status"


# --- B17: exact-head review, ranked findings, no style-nit substitute ---------


def pins_base_and_head(text: str) -> bool:
    flat_text = " ".join(text.split())
    return "base" in flat_text and ("head commit" in flat_text or "head revision" in flat_text)


def ranks_by_observable_impact(text: str) -> bool:
    flat_text = " ".join(text.split()).lower()
    return "order findings by observable impact" in flat_text


def rejects_a_style_nit_substitute(text: str) -> bool:
    flat_text = " ".join(text.split())
    return "MUST NOT stand in for the lifecycle" in flat_text


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "interrogate", "how"])
def test_review_pins_its_base_and_head(name: str) -> None:
    assert pins_base_and_head(owner(name)), f"{name} reviews an unbound revision"


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "interrogate", "how"])
def test_findings_are_ranked_by_observable_impact(name: str) -> None:
    assert ranks_by_observable_impact(owner(name)), f"{name} ranks findings by taste"


@pytest.mark.parametrize("name", ["thermo-nuclear-code-quality-review", "interrogate"])
def test_a_style_nit_list_is_not_the_lifecycle_review(name: str) -> None:
    assert rejects_a_style_nit_substitute(owner(name)), f"{name} accepts a style-only review"


def test_style_nit_only_review_fails_the_shipped_predicate() -> None:
    """Negative control: a naming list can never stand in for the lifecycle review."""
    shipped = owner("thermo-nuclear-code-quality-review")
    assert rejects_a_style_nit_substitute(shipped)

    style_only = shipped.replace(
        "MUST NOT stand in for the lifecycle, consumer, and security review",
        "may stand in for the lifecycle review",
    )
    assert not rejects_a_style_nit_substitute(style_only)


# --- read-only audit: mutation-free by observation ---------------------------


def tree_digest(root: Path, suffix: str | None = ".md") -> dict[str, str]:
    paths = root.rglob(f"*{suffix}") if suffix else root.rglob("*")
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def test_a_read_only_audit_triggers_no_mutation(tmp_path: Path) -> None:
    """The audit reports a violation and leaves the tree exactly as it found it."""
    audit_root = tmp_path / "audit"
    (audit_root / "skills" / "sample").mkdir(parents=True)
    (audit_root / "skills" / "sample" / "SKILL.md").write_text(
        "Start a worker with spawn_subagent.\n", encoding="utf-8"
    )
    shutil.copytree(ROOT / "profiles", audit_root / "profiles")

    before = tree_digest(audit_root, suffix=None)
    _, violations, scanned = scan_host_boundary.run_scan(audit_root, audit_root / "profiles")

    assert scanned == 1
    assert violations, "the audit found no violation in a tree that plants one"
    assert tree_digest(audit_root, suffix=None) == before


def test_the_repository_audit_is_clean_and_read_only() -> None:
    """A real read-only audit over this checkout: zero violations, zero writes."""
    before = tree_digest(ROOT / "skills")
    _, violations, scanned = scan_host_boundary.run_scan(ROOT, ROOT / "profiles")

    assert violations == [], violations
    assert scanned > 0
    assert tree_digest(ROOT / "skills") == before
