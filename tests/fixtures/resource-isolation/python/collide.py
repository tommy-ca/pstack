#!/usr/bin/env python3
"""Colliding verification fixture: fixed port, shared state path, no barrier.

Two concurrent invocations take both resources from the environment
(``CI_FIXTURE_PORT``, ``CI_FIXTURE_STATE``) and start work immediately, so the
second process loses the port bind and exits non-zero while the first is still
holding the resource and polluting the shared state directory.

Driven by ``tests/test_ci_resource_isolation.py`` as the negative control for
``isolated.py``: if this pair ever stops failing, the isolation rules the test
claims to prove have no sensitivity.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path

HOLD_DEFAULT = 2.0
HOLD_MIN = 0.05
HOLD_MAX = 10.0


def hold_seconds() -> float:
    try:
        value = float(os.environ.get("CI_FIXTURE_HOLD", HOLD_DEFAULT))
    except ValueError:
        value = HOLD_DEFAULT
    return min(max(value, HOLD_MIN), HOLD_MAX)


def main() -> int:
    worker = sys.argv[1] if len(sys.argv) > 1 else "a"
    port = int(os.environ["CI_FIXTURE_PORT"])
    state = Path(os.environ["CI_FIXTURE_STATE"])

    # Shared predictable path: every worker writes the same directory and the
    # same `owner` file, so concurrent runs clobber each other's state.
    state.mkdir(parents=True, exist_ok=True)
    (state / "owner").write_text(worker, encoding="utf-8")
    (state / f"{worker}.ready").write_text(
        json.dumps({"worker": worker, "port": port, "pid": os.getpid()}),
        encoding="utf-8",
    )

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind(("127.0.0.1", port))
    except OSError as exc:
        print(
            f"COLLISION worker={worker} port={port} errno={exc.errno} {exc.strerror}",
            file=sys.stderr,
        )
        return 1
    listener.listen(1)
    print(
        json.dumps({"fixture": "collide", "worker": worker, "port": port, "pid": os.getpid()}),
        flush=True,
    )

    # Bounded dwell: the claim is held long enough for a concurrent peer to
    # collide, and the process cannot hang if that peer never arrives.
    deadline = time.monotonic() + hold_seconds()
    while time.monotonic() < deadline:
        time.sleep(0.02)
    listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
