#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_no_openspec_python_wrappers_in_scripts() -> None:
    wrapper_path = ROOT / "scripts" / "openspec_change.py"
    assert not wrapper_path.exists(), "scripts/openspec_change.py must be deleted"

    scripts_dir = ROOT / "scripts"
    for script_file in scripts_dir.glob("*.py"):
        text = script_file.read_text(encoding="utf-8")
        assert "class ChangeResolution" not in text
        assert "def _active_openspec_changes" not in text
        assert "def resolve_openspec_change" not in text


def test_active_change_spec_deltas_align_with_base_specs() -> None:
    changes_dir = ROOT / "openspec" / "changes"
    specs_dir = ROOT / "openspec" / "specs"
    if not changes_dir.exists() or not specs_dir.exists():
        return
    for change_dir in sorted(changes_dir.iterdir()):
        if not change_dir.is_dir():
            continue
        specs_subdir = change_dir / "specs"
        if not specs_subdir.exists():
            continue
        for cap_dir in sorted(specs_subdir.iterdir()):
            delta_file = cap_dir / "spec.md"
            base_file = specs_dir / cap_dir.name / "spec.md"
            if not delta_file.exists() or not base_file.exists():
                continue
            base_content = base_file.read_text(encoding="utf-8")
            base_reqs = {
                line.strip()
                for line in base_content.splitlines()
                if line.strip().startswith("### Requirement:")
            }
            delta_content = delta_file.read_text(encoding="utf-8")
            current_section = None
            for line in delta_content.splitlines():
                stripped = line.strip()
                if stripped.startswith("## "):
                    current_section = stripped
                elif (
                    stripped.startswith("### Requirement:")
                    and current_section == "## ADDED Requirements"
                ):
                    assert stripped not in base_reqs, (
                        f"Requirement '{stripped}' in {delta_file} is listed under "
                        f"'## ADDED Requirements' but already exists in base spec {base_file}."
                    )


def test_direct_bunx_openspec_status_execution() -> None:
    proc = subprocess.run(
        ["bunx", "--yes", "@fission-ai/openspec@1.16.1", "status", "--all"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Change:" in proc.stdout


def test_direct_bunx_openspec_validate_all_execution() -> None:
    proc = subprocess.run(
        ["bunx", "--yes", "@fission-ai/openspec@1.16.1", "validate", "--all"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "passed" in proc.stdout


def test_direct_bunx_openspec_validate_changes_strict_execution() -> None:
    proc = subprocess.run(
        ["bunx", "--yes", "@fission-ai/openspec@1.16.1", "validate", "--changes", "--strict"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "passed" in proc.stdout


def test_direct_bunx_openspec_validate_archived_execution() -> None:
    proc = subprocess.run(
        ["bunx", "--yes", "@fission-ai/openspec@1.16.1", "validate", "--archived"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "passed" in proc.stdout
