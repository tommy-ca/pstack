#!/usr/bin/env python3
"""Concurrent-process resource isolation: the fixture pair that keeps the rules honest.

``tests/fixtures/resource-isolation/`` holds two implementations of one tiny
shape in Python and Node: two workers, one exclusive resource (a TCP port and a
state directory) and a ready marker the peer waits on.

- ``<lang>/collide.*`` takes a fixed port and a shared state path from the
  environment, starts work immediately, and loses the race when two runs
  overlap.
- ``<lang>/isolated.*`` allocates its own port atomically, works under a private
  root, waits for the peer's observed ready marker, and tears down awaited.

The colliding pair is the negative control for the isolation rules the
verification-skill authoring text states: if it ever stops failing, those rules
have no sensitivity.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "resource-isolation"
NODE = shutil.which("node")

# The fixtures bound their own waits (CI_FIXTURE_HOLD, CI_FIXTURE_WAIT) below
# this driver bound, so a bug shows up as a fixture exit code, not a killed test.
RUN_TIMEOUT = 30.0
COLLIDE_HOLD = "2.0"
ISOLATED_WAIT = "20.0"

LANGUAGES = [
    "python",
    pytest.param("node", marks=pytest.mark.skipif(NODE is None, reason="node is not on PATH")),
]


def _command(language: str, kind: str, worker: str) -> list[str]:
    if language == "python":
        return [sys.executable, str(FIXTURES / "python" / f"{kind}.py"), worker]
    assert NODE is not None
    return [NODE, str(FIXTURES / "node" / f"{kind}.mjs"), worker]


def _free_port() -> int:
    """A probably-free port for the colliding fixture.

    Scan-then-bind on purpose: this is the anti-pattern the colliding fixture is
    built to demonstrate, and the solo run below catches a port that was not
    actually free.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _spawn(command: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


@contextlib.contextmanager
def _running(commands: list[list[str]], env: dict[str, str]):
    """Run commands concurrently; kill whatever is still alive on any failure."""
    procs = [_spawn(command, env) for command in commands]
    try:
        yield procs
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)


def _wait_all(procs: list[subprocess.Popen[str]], timeout: float = RUN_TIMEOUT) -> list[float]:
    """Poll until every process exits; return each one's finish time."""
    deadline = time.monotonic() + timeout
    finished: list[float | None] = [None] * len(procs)
    while any(stamp is None for stamp in finished):
        for index, proc in enumerate(procs):
            if finished[index] is None and proc.poll() is not None:
                finished[index] = time.monotonic()
        if time.monotonic() > deadline:
            pytest.fail(f"fixtures did not exit within {timeout}s: {[proc.pid for proc in procs]}")
        time.sleep(0.02)
    return [stamp for stamp in finished if stamp is not None]


def _collect(proc: subprocess.Popen[str], label: str) -> tuple[str, str]:
    try:
        return proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail(f"{label} produced no output after exiting")


def _report(proc: subprocess.Popen[str], label: str) -> dict:
    out, err = _collect(proc, label)
    assert proc.returncode == 0, f"{label} exited {proc.returncode}: {err or out}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines, f"{label} printed no report"
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:  # pragma: no cover - fixture contract violation
        pytest.fail(f"{label} did not print a JSON report: {out!r}")


def _assert_no_listener(port: int) -> None:
    with pytest.raises(OSError):
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass


@pytest.mark.parametrize("language", LANGUAGES)
def test_colliding_pair_loses_exactly_one_worker(language: str, tmp_path: Path) -> None:
    state = tmp_path / "shared-state"
    port = _free_port()
    env = {
        **os.environ,
        "CI_FIXTURE_PORT": str(port),
        "CI_FIXTURE_STATE": str(state),
        "CI_FIXTURE_HOLD": "0.1",
    }

    # A single run is not an error: the collision is what the fixture proves.
    solo = subprocess.run(
        _command(language, "collide", "a"),
        capture_output=True,
        text=True,
        env=env,
        timeout=RUN_TIMEOUT,
        check=False,
    )
    assert solo.returncode == 0, solo.stderr or solo.stdout

    env["CI_FIXTURE_HOLD"] = COLLIDE_HOLD
    commands = [_command(language, "collide", worker) for worker in ("a", "b")]
    with _running(commands, env) as (first, second):
        finished = _wait_all([first, second])
        loser_index = 0 if finished[0] < finished[1] else 1
        winner_index = 1 - loser_index
        loser, winner = (first, second)[loser_index], (first, second)[winner_index]
        loser_worker = ("a", "b")[loser_index]

        assert loser.returncode != 0, "the colliding fixture must fail under overlap"
        assert winner.returncode == 0, winner.stderr
        loser_err = _collect(loser, f"colliding {language} loser")[1]
        assert f"COLLISION worker={loser_worker}" in loser_err, loser_err
        assert f"port={port}" in loser_err, loser_err

        # The winner still held the fixed port and the shared fixed state path.
        winner_report = _report(winner, f"colliding {language} winner")
        assert winner_report["port"] == port
        assert (state / f"{loser_worker}.ready").is_file()
        assert (state / "owner").is_file()


@pytest.mark.parametrize("language", LANGUAGES)
def test_isolated_pair_owns_its_resources(language: str, tmp_path: Path) -> None:
    shared_state = tmp_path / "shared-state"
    rendezvous = tmp_path / "rendezvous"
    fixed_port = _free_port()
    env = {
        **os.environ,
        # Both fixed fixtures must stay untouched by the isolated implementation.
        "CI_FIXTURE_PORT": str(fixed_port),
        "CI_FIXTURE_STATE": str(shared_state),
        "CI_FIXTURE_RENDEZVOUS": str(rendezvous),
        "CI_FIXTURE_WAIT": ISOLATED_WAIT,
    }

    commands = [_command(language, "isolated", worker) for worker in ("a", "b")]
    with _running(commands, env) as (first, second):
        _wait_all([first, second])
        reports = {
            "a": _report(first, f"isolated {language} a"),
            "b": _report(second, f"isolated {language} b"),
        }

    ports = {report["port"] for report in reports.values()}
    roots = {report["temp_root"] for report in reports.values()}
    # Atomic allocation: distinct ports and distinct private roots per worker.
    assert len(ports) == 2, ports
    assert len(roots) == 2, roots
    # The decoy env vars above are passed on purpose: the isolated fixtures must
    # ignore them. Whether the kernel later hands the decoy port to a bind(0) is
    # its own business, so that is not asserted here.
    # Observed readiness: each worker connected to the peer port it read.
    assert reports["a"]["peer_port"] == reports["b"]["port"]
    assert reports["b"]["peer_port"] == reports["a"]["port"]
    for worker, report in reports.items():
        assert "observed-ready" in report["events"], report
        assert "connected-peer" in report["events"], report
        # Quiescent teardown: the awaited child removed its private root.
        assert not Path(report["temp_root"]).exists(), f"{worker} left {report['temp_root']}"
        # ... and released the listener it owned.
        _assert_no_listener(report["port"])

    # Global state restoration: the shared fixed path was never written.
    assert not shared_state.exists(), sorted(p.name for p in shared_state.iterdir())
    assert sorted(p.name for p in rendezvous.iterdir()) == [
        "a.done",
        "a.observed",
        "a.ready",
        "b.done",
        "b.observed",
        "b.ready",
    ]
