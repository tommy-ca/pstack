"""P9: parity invariants shared by the swarm, arena and interrogate playbooks.

Each playbook must name (1) a bounded join deadline whose expiry is a reported
dropout, (2) an evidence binding that replaces prose-only verdicts, and (3) the
declared host census source read through ``get_declared_hosts``.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS = ("swarm", "arena", "interrogate")

BINDINGS = ("receipt scenario id", "file hash", "head sha", "commit sha")
CENSUS_TOKENS = ("pstack.package.json#host_targets", "get_declared_hosts")


def playbook(name: str) -> str:
    path = ROOT / "skills" / name / "SKILL.md"
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def declared_hosts() -> list[str]:
    spec = importlib.util.spec_from_file_location("verify_portable", ROOT / "scripts" / "verify-portable.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_declared_hosts()


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
