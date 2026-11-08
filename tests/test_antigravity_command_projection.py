"""Tests for Antigravity command and auxiliary projection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.antigravity_command_projection as ag_proj
import scripts.package_projection as pkg_proj
from scripts.portability_schema import PackageDescriptor


@pytest.fixture
def sample_descriptor() -> PackageDescriptor:
    desc, _ = pkg_proj.load_package_descriptor()
    return desc


def test_generate_antigravity_commands(sample_descriptor: PackageDescriptor) -> None:
    cmds = ag_proj.generate_antigravity_commands(sample_descriptor)
    assert len(cmds) >= 21
    assert "poteto-mode.toml" in cmds
    assert "thermos.toml" in cmds
    assert "description = " in cmds["poteto-mode.toml"]
    assert "prompt = " in cmds["poteto-mode.toml"]


def test_project_and_check_commands(tmp_path: Path, sample_descriptor: PackageDescriptor) -> None:
    cmds_dir = tmp_path / "commands"
    count = ag_proj.project_antigravity_commands(sample_descriptor, cmds_dir)
    assert count >= 21
    assert (cmds_dir / "poteto-mode.toml").is_file()
    assert (cmds_dir / "thermos.toml").is_file()

    # In sync check
    assert ag_proj.check_antigravity_commands(sample_descriptor, cmds_dir) is True

    # Drift check
    (cmds_dir / "poteto-mode.toml").write_text("drifted = true\n", encoding="utf-8")
    assert ag_proj.check_antigravity_commands(sample_descriptor, cmds_dir) is False

    # Missing directory check
    missing_dir = tmp_path / "nonexistent"
    assert ag_proj.check_antigravity_commands(sample_descriptor, missing_dir) is False


def test_project_and_check_auxiliary(tmp_path: Path, sample_descriptor: PackageDescriptor) -> None:
    models_file = tmp_path / "models.json"
    models_data = {"testRoleDefault": "pro", "roles": []}

    ag_proj.project_antigravity_auxiliary(sample_descriptor, models_file, models_data)
    assert models_file.is_file()
    assert (tmp_path / "commands" / "poteto-mode.toml").is_file()

    # Pass check
    assert ag_proj.check_antigravity_auxiliary(sample_descriptor, models_file, models_data) is True

    # Drift check
    models_file.write_text(json.dumps({"drift": True}), encoding="utf-8")
    assert ag_proj.check_antigravity_auxiliary(sample_descriptor, models_file, models_data) is False


def test_package_projection_reexport_parity() -> None:
    desc, _ = pkg_proj.load_package_descriptor()
    cmds_direct = ag_proj.generate_antigravity_commands(desc)
    cmds_reexport = pkg_proj.generate_antigravity_commands(desc)
    assert cmds_direct == cmds_reexport
    assert len(cmds_direct) >= 21
