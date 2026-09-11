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
