#!/usr/bin/env python3
"""Fail if enabled grok pstack does not expose pstack:swarm-workers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

NEED = "pstack:swarm-workers"


def load_inspect(path: Path | None) -> dict:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    got = subprocess.run(
        ["grok", "inspect", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if got.returncode != 0:
        print("FAIL plugin-agents grok inspect --json exited non-zero", file=sys.stderr)
        if got.stderr:
            print(got.stderr, file=sys.stderr, end="")
        raise SystemExit(1)
    return json.loads(got.stdout)


def enabled_pstack_paths(data: dict) -> list[str]:
    paths: list[str] = []
    for plugin in data.get("plugins") or []:
        if not isinstance(plugin, dict):
            continue
        if plugin.get("name") != "pstack":
            continue
        if plugin.get("enabled") is not True:
            continue
        path = plugin.get("path")
        if isinstance(path, str) and path:
            paths.append(path)
    return sorted(set(paths))


def agent_names(data: dict) -> list[str]:
    names: list[str] = []
    for agent in data.get("agents") or []:
        if isinstance(agent, dict):
            name = agent.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-json", type=Path)
    args = parser.parse_args()
    try:
        data = load_inspect(args.inspect_json)
    except json.JSONDecodeError:
        print("FAIL plugin-agents inspect JSON is not an object", file=sys.stderr)
        return 1
    names = agent_names(data)
    paths = enabled_pstack_paths(data)
    if NEED in names:
        print(f"PASS plugin-agents {NEED}")
        if paths:
            print("enabled pstack path: " + paths[0])
        return 0
    print(f"FAIL plugin-agents missing {NEED}", file=sys.stderr)
    if paths:
        print("enabled pstack path: " + paths[0], file=sys.stderr)
        print(
            "Install this checkout with grok --sandbox off plugin install <root> --trust",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
