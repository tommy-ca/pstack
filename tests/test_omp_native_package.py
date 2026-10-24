"""Native OMP package proof: the real binary must enroll what the install writes.

The skill gate is a control/treatment delta (see the lever's docstring), because
an isolated PI_CONFIG_DIR still shares the ambient skill and agent directories.

The vertical-slice half (#292) splits deliberately: its offline arm (projection,
manifest shape, uninstall plan, four-plane receipt with a BLOCKED runtime plane)
must run with no binary at all, so it is not behind the binary gate. Only the
rows that speak to the real binary take that gate.
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
SLICE_LEVER = ROOT / "scripts" / "prove-omp-vertical-slice.py"

needs_omp = pytest.mark.skipif(shutil.which("omp") is None, reason="omp binary not on PATH")
needs_live_route = pytest.mark.skipif(
    os.environ.get("PSTACK_RUN_OMP_LIVE") != "1",
    reason="needs a model route; set PSTACK_RUN_OMP_LIVE=1",
)


def run_lever(*args: str, env: dict | None = None) -> dict:
    run_env = {**os.environ} if env is None else env
    proc = subprocess.run(
        [sys.executable, str(LEVER), "--json", *args],
        capture_output=True,
        text=True,
        timeout=300,
        env=run_env,
    )
    assert proc.stdout.strip(), proc.stderr
    return json.loads(proc.stdout)


def run_slice(*args: str, path: str | None = None, timeout: int = 600) -> dict:
    """Run the slice lever. `path` replaces PATH so the no-binary arm is real."""
    env = None if path is None else {**os.environ, "PATH": path}
    proc = subprocess.run(
        [sys.executable, str(SLICE_LEVER), "--json", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    assert proc.stdout.strip(), proc.stderr
    return json.loads(proc.stdout)


@needs_omp
def test_the_install_is_listed_and_its_skills_tree_loads() -> None:
    report = run_lever()
    assert report["verdict"] == "PASS", report
    assert report["enrolled"] is True
    assert f"skill:{report['probe_skill']}" in report["contributed_skills"]
    assert report["displaced_ambient_skills"], "the package's skills must win the ambient name collisions"
    assert report["effective_root_inside_disposable"] is True
    assert report["ambient_unchanged"] is True


@needs_omp
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


@needs_omp
@needs_live_route
def test_the_live_arm_resolves_a_packaged_agent() -> None:
    report = run_lever("--live")
    assert report["verdict"] == "PASS", report
    agent = report["agent"]
    assert agent["ambient_defines_it"] is False
    assert agent["resolved"] is True
    assert agent["sources"] == ["user"]
    assert agent["settled"] is True


@needs_omp
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


# --- vertical slice (#292) --------------------------------------------------

NO_HOST_CLIS = "/usr/bin:/bin"


def tree_hashes(root: Path) -> dict:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_offline_slice_runs_without_a_binary(tmp_path: Path) -> None:
    """Projection, manifest shape, uninstall plan and a BLOCKED runtime plane.

    PATH is stripped of the `omp` install, so this asserts the offline half, not
    a host that happens to have the binary.
    """
    report = run_slice("--out", str(tmp_path), path=NO_HOST_CLIS)

    assert report["omp_bin"] is None, report["omp_bin"]
    assert report["verdict"] == "BLOCKED", report
    assert report["planes"] == {
        "canonical": "PASS",
        "adapter": "PASS",
        "package": "PASS",
        "runtime": "BLOCKED",
    }
    offline = report["offline"]
    assert offline["shape_ok"] is True, offline["shape_errors"]
    assert offline["manifest_ok"] is True
    assert offline["router_matches_canonical"] is True
    assert offline["agent_role_declared"] is True
    assert offline["hardcoded_provider_selector"] is False

    # The uninstall plan names the user files it keeps and the owned paths it removes.
    assert offline["plan"]["preserved"] == ["local/keep.txt", "user-notes.md"], offline["plan"]
    assert "package.json" in offline["plan"]["owned"], offline["plan"]
    assert offline["uninstall_ok"] is True, offline["uninstall_errors"]
    assert offline["sentinels_preserved"] is True
    assert offline["owned_paths_removed"] is True
    assert report["live"] is None

    # The offline receipt exists, carries all four planes, and never claims runtime proof.
    receipt = report["receipt"]
    assert receipt["overall_verdict"] == "BLOCKED"
    assert set(receipt["planes"]) == {"canonical", "adapter", "package", "runtime"}
    assert receipt["surface_revisions"]["spec_hash"] != "missing"
    assert report["exact_head"] in receipt["claim"]
    runtime = [s for s in receipt["scenarios"] if s["plane"] == "runtime"]
    assert [s["verdict"] for s in runtime] == ["BLOCKED"]
    assert [s["evidence_level"] for s in runtime] == ["offline"]
    assert all(s["settlement"] is None for s in receipt["scenarios"])
    assert all(s["evidence_level"] for s in receipt["scenarios"])
    assert (tmp_path / "slice-receipt.json").is_file()


def test_the_slice_leaves_the_receipt_store_untouched(tmp_path: Path) -> None:
    """Acceptance guard: the run writes its receipt to --out, never to .audit."""
    store = ROOT / ".audit"
    before = tree_hashes(store)

    report = run_slice("--out", str(tmp_path), path=NO_HOST_CLIS)

    assert report["receipt_path"] == str(tmp_path / "slice-receipt.json")
    assert tree_hashes(store) == before
    assert "slice-receipt.json" not in before


@needs_omp
@needs_live_route
def test_the_live_slice_resolves_the_role_and_joins_one_child(tmp_path: Path) -> None:
    """One child, one session: link, discovery, role resolution, join, uninstall."""
    report = run_slice("--live", "--out", str(tmp_path))

    assert report["verdict"] == "PASS", report
    assert report["planes"] == {
        "canonical": "PASS",
        "adapter": "PASS",
        "package": "PASS",
        "runtime": "PASS",
    }
    live = report["live"]
    assert live["enrolled"] is True
    assert live["discovery_root_inside_disposable"] is True
    assert live["router_advertised"] is True
    assert live["linked_router_matches_package"] is True
    assert live["uninstalled"] is True
    assert live["source_sentinels_intact"] is True
    assert live["ambient_unchanged"] is True

    # The slice-local binding is the role frontmatter, resolved through the overlay.
    assert live["overlay_roles"] == {"review": report["review_selector"]}
    assert live["binding"]["after"].count('model: "@review"') == 1
    assert live["binding"]["after"] != live["binding"]["before"]

    child = live["child"]
    assert child["settled"] is True
    assert child["protocol_version"] == 2
    assert child["parent_literal"] is True
    assert child["child_token_seen"] is True, "the child's own output was observed"
    settlement = child["settlement"]
    assert settlement["terminal_outcome"] == "success"
    assert settlement["transport"] == "rpc"
    assert settlement["model"] == report["review_selector"]

    runtime = [s for s in report["receipt"]["scenarios"] if s["id"] == "slice-runtime-child-spawn"]
    assert [s["verdict"] for s in runtime] == ["PASS"]
    assert [s["evidence_level"] for s in runtime] == ["observed_live"]
    assert runtime[0]["settlement"]["child_id"] == settlement["child_id"]

    # Read-only stays downgraded to advisory; no write denial was observed.
    assert report["readonly"]["enforcement"] == "advisory"
    assert report["readonly"]["observed_negative_write_probe"] is False
    # One child, one session, inside the bounded runner rather than tail-spinning.


def test_prove_omp_native_package_is_hermetic_against_ambient_home(tmp_path: Path) -> None:
    """#728: probe-omp-native-package resolves paths against fixture HOME without ambient leak."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("prove_omp_pkg", LEVER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    fixture_home = tmp_path / "custom-fixture-home"
    fixture_home.mkdir()
    (fixture_home / ".omp" / "plugins").mkdir(parents=True)
    (fixture_home / ".omp" / "plugins" / "omp-plugins.lock.json").write_text('{"fixture": true}\n', encoding="utf-8")

    os.environ["PSTACK_FIXTURE_HOME"] = str(fixture_home)
    try:
        assert mod.get_effective_home() == fixture_home
        snap = mod.ambient_snapshot()
        assert snap["lock"] == '{"fixture": true}\n'
    finally:
        os.environ.pop("PSTACK_FIXTURE_HOME", None)

