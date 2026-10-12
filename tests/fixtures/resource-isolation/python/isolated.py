#!/usr/bin/env python3
"""Isolated verification fixture: per-process port and private state root.

Each worker binds port 0 and keeps the socket (atomic allocation, no
scan-then-bind), works under its own ``mkdtemp`` root, publishes a ready marker,
waits for the peer's marker before touching the peer, and then closes the
listener and removes its root.

``CI_FIXTURE_STATE`` / ``CI_FIXTURE_PORT`` are never read here; the shared
rendezvous directory the peers meet in comes from ``CI_FIXTURE_RENDEZVOUS``.
Contrast with ``collide.py``; driven by ``tests/test_ci_resource_isolation.py``.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
import time
from pathlib import Path

WAIT_DEFAULT = 15.0
WAIT_MIN = 0.05
WAIT_MAX = 60.0


def wait_seconds() -> float:
    try:
        value = float(os.environ.get("CI_FIXTURE_WAIT", WAIT_DEFAULT))
    except ValueError:
        value = WAIT_DEFAULT
    return min(max(value, WAIT_MIN), WAIT_MAX)


def wait_json(path: Path, deadline: float) -> dict:
    while time.monotonic() < deadline:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            time.sleep(0.01)
    raise TimeoutError(f"peer marker {path.name} never appeared within the bounded wait")


def connect(port: int) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=5):
        pass


def main() -> int:
    worker = sys.argv[1] if len(sys.argv) > 1 else "a"
    peer = "b" if worker == "a" else "a"
    rendezvous = Path(os.environ["CI_FIXTURE_RENDEZVOUS"])
    rendezvous.mkdir(parents=True, exist_ok=True)

    temp_root = Path(tempfile.mkdtemp(prefix=f"ci-fixture-{worker}-"))
    private_state = temp_root / "state"
    private_state.mkdir()
    (private_state / "worker.json").write_text(json.dumps({"worker": worker}), encoding="utf-8")

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    deadline = time.monotonic() + wait_seconds()
    events = ["allocated"]
    code = 0
    failure = ""
    peer_port = 0
    try:
        (rendezvous / f"{worker}.ready").write_text(
            json.dumps(
                {
                    "worker": worker,
                    "port": port,
                    "temp_root": str(temp_root),
                    "pid": os.getpid(),
                }
            ),
            encoding="utf-8",
        )
        events.append("published")
        ready = wait_json(rendezvous / f"{peer}.ready", deadline)
        peer_port = ready["port"]
        events.append("observed-ready")
        # Peer step: only after the peer's readiness has been observed.
        connect(peer_port)
        events.append("connected-peer")
        (rendezvous / f"{worker}.observed").write_text(
            json.dumps({"worker": worker, "port": port}), encoding="utf-8"
        )
        wait_json(rendezvous / f"{peer}.observed", deadline)
        events.append("peer-observed-us")
    except TimeoutError as exc:
        code, failure = 3, f"ISOLATION-TIMEOUT worker={worker} {exc}"
    except OSError as exc:
        code, failure = 2, f"ISOLATION-PEER worker={worker} peer={peer} errno={exc.errno} {exc.strerror}"
    finally:
        listener.close()
        shutil.rmtree(temp_root, ignore_errors=True)
        (rendezvous / f"{worker}.done").write_text(
            json.dumps({"worker": worker, "code": code}), encoding="utf-8"
        )

    if code:
        print(failure, file=sys.stderr)
        return code
    print(
        json.dumps(
            {
                "fixture": "isolated",
                "worker": worker,
                "port": port,
                "temp_root": str(temp_root),
                "peer_port": peer_port,
                "events": events,
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
