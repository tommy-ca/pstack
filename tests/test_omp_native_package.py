"""Native OMP package proof: the real binary must enroll what the install writes.

The skill gate is a control/treatment delta (see the lever's docstring), because
an isolated PI_CONFIG_DIR still shares the ambient skill and agent directories.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEVER = ROOT / "scripts" / "prove-omp-native-package.py"

pytestmark = pytest.mark.skipif(shutil.which("omp") is None, reason="omp binary not on PATH")


def run_lever(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(LEVER), "--json", *args],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.stdout.strip(), proc.stderr
    return json.loads(proc.stdout)


def test_the_install_is_listed_and_its_skills_tree_loads() -> None:
    report = run_lever()
    assert report["verdict"] == "PASS", report
    assert report["enrolled"] is True
    assert f"skill:{report['probe_skill']}" in report["contributed_skills"]
    assert report["displaced_ambient_skills"], "the package's skills must win the ambient name collisions"
    assert report["effective_root_inside_disposable"] is True
    assert report["ambient_unchanged"] is True


@pytest.mark.skipif(
    os.environ.get("PSTACK_RUN_OMP_LIVE") != "1",
    reason="needs a model route; set PSTACK_RUN_OMP_LIVE=1",
)
def test_the_live_arm_resolves_a_packaged_agent() -> None:
    report = run_lever("--live")
    assert report["verdict"] == "PASS", report
    agent = report["agent"]
    assert agent["ambient_defines_it"] is False
    assert agent["resolved"] is True
    assert agent["sources"] == ["user"]
    assert agent["settled"] is True


def test_a_root_plugin_json_package_is_not_enrolled(tmp_path: Path) -> None:
    """Negative control: the pre-#290 projection shape contributes nothing."""
    package = tmp_path / "legacy"
    skill = package / "skills" / "legacy-probe" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: legacy-probe\ndescription: legacy probe\n---\n", encoding="utf-8")
    (package / "plugin.json").write_text(
        json.dumps(
            {
                "name": "pstack",
                "version": "0.0.1",
                "skills_root": "./skills/",
                "entrypoint": "skills/poteto-mode/SKILL.md",
            }
        ),
        encoding="utf-8",
    )

    report = run_lever("--package-dir", str(package))

    assert report["verdict"] == "FAIL", report
    assert report["enrolled"] is False
    assert f"skill:{report['probe_skill']}" not in report["contributed_skills"]
