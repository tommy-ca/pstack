#!/usr/bin/env python3
"""Arena harness for the #495 index-repair shape (pstack, trunk 163a4e1).

Read-only with respect to the repo: every copy lives under /tmp/arena-495.

    python3 arena495.py setup   <ARM>   [--overlay DIR]   # pristine copy + overlay + stash
    python3 arena495.py battery <ARM>                     # probe battery -> battery.{json,txt}
    python3 arena495.py pytest  <ARM>   [-- -k EXPR]      # durability suite in the arm copy
    python3 arena495.py diffstat <ARM>                    # changed lines vs trunk
    python3 arena495.py table                             # every arm that has a battery.json

Probes mutate only `.audit/evidence/index.json` and `<host>-receipt.json`, and every
probe starts by restoring those bytes from `<ARM>/stash`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ARENA = Path("/tmp/arena-495")
SRC = Path("/home/tommyk/projects/pstack")
TMP = Path("/var/tmp/arena-495-tmp")
VENV_PY = SRC / ".venv" / "bin" / "python"
PY = str(VENV_PY) if VENV_PY.exists() else sys.executable
VERIFIER = "scripts/verify-portable.py"
EVIDENCE = Path(".audit/evidence")
INDEX = EVIDENCE / "index.json"
HOSTS = ["grok", "codex", "omp", "opencode", "antigravity"]
IGNORE = shutil.ignore_patterns(
    ".git", ".worktrees", ".venv", "__pycache__", "node_modules", ".pytest_cache",
)
STASH_GLOBS = ["index.json", "*-receipt.json"]

MARKERS = [
    "STALE/REBUILD-REQUIRED",
    "cannot be read as a usable receipt",
    "cannot be read:",
    "unreadable",
    "disagrees with",
    "REFUSING",
    "invalid",
    "Traceback",
]


# ---------------------------------------------------------------- arm plumbing

def arm_dir(arm: str) -> Path:
    return ARENA / "candidates" / arm.upper()


def repo(arm: str) -> Path:
    return arm_dir(arm) / "repo"


def sha(path: Path) -> str:
    if not path.exists():
        return "<missing>"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def setup(arm: str) -> None:
    ad = arm_dir(arm)
    ad.mkdir(parents=True, exist_ok=True)
    (ad / "files").mkdir(exist_ok=True)
    target = repo(arm)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SRC, target, ignore=IGNORE, symlinks=True)
    overlay = ad / "files"
    copied = []
    for path in sorted(overlay.rglob("*")):
        if path.is_file():
            rel = path.relative_to(overlay)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            copied.append(str(rel))
    stash = ad / "stash"
    if stash.exists():
        shutil.rmtree(stash)
    stash.mkdir()
    for pattern in STASH_GLOBS:
        for path in sorted((target / EVIDENCE).glob(pattern)):
            if path.is_file():
                shutil.copy2(path, stash / path.name)
    print(f"[{arm}] setup: copy at {target} ({len(copied)} overlay files: {', '.join(copied) or 'none'})")
    print(f"[{arm}] stash: {len(list(stash.iterdir()))} evidence files")


def reset(arm: str) -> None:
    ad = arm_dir(arm)
    target = repo(arm)
    ev = target / EVIDENCE
    for path in list(ev.glob("*-receipt.json")) + [ev / "index.json"]:
        if path.is_symlink() or path.exists():
            path.unlink()
    os.chmod(ev, 0o755)
    for path in sorted((ad / "stash").iterdir()):
        dest = ev / path.name
        shutil.copy2(path, dest)
        os.chmod(dest, 0o644)


def run(cmd: List[str], cwd: Path, timeout: int = 300) -> Dict[str, Any]:
    started = time.time()
    TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(TMP))
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        return {
            "cmd": " ".join(cmd),
            "exit": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timeout": False,
            "seconds": round(time.time() - started, 1),
        }
    except subprocess.TimeoutExpired as err:
        out = err.stdout.decode() if isinstance(err.stdout, bytes) else (err.stdout or "")
        return {
            "cmd": " ".join(cmd),
            "exit": None,
            "stdout": out,
            "stderr": "TIMEOUT",
            "timeout": True,
            "seconds": round(time.time() - started, 1),
        }


def check(arm: str, args: List[str], timeout: int = 300) -> Dict[str, Any]:
    return run([PY, VERIFIER, *args], cwd=repo(arm), timeout=timeout)


def markers(text: str) -> List[str]:
    return [m for m in MARKERS if m in text]


def reason(text: str) -> str:
    """The first line that looks like a verdict, used for loop comparison."""
    for line in text.splitlines():
        if any(m in line for m in MARKERS) or "FAIL" in line:
            return line.strip()
    return text.strip().splitlines()[-1].strip() if text.strip() else ""


def index_state(arm: str) -> Dict[str, Any]:
    path = repo(arm) / INDEX
    try:
        exists = path.exists()
    except OSError:
        return {"state": "stat-denied", "rows": [], "sha": "<denied>"}
    if not exists:
        return {"state": "missing", "rows": [], "sha": "<missing>"}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        return {"state": f"unreadable:{type(err).__name__}", "rows": [], "sha": "<denied>"}
    digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
    try:
        data = json.loads(raw)
    except Exception:
        return {"state": "unparseable", "rows": [], "sha": digest}
    if not isinstance(data, dict) or not isinstance(data.get("hosts", {}), dict):
        return {"state": f"wrong-shape:{type(data).__name__}", "rows": [], "sha": digest}
    return {"state": "ok", "rows": sorted(data["hosts"].keys()), "sha": digest}


def receipt_shas(arm: str) -> str:
    ev = repo(arm) / EVIDENCE
    try:
        parts = [f"{p.name}:{sha(p)}" for p in sorted(ev.glob("*-receipt.json"))]
    except OSError as err:
        return f"<denied:{type(err).__name__}>"
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def load_index(arm: str) -> Dict[str, Any]:
    return json.loads((repo(arm) / INDEX).read_text(encoding="utf-8"))


def save_index(arm: str, data: Any) -> None:
    (repo(arm) / INDEX).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mutate(arm: str, kind: str) -> str:
    target = repo(arm)
    ev = target / EVIDENCE
    if kind == "none":
        return "none"
    if kind.startswith("drop_row:"):
        host = kind.split(":", 1)[1]
        data = load_index(arm)
        data["hosts"].pop(host, None)
        save_index(arm, data)
        return f"index row for {host} deleted"
    if kind == "index_list":
        (target / INDEX).write_text("[]\n", encoding="utf-8")
        return "index.json = []"
    if kind == "index_garbage":
        (target / INDEX).write_text("{not json\n", encoding="utf-8")
        return "index.json = unparseable"
    if kind == "index_deleted":
        (target / INDEX).unlink()
        return "index.json removed"
    if kind == "index_denied":
        os.chmod(ev / "index.json", 0o000)
        return "index.json chmod 000"
    if kind == "index_readonly":
        os.chmod(ev / "index.json", 0o444)
        return "index.json chmod 444"
    if kind == "index_dir_denied":
        os.chmod(ev, 0o000)
        return ".audit/evidence chmod 000"
    if kind.startswith("corrupt_receipt:"):
        host = kind.split(":", 1)[1]
        (ev / f"{host}-receipt.json").write_text("{not json\n", encoding="utf-8")
        return f"{host}-receipt.json = unparseable"
    if kind.startswith("shape_receipt:"):
        host = kind.split(":", 1)[1]
        (ev / f"{host}-receipt.json").write_text('{"run_id": "x"}\n', encoding="utf-8")
        return f'{host}-receipt.json = {{"run_id": "x"}} (valid JSON, not a receipt)'
    if kind.startswith("drop_receipt:"):
        host = kind.split(":", 1)[1]
        (ev / f"{host}-receipt.json").unlink()
        return f"{host}-receipt.json removed"
    raise SystemExit(f"unknown mutation {kind}")


PROBES: List[Dict[str, Any]] = [
    {"name": "baseline_all", "mutate": "none", "args": ["check-evidence", "--host", "all"]},
    {"name": "orphan_row", "mutate": "drop_row:grok", "args": ["check-evidence", "--host", "grok"], "remedy": True},
    {"name": "orphan_corrupt_bytes", "mutate": "corrupt_receipt:codex", "args": ["check-evidence", "--host", "codex"], "remedy": True},
    {"name": "orphan_unusable_shape", "mutate": "shape_receipt:codex", "args": ["check-evidence", "--host", "codex"], "remedy": True},
    {"name": "row_without_receipt", "mutate": "drop_receipt:grok", "args": ["check-evidence", "--host", "grok"], "remedy": True},
    {"name": "index_list", "mutate": "index_list", "args": ["check-evidence", "--host", "grok"], "remedy": True},
    {"name": "index_garbage", "mutate": "index_garbage", "args": ["check-evidence", "--host", "grok"], "remedy": True},
    {"name": "index_deleted", "mutate": "index_deleted", "args": ["check-evidence", "--host", "grok"], "remedy": True},
    {"name": "index_denied", "mutate": "index_denied", "args": ["check-evidence", "--host", "grok"]},
    {"name": "index_readonly_orphan", "mutate": "index_readonly", "args": ["check-evidence", "--host", "grok"], "remedy": True, "also_drop": "grok"},
    {"name": "evidence_dir_denied", "mutate": "index_dir_denied", "args": ["check-evidence", "--host", "grok"]},
    {"name": "droid_no_receipt", "mutate": "none", "args": ["check-evidence", "--host", "droid"]},
]

PRESCRIPTION = re.compile(
    r"(?:python3\s+)?(?:\S*/)?verify-portable\.py\s+(?:refresh-static|rebuild-index|repair-index)"
    r"(?:\s+--host\s+[A-Za-z0-9_.-]+)?"
)


def probe(arm: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    reset(arm)
    detail = ""
    if spec.get("also_drop"):
        detail += mutate(arm, f"drop_row:{spec['also_drop']}") + "; "
    detail += mutate(arm, spec["mutate"])
    before = index_state(arm)
    receipts_before = receipt_shas(arm)
    result = check(arm, spec["args"], timeout=300)
    after = index_state(arm)
    receipts_after = receipt_shas(arm)
    rec: Dict[str, Any] = {
        "name": spec["name"],
        "setup": detail,
        "args": spec["args"],
        "exit": result["exit"],
        "timeout": result["timeout"],
        "seconds": result["seconds"],
        "markers": markers(result["stdout"] + result["stderr"]),
        "reason": reason(result["stdout"] or result["stderr"]),
        "stdout": result["stdout"].strip()[-1500:],
        "stderr": result["stderr"].strip()[-600:],
        "index_before": before,
        "index_after": after,
        "index_written": before["sha"] != after["sha"],
        "receipts_written": receipts_before != receipts_after,
    }
    os.chmod(repo(arm) / EVIDENCE, 0o755)
    for path in list((repo(arm) / EVIDENCE).glob("index.json")):
        if path.exists():
            os.chmod(path, 0o644)
    recheck = None
    if spec.get("remedy"):
        match = PRESCRIPTION.search(result["stdout"])
        rec["prescription"] = match.group(0).strip().rstrip("`.,;:") if match else None
        if rec["prescription"]:
            remedy_args = [PY] + rec["prescription"].split()[1:]
            remedy = run(remedy_args, cwd=repo(arm), timeout=600)
            recheck = check(arm, spec["args"], timeout=300)
            rec["remedy"] = {
                "cmd": remedy["cmd"],
                "exit": remedy["exit"],
                "timeout": remedy["timeout"],
                "reason": reason(remedy["stdout"] or remedy["stderr"]),
                "stderr": remedy["stderr"].strip()[-300:],
            }
            rec["recheck_exit"] = recheck["exit"]
            rec["recheck_reason"] = reason(recheck["stdout"] or recheck["stderr"])
            rec["loop"] = bool(
                recheck["exit"] not in (0, None)
                and rec["recheck_reason"] == rec["reason"]
                and rec["recheck_reason"] != ""
            )
    return rec


def battery(arm: str) -> None:
    ad = arm_dir(arm)
    if not repo(arm).exists():
        raise SystemExit(f"[{arm}] no copy; run setup first")
    records = [probe(arm, spec) for spec in PROBES]
    payload = {"arm": arm, "trunk": SRC.resolve().name, "records": records}
    (ad / "battery.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [f"arm {arm} — battery", ""]
    for rec in records:
        lines.append(
            f"{rec['name']:<22} exit={rec['exit']!s:<5} time={rec['seconds']!s:>6}s "
            f"idx={rec['index_after']['state']:<12} rows={len(rec['index_after']['rows'])} "
            f"idx_written={rec['index_written']!s:<5} receipts_written={rec['receipts_written']!s:<5}"
            f" loop={rec.get('loop')}"
        )
        lines.append(f"    setup: {rec['setup']}")
        lines.append(f"    reason: {rec['reason'][:200]}")
        if rec.get("prescription"):
            lines.append(f"    prescription: {rec['prescription'][:200]}")
        if rec.get("remedy"):
            lines.append(
                f"    remedy exit={rec['remedy']['exit']} recheck_exit={rec.get('recheck_exit')} "
                f"recheck: {rec.get('recheck_reason', '')[:160]}"
            )
        if rec["timeout"]:
            lines.append("    TIMEOUT")
        if rec["stderr"]:
            lines.append(f"    stderr: {rec['stderr'][:200]}")
    report = "\n".join(lines)
    (ad / "battery.txt").write_text(report + "\n", encoding="utf-8")
    print(report)


def pytest_mode(arm: str, extra: List[str]) -> None:
    cmd = [PY, "-m", "pytest", "-q", "-p", "no:randomly", *extra]
    result = run(cmd, cwd=repo(arm), timeout=1800)
    tail = "\n".join(result["stdout"].strip().splitlines()[-40:])
    print(f"[{arm}] exit={result['exit']} {result['seconds']}s\n{tail}\n{result['stderr'][-500:]}")
    (arm_dir(arm) / "pytest.txt").write_text(
        f"cmd: {' '.join(cmd)}\nexit: {result['exit']} ({result['seconds']}s)\n\n{tail}\n",
        encoding="utf-8",
    )


def diffstat(arm: str) -> None:
    ad = arm_dir(arm)
    overlay = ad / "files"
    files = [p for p in sorted(overlay.rglob("*")) if p.is_file()]
    added = removed = 0
    per_file = []
    for path in files:
        rel = path.relative_to(overlay)
        original = SRC / rel
        old = original.read_text(encoding="utf-8").splitlines() if original.exists() else []
        new = path.read_text(encoding="utf-8").splitlines()
        result = subprocess.run(
            ["git", "diff", "--no-index", "--numstat", "--", str(original), str(path)],
            capture_output=True, text=True,
        )
        parts = result.stdout.strip().split("\t")
        a, r = (int(parts[0]), int(parts[1])) if len(parts) >= 2 and parts[0].isdigit() else (len(new), len(old))
        added += a
        removed += r
        per_file.append((str(rel), a, r))
    summary = {
        "arm": arm,
        "files": [{"path": p, "added": a, "removed": r} for p, a, r in per_file],
        "total_added": added,
        "total_removed": removed,
        "total_changed": added + removed,
    }
    (ad / "diffstat.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def table() -> None:
    rows = []
    for ad in sorted((ARENA / "candidates").glob("*")):
        payload_file = ad / "battery.json"
        stat_file = ad / "diffstat.json"
        if not payload_file.exists():
            continue
        payload = json.loads(payload_file.read_text(encoding="utf-8"))
        records = {r["name"]: r for r in payload["records"]}
        orphan = records.get("orphan_row", {})
        orphan_corrupt = records.get("orphan_corrupt_bytes", {})
        writes = [n for n, r in records.items() if r.get("index_written")]
        loops = [n for n, r in records.items() if r.get("loop")]
        timeouts = [n for n, r in records.items() if r.get("timeout")]
        stat = json.loads(stat_file.read_text(encoding="utf-8")) if stat_file.exists() else {}
        rows.append(
            [
                ad.name,
                stat.get("total_changed", "?"),
                orphan.get("exit"),
                "loop" if orphan.get("loop") else "-",
                orphan_corrupt.get("exit"),
                "loop" if orphan_corrupt.get("loop") else "-",
                ",".join(writes) or "-",
                ",".join(loops) or "-",
                ",".join(timeouts) or "-",
                "ok" if not any(r.get("markers") and "Traceback" in r["markers"] for r in payload["records"]) else "TRACEBACK",
            ]
        )
    header = ["arm", "changed", "orphan_exit", "orphan_loop", "corrupt_exit", "corrupt_loop", "read_verb_writes", "loops", "timeouts", "crash"]
    print(" | ".join(header))
    for row in rows:
        print(" | ".join(str(c) for c in row))


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit(__doc__)
    mode, arm = argv[0], argv[1] if len(argv) > 1 else ""
    if mode == "table":
        table()
    elif mode == "setup":
        setup(arm)
    elif mode == "battery":
        battery(arm)
    elif mode == "pytest":
        pytest_mode(arm, argv[2:] or ["tests/test_evidence_durability.py"])
    elif mode == "diffstat":
        diffstat(arm)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
