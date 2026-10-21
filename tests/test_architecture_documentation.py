"""Pin the architecture guide to the current schema/profile/transport contract.

These tests are intentionally small and source-derived. They check that a reader
can find the current guide and that its factual, enumerable claims agree with
the files checked out on this exact PR head. They do NOT certify native execution,
JEV privacy, live API support, or the correctness of advisory admission.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "architecture" / "harness-adapters-and-jev-2026-10-20.md"


def _doc() -> str:
    return ARCH.read_text(encoding="utf-8")


def test_architecture_is_linked_from_readme_and_porting_guide() -> None:
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    porting = (ROOT / "docs" / "guide" / "12-porting.md").read_text(encoding="utf-8")
    assert "./docs/architecture/harness-adapters-and-jev-2026-10-20.md" in root_readme
    assert "../architecture/harness-adapters-and-jev-2026-10-20.md" in porting
    assert "Historical Batch 2 acceptance matrix" in porting


def test_current_schema_inventory_matches_documented_schema_names() -> None:
    discovered = {p.name for p in (ROOT / "schemas" / "portability").glob("*.schema.json")}
    documented = set(re.findall(r"`([a-z-]+\.schema\.json)`", _doc()))
    assert discovered == documented, (
        f"documented schema inventory drift: missing={discovered - documented}, "
        f"not shipped={documented - discovered}"
    )


def test_host_support_table_reflects_actual_profiles() -> None:
    table = dict(re.findall(
        r"^\|\s*`([a-z][a-z0-9:-]*)`\s*\|[^\n]*?\|\s*"
        r"`(candidate|mapped|packaged|verified|supported)`\s*\|",
        _doc(),
        re.MULTILINE,
    ))
    profiles = {
        json.loads(path.read_text(encoding="utf-8"))["host"]:
        json.loads(path.read_text(encoding="utf-8"))["support_state"]
        for path in (ROOT / "profiles").glob("*.json")
    }
    assert table == profiles, f"documented host states must match live profile declarations: {table=} {profiles=}"
    package = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    assert set(package["host_targets"]) <= set(table), "shipped targets missing from host table"


def test_upstream_source_of_truth_matches_package_pin() -> None:
    desc = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    canonical = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert f"tree {desc['upstream_pin']}" in canonical
    assert desc["upstream_pin"] in _doc()
    assert desc["version"] in _doc()


def test_documented_relative_links_resolve_within_repository() -> None:
    text = _doc()
    for match in re.findall(r"\]\(([^)]+)\)", text):
        if match.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative = match.split("#", 1)[0]
        if not relative:
            continue
        target = (ARCH.parent / relative).resolve()
        assert target.is_relative_to(ROOT.resolve()), f"documentation path escapes repository: {match}"
        assert target.exists(), f"architecture documentation references missing path: {match}"


def test_jev_implementation_caveats_remain_explicit() -> None:
    decision_source = (ROOT / "scripts" / "decision_adapter.py").read_text(encoding="utf-8")
    doc = _doc()
    assert "import urllib.request" in decision_source
    assert "urllib" in doc
    assert "default" in doc.lower() and "OFF" in doc
    assert "Choice-only" in doc
    # Every current high-risk JEV caveat must have an owner, rather than appearing
    # to be solved by this documentation change or by a historical closed issue.
    for issue in ("#658", "#659", "#660", "#663", "#664"):
        assert issue in doc



def test_localized_readmes_agree_on_portable_authority_and_host_scope() -> None:
    """Both entry points distinguish a six-host descriptor from Grok-only setup."""
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    guide = "docs/architecture/harness-neutral-authority-2026-10-21.md"
    assert guide in english
    assert guide in chinese
    assert "multi-harness reference port" in english
    assert "多 Agent Harness 可移植参考实现" in chinese
    assert "Grok Build is one host adapter" in english
    assert "Grok Build 是其中一个宿主适配器" in chinese
    assert "## Grok Build installation" in english
    assert "## Grok Build 安装" in chinese
    assert "## Grok Build 默认模型与 effort" in chinese
    assert "Droid" in chinese
