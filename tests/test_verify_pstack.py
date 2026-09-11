from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVER = ROOT / "skills" / "verify-pstack" / "scripts" / "verify.py"


def load_lever():
    spec = importlib.util.spec_from_file_location("verify_pstack_lever", LEVER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_lever_module_loads() -> None:
    mod = load_lever()
    assert hasattr(mod, "main")


def test_doctor_leftover_stdout_has_pass_and_playbooks() -> None:
    proc = subprocess.run(
        [sys.executable, str(LEVER), "doctor", "--root", str(ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "PASS leftover-scanner" in proc.stdout
    run_id = None
    for line in proc.stdout.splitlines():
        if line.startswith("run_id:"):
            run_id = line.split(":", 1)[1].strip()
            break
    assert run_id, proc.stdout
    leftover = Path(
        f"/tmp/verify-pstack-evidence-{run_id}/doctor/leftover-scanner/stdout.txt"
    )
    text = leftover.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "PASS"
    assert "playbooks: 22 named + opening-a-pr" in text
    assert "principles: 23" in text
    assert "plugin.json name: pstack" in text


def test_log_argv_is_refused() -> None:
    proc = subprocess.run(
        [sys.executable, str(LEVER), "doctor", "--root", str(ROOT), "--log"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2, proc.stderr + proc.stdout
    assert "REFUSED: --log is not a verify path" in proc.stderr


def test_apply_skills_argv_is_refused() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(LEVER),
            "doctor",
            "--root",
            str(ROOT),
            "--apply-skills",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2, proc.stderr + proc.stdout
    assert "REFUSED: --apply-skills is not a verify path" in proc.stderr


def test_later_drive_without_leftover_pass_is_refused() -> None:
    run_id = f"struct-nodoc-{os.getpid()}-{time.time_ns()}"
    proc = subprocess.run(
        [
            sys.executable,
            str(LEVER),
            "drive",
            "--root",
            str(ROOT),
            "--feature",
            "upstream-pin",
            "--run-id",
            run_id,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0, proc.stdout
    assert "leftover scanner PASS is required doctor" in proc.stderr
    cleanup = subprocess.run(
        [sys.executable, str(LEVER), "cleanup", "--run-id", run_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert cleanup.returncode == 0, cleanup.stderr + cleanup.stdout
    evidence = Path(f"/tmp/verify-pstack-evidence-{run_id}")
    assert evidence.is_dir(), evidence


FOUR_H2_PREFIX = (
    "Sub-features",
    "How to get to it (user POV)",
)
FOUR_H2_SUFFIX = ("Gotchas",)


def _h2s(path: Path) -> list[str]:
    return [
        line[3:].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]


def _assert_four_h2s(path: Path, harness: str) -> None:
    got = _h2s(path)
    expected = [
        *FOUR_H2_PREFIX,
        f"Driving it with {harness}",
        *FOUR_H2_SUFFIX,
    ]
    assert got == expected, f"{path}: {got!r}"


def _feature_files(folder: Path) -> list[Path]:
    files = sorted(p for p in folder.glob("*.md") if p.name != "README.md")
    assert files, folder
    return files


def test_verify_pstack_feature_ids_include_upstream_recipe() -> None:
    text = (ROOT / "skills" / "verify-pstack" / "scripts" / "verify.py").read_text(
        encoding="utf-8"
    )
    assert '"upstream-recipe"' in text


def test_verify_pstack_feature_files_have_four_h2s() -> None:
    folder = ROOT / "skills" / "verify-pstack" / "features"
    for path in _feature_files(folder):
        _assert_four_h2s(path, "verify.py")


def test_feature_map_example_files_have_four_h2s() -> None:
    folder = (
        ROOT
        / "skills"
        / "create-verification-skill"
        / "references"
        / "feature-map-example"
    )
    for path in _feature_files(folder):
        _assert_four_h2s(path, "control-notes")


def test_live_openspec_specs_do_not_say_21_principles() -> None:
    specs = ROOT / "openspec" / "specs"
    stale = []
    for path in specs.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "21 principle" in text or "principles: 21" in text or "Twenty-one principle" in text:
            stale.append(str(path.relative_to(ROOT)))
    assert stale == [], stale


def test_readme_lists_verify_pstack() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "/verify-pstack" in text
    assert "skills/verify-pstack" in text


def test_feature_indexes_name_full_sweep() -> None:
    paths = (
        ROOT / "skills" / "verify-pstack" / "features" / "README.md",
        ROOT
        / "skills"
        / "create-verification-skill"
        / "references"
        / "feature-map-example"
        / "README.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "## Full sweep" in text, path
        assert "top to bottom" in text, path

