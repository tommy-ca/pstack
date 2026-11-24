"""Regression and parity checks for Cursor PStack 0.15.46-0.15.48 wave 1."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import (
    canonical_index,
    package_install_staging,
    package_projection,
    prove_antigravity_native_package,
)


def test_reframe_skill_and_docs_present() -> None:
    reframe = (ROOT / "skills" / "reframe" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: reframe" in reframe
    assert "disable-model-invocation: true" in reframe
    assert "8 to 12 terms" in reframe
    assert "2 or 3 neighboring fields" in reframe
    assert "Open every link" in reframe

    for doc_path in (
        ROOT / "skills" / "poteto-help" / "SKILL.md",
        ROOT / "docs" / "guide" / "02-poteto-mode.md",
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
    ):
        assert "/reframe" in doc_path.read_text(encoding="utf-8"), str(doc_path)


def test_statechart_windows_portability_ported() -> None:
    skill = (ROOT / "skills" / "statechart" / "SKILL.md").read_text(encoding="utf-8")
    dot_ts = (
        ROOT / "skills" / "statechart" / "scripts" / "frontends" / "dot.ts"
    ).read_text(encoding="utf-8")
    run_ts = (ROOT / "skills" / "statechart" / "scripts" / "run.ts").read_text(
        encoding="utf-8"
    )
    statechart_ts = (
        ROOT / "skills" / "statechart" / "scripts" / "statechart.ts"
    ).read_text(encoding="utf-8")

    assert "--disable-warning=ExperimentalWarning" in skill
    assert (ROOT / "skills" / "statechart" / "scripts" / "janitor.ts").is_file()
    assert (ROOT / "skills" / "statechart" / "scripts" / "kill.ts").is_file()
    assert "export const splitLines" in dot_ts
    assert "-Dstdout.encoding=UTF-8" in run_ts
    assert "-Dstderr.encoding=UTF-8" in run_ts
    assert "killGroup" not in run_ts
    assert 'from "./kill.ts"' in statechart_ts
    assert "janitor.ts" in statechart_ts


def test_antigravity_rules_single_source_of_truth(tmp_path: Path) -> None:
    expected = package_projection.generate_antigravity_rules()
    assert "levereable" not in expected
    assert "verifiable proofs" in expected

    staging_src = inspect.getsource(package_install_staging)
    prover_src = inspect.getsource(prove_antigravity_native_package)
    assert "generate_antigravity_rules()" in staging_src
    assert "stage_antigravity_package" in prover_src
    assert "levereable" not in staging_src
    assert "levereable" not in prover_src

    staged = package_install_staging.stage_antigravity_package(tmp_path)
    assert (staged / "rules" / "AGENTS.md").read_text(encoding="utf-8") == expected


def test_canonical_index_and_classification_include_01548() -> None:
    decision = canonical_index.classify_drift_entry("skills/reframe/SKILL.md", "A")
    assert decision["mode"] == "preserve"

    table = (
        ROOT / "skills" / "swarm" / "references" / "classification.tsv"
    ).read_text(encoding="utf-8")
    assert "# tip=ca782ed8b3c2c521cead8e1720d55c3a5dbf2347" in table
    assert "skills/reframe/SKILL.md\tA\tport" in table
    assert "skills/statechart/scripts/janitor.ts\tA\tport" in table
