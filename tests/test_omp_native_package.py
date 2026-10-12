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


def test_the_four_owed_negatives_are_observed() -> None:
    """#298's named negatives: nested skill, disable cycle, `omp` key, precedence.

    This test is skipped, never passed, when `omp` is absent: the assertions are
    statements about what the real binary does.
    """
    report = run_lever()
    assert report["verdict"] == "PASS", report
    assert report["negatives_ok"] is True, report["negatives"]

    # 1. A skill below the one-level discovery depth must not be found.
    nested = report["negatives"]["nested_skill"]
    assert nested["discovered"] is False, nested

    # 2. One unmanaged file survives link, disable, re-enable and uninstall.
    sentinel = report["negatives"]["sentinel"]
    assert sentinel["survived_link"] is True, sentinel
    assert sentinel["survived_uninstall"] is True, sentinel

    # 3. Disable hides the package, enable restores exactly what it contributed.
    cycle = report["negatives"]["disable_cycle"]
    assert cycle["enabled_after_disable"] is True, cycle
    assert cycle["probe_hidden_while_disabled"] is True, cycle
    assert cycle["contributes_nothing_while_disabled"] is True, cycle
    assert cycle["sentinel_survived_disable"] is True, cycle
    assert cycle["enabled_after_enable"] is True, cycle
    assert cycle["skills_restored_on_enable"] is True, cycle
    assert cycle["sentinel_survived_enable"] is True, cycle

    # 4. `package.json#omp` gates loading: absent and mis-shaped load nothing, and
    #    the absent key is the sharp case because the package is still listed.
    rows = {row["variant"]: row for row in report["negatives"]["omp_key"]}
    assert rows["missing"]["listed"] is True, "the absent omp key is listed, not rejected"
    for variant in ("missing", "null", "malformed_string"):
        assert rows[variant]["probe_advertised"] is False, rows[variant]
        assert rows[variant]["contributed_skills"] == [], rows[variant]
    assert rows["empty_object"]["probe_advertised"] is True, "key presence is the gate, not its shape"

    # 5. Precedence: same-name links must not both be advertised, and the winner
    #    must be recorded as it actually resolves rather than assumed.
    precedence = report["negatives"]["precedence"]
    assert [row["order"] for row in precedence] == [["user", "project"], ["project", "user"]], precedence
    for row in precedence:
        assert row["entries_for_name"] == 1, row
        assert row["survivor"] is not None, row
        assert row["survivor_is_the_last_link"] is True, row
        assert row["survivor_advertised_outside_the_project"] is True, row
        assert row["effective_plugin_path_inside_disposable"] is True, row


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
