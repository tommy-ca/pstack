from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVER = ROOT / ".grok" / "skills" / "verify-pstack" / "scripts" / "verify.py"


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


def test_verify_pstack_is_project_local_not_shipped() -> None:
    skill = ROOT / ".grok" / "skills" / "verify-pstack"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "scripts" / "verify.py").is_file()
    assert (skill / "features" / "README.md").is_file()
    assert not (ROOT / "skills" / "verify-pstack").exists()


def test_resolve_root_walks_parents_past_grok_skills() -> None:
    mod = load_lever()
    assert mod.resolve_root(ROOT) == ROOT.resolve()
    cwd = os.getcwd()
    try:
        os.chdir("/tmp")
        found = mod.resolve_root(None)
    finally:
        os.chdir(cwd)
    assert found == ROOT.resolve()
    assert (found / "plugin.json").is_file()


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


def test_verify_pstack_drive_upstream_recipe_operator_path() -> None:
    run_id = f"recipe-{os.getpid()}-{time.time_ns()}"
    evidence = Path(f"/tmp/verify-pstack-evidence-{run_id}")
    try:
        doctor = subprocess.run(
            [
                sys.executable,
                str(LEVER),
                "doctor",
                "--root",
                str(ROOT),
                "--run-id",
                run_id,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert doctor.returncode == 0, doctor.stderr + doctor.stdout
        drive = subprocess.run(
            [
                sys.executable,
                str(LEVER),
                "drive",
                "--root",
                str(ROOT),
                "--feature",
                "upstream-recipe",
                "--run-id",
                run_id,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert drive.returncode == 0, drive.stderr + drive.stdout
        cmd = (evidence / "features" / "upstream-recipe" / "cmd.txt").read_text(
            encoding="utf-8"
        )
        assert "sync-from-upstream.py" in cmd
        assert "--recipe" in cmd
        assert "--log" not in cmd
        stdout = (evidence / "features" / "upstream-recipe" / "stdout.txt").read_text(
            encoding="utf-8"
        )
        for needle in (
            "--pin",
            "--log",
            "adapt-harness.py",
            "verify.py run",
            "Full sweep",
            "leftover-scanner",
            "upstream-pin",
            "upstream-recipe",
            "refresh-hygiene",
            "release-tag",
            "partition.py",
            "apply.py",
            "apply-check",
        ):
            assert needle in stdout, needle
    finally:
        cleanup = subprocess.run(
            [sys.executable, str(LEVER), "cleanup", "--run-id", run_id],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert cleanup.returncode == 0, cleanup.stderr + cleanup.stdout
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
    mod = load_lever()
    folder = ROOT / ".grok" / "skills" / "verify-pstack" / "features"
    stems = tuple(p.stem for p in _feature_files(folder))
    assert mod.FEATURE_IDS == tuple(mod.DRIVERS)
    assert tuple(sorted(mod.FEATURE_IDS)) == stems


def test_verify_pstack_feature_files_have_four_h2s() -> None:
    folder = ROOT / ".grok" / "skills" / "verify-pstack" / "features"
    for path in _feature_files(folder):
        _assert_four_h2s(path, "verify.py")


def test_maps_lock_proven_drive_needles() -> None:
    features = ROOT / ".grok" / "skills" / "verify-pstack" / "features"
    leftover = (features / "leftover-scanner.md").read_text(encoding="utf-8")
    walk = next(
        line for line in leftover.splitlines() if "`leftover-tree-walk`" in line
    )
    assert "skills markdown" not in walk
    assert "`docs/`" in walk
    assert "`.grok/skills/`" in walk
    for suffix in (".md", ".toml", ".json", ".mjs"):
        assert suffix in walk, suffix

    recipe = (features / "upstream-recipe.md").read_text(encoding="utf-8")
    driving, gotchas = recipe.split("## Driving it with verify.py", 1)[1].split(
        "## Gotchas", 1
    )
    for needle in (
        "partition.py",
        "apply.py",
        "apply-check",
        "verify.py run",
        "Full sweep",
        "leftover-scanner",
        "upstream-pin",
        "upstream-recipe",
        "refresh-hygiene",
        "release-tag",
    ):
        assert needle in driving, needle
    assert "--run-id" in gotchas
    assert "verify.py run" in gotchas
    assert "Pytest" in gotchas

    release = (features / "release-tag.md").read_text(encoding="utf-8")
    driving = release.split("## Driving it with verify.py", 1)[1]
    assert "PASS release-tag" in driving
    assert "PASS tests/test_release.py" in driving
    assert "sys.executable" in driving
    assert "features/release-tag/stdout.txt" in driving
    assert "features/release-tag/cmd.txt" in driving
    assert "Evidence argv is `python3 tests/test_release.py`" not in driving


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
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "/verify-pstack" in text
        assert ".grok/skills/verify-pstack/scripts/verify.py" in text
        for feature in (
            "leftover-scanner",
            "upstream-pin",
            "upstream-recipe",
            "refresh-hygiene",
            "release-tag",
        ):
            assert feature in text, (name, feature)
    skill = (ROOT / ".grok" / "skills" / "verify-pstack" / "SKILL.md").read_text(encoding="utf-8")
    assert "Drive it with `.grok/skills/verify-pstack/scripts/verify.py`" in skill
    assert "Drive it with `scripts/verify.py`" not in skill
    assert "Plugin doctor lives at `.grok/skills/verify-pstack/`" in skill
    assert "Do not ship it under `skills/`." in skill
    upstream = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert "sync-from-upstream.py --pin" in upstream
    assert "sync-from-upstream.py --log" in upstream
    assert "verify.py run" in upstream


def test_feature_indexes_name_full_sweep() -> None:
    paths = (
        ROOT / ".grok" / "skills" / "verify-pstack" / "features" / "README.md",
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

