"""Drive absorbed.py. A stale pin or a missing intent line fails. The current tree passes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".grok" / "skills" / "verify-pstack" / "scripts" / "absorbed.py"
INTENT_FILES = (
    "docs/guide/07-overnight.md",
    "skills/show-me-your-work/scripts/log.sh",
    "skills/poteto-mode/scripts/check-plan.mjs",
    "skills/principle-outcome-oriented-execution/SKILL.md",
    "skills/interrogate/references/reviewer-prompt.md",
    "skills/poteto-mode/SKILL.md",
    "skills/poteto-mode/references/grok-tools.md",
    "plugin.json",
)


def _run(root: Path, extra: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--root", str(root), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_intent(dest: Path, pin: str) -> None:
    for rel in INTENT_FILES:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
    (dest / "UPSTREAM").write_text(
        f"tree {pin}\n93b00b89ef425a9c1bac0d0b317dfc49c930ac99\n",
        encoding="utf-8",
    )


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return proc.stdout.strip()


def test_stale_commits_file_fails(tmp_path: Path) -> None:
    commits = tmp_path / "commits.txt"
    commits.write_text("12d587d touch pstack\n", encoding="utf-8")
    proc = _run(ROOT, ["--commits-file", str(commits)])
    assert proc.returncode != 0
    assert "pstack commits after pin" in proc.stdout
    assert "12d587d touch pstack" in proc.stdout


def test_missing_overnight_sentence_fails(tmp_path: Path) -> None:
    root = tmp_path / "root"
    pin = "4b4d98e5e3b3c139f63dbc1ce4b538954c8f2f52"
    _copy_intent(root, pin)
    overnight = root / "docs/guide/07-overnight.md"
    overnight.write_text(
        overnight.read_text(encoding="utf-8").replace(
            "starts a round at the owner", "checks every merge-ready head"
        ),
        encoding="utf-8",
    )
    commits = tmp_path / "empty.txt"
    commits.write_text("", encoding="utf-8")
    proc = _run(root, ["--commits-file", str(commits)])
    assert proc.returncode != 0
    assert "missing docs/guide/07-overnight.md: starts a round at the owner" in proc.stdout
    assert "pstack commits after pin" not in proc.stdout


def test_current_tree_passes(tmp_path: Path) -> None:
    commits = tmp_path / "empty.txt"
    commits.write_text("\n", encoding="utf-8")
    proc = _run(ROOT, ["--commits-file", str(commits)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "PASS absorbed-intent"


def test_cache_commit_after_pin_fails(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    _git(cache, "init", "-b", "main")
    _git(cache, "config", "user.email", "absorbed@example.com")
    _git(cache, "config", "user.name", "absorbed")
    note = cache / "pstack" / "note.txt"
    note.parent.mkdir()
    note.write_text("one\n", encoding="utf-8")
    _git(cache, "add", "pstack/note.txt")
    _git(cache, "commit", "-m", "pin")
    pin = _git(cache, "rev-parse", "HEAD")
    root = tmp_path / "root"
    _copy_intent(root, pin)
    note.write_text("two\n", encoding="utf-8")
    _git(cache, "add", "pstack/note.txt")
    _git(cache, "commit", "-m", "after")
    proc = _run(root, ["--cache", str(cache)])
    assert proc.returncode != 0
    assert "pstack commits after pin" in proc.stdout


def test_cache_at_pin_passes(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    _git(cache, "init", "-b", "main")
    _git(cache, "config", "user.email", "absorbed@example.com")
    _git(cache, "config", "user.name", "absorbed")
    note = cache / "pstack" / "note.txt"
    note.parent.mkdir()
    note.write_text("one\n", encoding="utf-8")
    _git(cache, "add", "pstack/note.txt")
    _git(cache, "commit", "-m", "pin")
    pin = _git(cache, "rev-parse", "HEAD")
    outside = cache / "other.txt"
    outside.write_text("no\n", encoding="utf-8")
    _git(cache, "add", "other.txt")
    _git(cache, "commit", "-m", "outside pstack")
    root = tmp_path / "root"
    _copy_intent(root, pin)
    proc = _run(root, ["--cache", str(cache)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "PASS absorbed-intent"
