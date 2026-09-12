#!/usr/bin/env python3
"""Drive pstack plugin verification. Leftover scanner is required doctor."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

FEATURE_IDS = (
    "leftover-scanner",
    "upstream-pin",
    "upstream-recipe",
    "refresh-hygiene",
    "release-tag",
)
NEED_DOCTOR = frozenset(FEATURE_IDS) - {"leftover-scanner"}
TSV_HEADER = "kind\taction\tpath\tnote"
PIN_RE = re.compile(r"^tree ([0-9a-f]{40})$", re.M)
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LIVE_SKILLS = Path.home() / ".grok" / "skills"
LIVE_REFLECT = LIVE_SKILLS / "reflect" / "SKILL.md"
TIMEOUT_S = 120
HYGIENE_TIMEOUT_S = 180


@dataclass(frozen=True)
class Paths:
    root: Path
    run_id: str
    evidence: Path
    scratch: Path


@dataclass(frozen=True)
class Capture:
    cmd: tuple[str, ...]
    cwd: Path
    stdout: str
    stderr: str
    returncode: int
    out_dir: Path


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def refuse(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(2)


def looks_like_plugin(root: Path) -> bool:
    plugin = root / "plugin.json"
    scanner = root / "scripts" / "verify-harness.py"
    if not plugin.is_file() or not scanner.is_file():
        return False
    try:
        name = json.loads(plugin.read_text(encoding="utf-8")).get("name")
    except (OSError, json.JSONDecodeError, UnicodeError):
        return False
    return name == "pstack"


def resolve_root(explicit: Path | None) -> Path:
    if explicit is not None:
        root = explicit.expanduser().resolve()
        if not looks_like_plugin(root):
            fail(f"not a pstack plugin checkout: {root}")
        return root
    here = Path(__file__).resolve()
    for parent in here.parents:
        if looks_like_plugin(parent):
            return parent
    cwd = Path.cwd()
    if looks_like_plugin(cwd):
        return cwd
    fail("pass --root to the pstack plugin checkout")


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id) or len(run_id) > 80:
        refuse(f"invalid run-id: {run_id!r}")
    return run_id


def new_run_id() -> str:
    env = os.environ.get("VERIFY_PSTACK_RUN_ID", "").strip()
    if env:
        return validate_run_id(env)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{stamp}-{secrets.token_hex(3)}"


def make_paths(root: Path, run_id: str) -> Paths:
    run_id = validate_run_id(run_id)
    evidence = Path(f"/tmp/verify-pstack-evidence-{run_id}")
    scratch = Path(f"/tmp/verify-pstack-scratch-{run_id}")
    if evidence.resolve() == scratch.resolve():
        refuse("evidence and scratch resolve to the same path")
    evidence.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    return Paths(root=root, run_id=run_id, evidence=evidence, scratch=scratch)


def banned_argv(argv: Sequence[str]) -> str | None:
    joined = " ".join(argv)
    if "--apply-skills" in argv:
        return "--apply-skills is not a verify path"
    if "--apply" in argv:
        return "--apply is not a verify path"
    if "--log" in argv:
        return "--log is not a verify path"
    if "release.sh" in joined:
        return "do not run scripts/release.sh from verify"
    if "mise use -g" in joined or (len(argv) >= 3 and "mise" in argv and "use" in argv and "-g" in argv):
        return "do not run mise use -g"
    seq = iter(argv)
    if "git" in seq and "worktree" in seq and "remove" in seq:
        return "do not git worktree remove"
    return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fingerprint(path: Path) -> tuple[int, int, int, bool] | None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    return (st.st_ino, st.st_mtime_ns, st.st_size, stat.S_ISLNK(st.st_mode))


def follow_fingerprint(path: Path) -> list[int] | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return [st.st_ino, st.st_mtime_ns, st.st_size]


def live_skills_snapshot() -> dict[str, object]:
    lstat = fingerprint(LIVE_REFLECT)
    return {
        "skills_exists": LIVE_SKILLS.exists() or LIVE_SKILLS.is_symlink(),
        "skills_is_symlink": LIVE_SKILLS.is_symlink(),
        "reflect_is_symlink": LIVE_REFLECT.is_symlink(),
        "reflect_lstat": None if lstat is None else list(lstat),
        "reflect_stat": follow_fingerprint(LIVE_REFLECT),
    }


def assert_live_skills_unchanged(before: Mapping[str, object]) -> None:
    after = live_skills_snapshot()
    if after != before:
        fail("live ~/.grok/skills/reflect changed during verify")


def assert_tmp_skills(skills: Path) -> None:
    resolved = skills.expanduser().resolve()
    live = LIVE_SKILLS.expanduser()
    try:
        live_res = live.resolve()
    except OSError:
        live_res = live
    if resolved == live_res or live_res in resolved.parents:
        refuse("skills dest is live ~/.grok/skills")
    if not str(resolved).startswith("/tmp/"):
        refuse("skills dest must be under /tmp/")


def capture(
    cmd: Sequence[str],
    *,
    cwd: Path,
    out_dir: Path,
    timeout: int = TIMEOUT_S,
    extra_env: Mapping[str, str] | None = None,
) -> Capture:
    banned = banned_argv(cmd)
    if banned:
        refuse(banned)
    if any(part.endswith("release.sh") for part in cmd):
        refuse("do not run scripts/release.sh from verify")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text(out_dir / "cmd.txt", shlex.join(cmd) + "\n")
    write_text(out_dir / "cwd.txt", str(cwd) + "\n")
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        write_text(out_dir / "stdout.txt", "")
        write_text(out_dir / "stderr.txt", str(exc) + "\n")
        write_text(out_dir / "exit.txt", "127\n")
        fail(f"missing executable: {cmd[0]}")
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        write_text(out_dir / "stdout.txt", stdout)
        write_text(out_dir / "stderr.txt", stderr + "\ntimeout\n")
        write_text(out_dir / "exit.txt", "124\n")
        fail(f"timeout: {shlex.join(cmd)}")
    write_text(out_dir / "stdout.txt", proc.stdout)
    write_text(out_dir / "stderr.txt", proc.stderr)
    write_text(out_dir / "exit.txt", f"{proc.returncode}\n")
    return Capture(
        cmd=tuple(cmd),
        cwd=cwd,
        stdout=proc.stdout,
        stderr=proc.stderr,
        returncode=proc.returncode,
        out_dir=out_dir,
    )


def load_run(paths: Paths) -> dict[str, object]:
    loc = paths.evidence / "run.json"
    if not loc.is_file():
        return {
            "run_id": paths.run_id,
            "root": str(paths.root),
            "evidence": str(paths.evidence),
            "scratch": str(paths.scratch),
            "doctor": {},
            "features": {},
        }
    try:
        data = json.loads(loc.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "run_id": paths.run_id,
            "root": str(paths.root),
            "evidence": str(paths.evidence),
            "scratch": str(paths.scratch),
            "doctor": {},
            "features": {},
        }
    if not isinstance(data, dict):
        fail("run.json is not an object")
    return data


def save_run(paths: Paths, data: dict[str, object]) -> None:
    data["run_id"] = paths.run_id
    data["root"] = str(paths.root)
    data["evidence"] = str(paths.evidence)
    data["scratch"] = str(paths.scratch)
    write_text(paths.evidence / "run.json", json.dumps(data, indent=2) + "\n")


def leftover_pass(text: str) -> bool:
    lines = [ln.rstrip() for ln in text.splitlines()]
    return (
        bool(lines)
        and lines[0] == "PASS"
        and "playbooks: 22 named + opening-a-pr" in text
        and "principles: 23" in text
        and "plugin.json name: pstack" in text
    )


def doctor_already_passed(paths: Paths) -> bool:
    stdout = paths.evidence / "doctor" / "leftover-scanner" / "stdout.txt"
    exit_file = paths.evidence / "doctor" / "leftover-scanner" / "exit.txt"
    if not stdout.is_file() or not exit_file.is_file():
        return False
    if exit_file.read_text(encoding="utf-8").strip() != "0":
        return False
    return leftover_pass(stdout.read_text(encoding="utf-8"))


def require_doctor(paths: Paths) -> None:
    if not doctor_already_passed(paths):
        fail("leftover scanner PASS is required doctor; run verify.py doctor first")
    workflows = paths.root / ".grok" / "workflows"
    if workflows.exists():
        fail("plugin repo must not contain .grok/workflows")


def cmd_leftover_scanner(paths: Paths, out_dir: Path) -> Capture:
    script = paths.root / "scripts" / "verify-harness.py"
    got = capture(
        [sys.executable, str(script)],
        cwd=paths.root,
        out_dir=out_dir,
    )
    if got.returncode != 0 or not leftover_pass(got.stdout):
        fail("leftover scanner did not print PASS and exit 0")
    return got


def cmd_plugin_validate(paths: Paths, out_dir: Path) -> Capture:
    got = capture(
        ["grok", "plugin", "validate", str(paths.root)],
        cwd=paths.root,
        out_dir=out_dir,
    )
    if got.returncode != 0 or "Plugin manifest is valid." not in got.stdout:
        fail("grok plugin validate did not report a valid manifest")
    return got


def run_doctor(paths: Paths) -> None:
    workflows = paths.root / ".grok" / "workflows"
    if workflows.exists():
        fail("plugin repo must not contain .grok/workflows")
    data = load_run(paths)
    leftover = cmd_leftover_scanner(paths, paths.evidence / "doctor" / "leftover-scanner")
    validate = cmd_plugin_validate(paths, paths.evidence / "doctor" / "plugin-validate")
    doctor = {
        "leftover_scanner": {
            "exit": leftover.returncode,
            "pass": True,
            "evidence": str(leftover.out_dir),
        },
        "plugin_validate": {
            "exit": validate.returncode,
            "pass": True,
            "evidence": str(validate.out_dir),
        },
    }
    data["doctor"] = doctor
    save_run(paths, data)
    print("PASS leftover-scanner")
    print("PASS plugin-validate")


def drive_leftover_scanner(paths: Paths) -> None:
    got = cmd_leftover_scanner(paths, paths.evidence / "features" / "leftover-scanner")
    data = load_run(paths)
    features = dict(data.get("features") or {})
    features["leftover-scanner"] = {
        "exit": got.returncode,
        "pass": True,
        "evidence": str(got.out_dir),
    }
    data["features"] = features
    save_run(paths, data)
    print("PASS leftover-scanner")


def drive_upstream_pin(paths: Paths) -> None:
    script = paths.root / "scripts" / "sync-from-upstream.py"
    got = capture(
        [sys.executable, str(script), "--pin"],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "upstream-pin",
    )
    sha = got.stdout.strip()
    if got.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail("sync-from-upstream.py --pin did not print a 40-hex SHA")
    upstream = (paths.root / "UPSTREAM").read_text(encoding="utf-8")
    match = PIN_RE.search(upstream)
    if match is None or match.group(1) != sha:
        fail("pin SHA does not match UPSTREAM tree line")
    data = load_run(paths)
    features = dict(data.get("features") or {})
    features["upstream-pin"] = {
        "exit": got.returncode,
        "sha": sha,
        "evidence": str(got.out_dir),
    }
    data["features"] = features
    save_run(paths, data)
    print(f"PASS upstream-pin {sha}")


def drive_upstream_recipe(paths: Paths) -> None:
    script = paths.root / "scripts" / "sync-from-upstream.py"
    got = capture(
        [sys.executable, str(script), "--recipe"],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "upstream-recipe",
    )
    if got.returncode != 0:
        fail("sync-from-upstream.py --recipe failed")
    if "--log" in got.cmd:
        fail("recipe drive must not pass --log")
    text = got.stdout
    for needle in (
        "sync-from-upstream.py --pin",
        "sync-from-upstream.py --log",
        "adapt-harness.py",
        "verify.py run",
        "verify-harness.py",
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
        if needle not in text:
            fail(f"recipe stdout missing {needle}")
    if "verify-harness.py && python3 tests/test_verify_harness.py" in text:
        fail("recipe step 5 must not use pytest as leftover doctor")
    data = load_run(paths)
    features = dict(data.get("features") or {})
    features["upstream-recipe"] = {
        "exit": got.returncode,
        "evidence": str(got.out_dir),
    }
    data["features"] = features
    save_run(paths, data)
    print("PASS upstream-recipe")


def host_dest(line: str) -> Path:
    first = line.splitlines()[0] if line.strip() else ""
    try:
        toks = shlex.split(first)
    except ValueError:
        fail("host-script stdout is not a cp command")
    if len(toks) != 4 or toks[0] != "cp" or toks[1] != "--":
        fail("host-script stdout must start with cp -- ")
    return Path(toks[3])


def drive_refresh_hygiene(paths: Paths) -> None:
    before = live_skills_snapshot()
    skills = paths.scratch / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    assert_tmp_skills(skills)
    dest = skills / "reflect" / "SKILL.md"
    script = paths.root / "skills" / "swarm" / "scripts" / "refresh-hygiene.py"
    packaged = paths.root / "skills" / "swarm" / "scripts" / "verify-refresh-hygiene.py"
    dry = capture(
        [sys.executable, str(script), "--root", str(paths.root), "--skills", str(skills)],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "refresh-hygiene" / "dry-run",
    )
    if dry.returncode not in (0, 2):
        fail(f"hygiene dry-run exited {dry.returncode}")
    if not dry.stdout.startswith(TSV_HEADER):
        fail("hygiene dry-run stdout missing TSV header")
    host = capture(
        [
            sys.executable,
            str(script),
            "--root",
            str(paths.root),
            "--skills",
            str(skills),
            "--host-script",
        ],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "refresh-hygiene" / "host-script",
    )
    if host.returncode != 0:
        fail(f"hygiene --host-script exited {host.returncode}")
    if not host.stdout.startswith("cp -- "):
        fail("hygiene --host-script stdout must start with cp -- ")
    dest_path = host_dest(host.stdout)
    assert_tmp_skills(dest_path.parent.parent)
    if "/.grok/skills/" in str(dest_path):
        fail("host-script dest is live ~/.grok/skills")
    if dest_path.exists() or dest.exists():
        fail("host-script wrote dest")
    lever = capture(
        [sys.executable, str(packaged)],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "refresh-hygiene" / "packaged-lever",
        timeout=HYGIENE_TIMEOUT_S,
    )
    if lever.returncode != 0:
        fail("verify-refresh-hygiene.py failed")
    assert_live_skills_unchanged(before)
    data = load_run(paths)
    features = dict(data.get("features") or {})
    features["refresh-hygiene"] = {
        "dry_run_exit": dry.returncode,
        "host_script_exit": host.returncode,
        "packaged_exit": lever.returncode,
        "host_dest": str(dest_path),
        "evidence": str(paths.evidence / "features" / "refresh-hygiene"),
    }
    data["features"] = features
    save_run(paths, data)
    print("PASS refresh-hygiene")


def drive_release_tag(paths: Paths) -> None:
    test = paths.root / "tests" / "test_release.py"
    got = capture(
        [sys.executable, str(test)],
        cwd=paths.root,
        out_dir=paths.evidence / "features" / "release-tag",
    )
    if got.returncode != 0 or "PASS tests/test_release.py" not in got.stdout:
        fail("tests/test_release.py did not PASS")
    if "release.sh" in " ".join(got.cmd):
        refuse("do not run scripts/release.sh from verify")
    data = load_run(paths)
    features = dict(data.get("features") or {})
    features["release-tag"] = {
        "exit": got.returncode,
        "pass": True,
        "evidence": str(got.out_dir),
    }
    data["features"] = features
    save_run(paths, data)
    print("PASS release-tag")


DRIVERS: dict[str, Callable[[Paths], None]] = {
    "leftover-scanner": drive_leftover_scanner,
    "upstream-pin": drive_upstream_pin,
    "upstream-recipe": drive_upstream_recipe,
    "refresh-hygiene": drive_refresh_hygiene,
    "release-tag": drive_release_tag,
}


def run_drive(paths: Paths, feature: str | None) -> None:
    names = FEATURE_IDS if feature is None else (feature,)
    if feature is None or any(name in NEED_DOCTOR for name in names):
        require_doctor(paths)
    for name in names:
        driver = DRIVERS[name]
        driver(paths)


def run_cleanup(paths: Paths) -> None:
    evidence = paths.evidence
    scratch = paths.scratch
    if scratch.exists():
        if evidence.resolve() == scratch.resolve():
            refuse("refusing to delete evidence")
        if evidence.resolve() in scratch.resolve().parents:
            refuse("refusing to delete a path that contains evidence")
        if str(scratch.resolve()) == str(LIVE_SKILLS.resolve()):
            refuse("refusing to delete ~/.grok/skills")
        shutil.rmtree(scratch)
    if not evidence.is_dir():
        fail(f"evidence missing after cleanup: {evidence}")
    leftover = evidence / "doctor" / "leftover-scanner" / "stdout.txt"
    if leftover.is_file() and leftover_pass(leftover.read_text(encoding="utf-8")):
        print(f"evidence leftover-scanner PASS kept at {leftover}")
    print(f"PASS cleanup evidence kept at {evidence}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    banned = banned_argv(argv)
    if banned:
        refuse(banned)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument(
        "--feature",
        choices=FEATURE_IDS,
        help="drive one mapped feature; omit to drive all",
    )
    parser.add_argument(
        "command",
        choices=("doctor", "drive", "cleanup", "run"),
        help="doctor is leftover scanner plus grok plugin validate",
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = resolve_root(args.root)
    run_id = validate_run_id(args.run_id) if args.run_id else new_run_id()
    paths = make_paths(root, run_id)
    print(f"run_id: {paths.run_id}", flush=True)
    print(f"evidence: {paths.evidence}", flush=True)
    print(f"scratch: {paths.scratch}", flush=True)
    if args.command == "doctor":
        run_doctor(paths)
    elif args.command == "drive":
        run_drive(paths, args.feature)
    elif args.command == "cleanup":
        run_cleanup(paths)
    elif args.command == "run":
        run_doctor(paths)
        run_drive(paths, args.feature)
        run_cleanup(paths)
    else:
        fail(f"unknown command {args.command}")
    print("PASS")
    print(f"evidence: {paths.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
