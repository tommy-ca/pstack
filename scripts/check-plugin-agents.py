#!/usr/bin/env python3
"""Fail unless enabled grok pstack is the intended tree with pstack:swarm-workers."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

NEED = "pstack:swarm-workers"
INSTALL = (
    "Install https://github.com/tommy-ca/pstack with grok --sandbox off "
    "plugin install tommy-ca/pstack --trust"
)
OVERLAY = (
    "inspect skills[] collidesWith on a pstack plugin skill. "
    "Remove the overlapping user overlay. "
    "Do not copy plugin skills into ~/.grok/skills."
)

PathKind = Literal[
    "installed-plugins",
    "checkout",
    "marketplace",
    "home-plugins-symlink",
    "other",
]
KIND_FAIL = {
    "marketplace": "FAIL plugin-agents marketplace path",
    "home-plugins-symlink": "FAIL plugin-agents ~/.grok/plugins/pstack bind",
}


def load_inspect(path: Path | None) -> object:
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


def is_marketplace_tree(path: str) -> bool:
    parts = Path(path).expanduser().parts
    if "marketplaces" not in parts:
        return False
    idx = parts.index("marketplaces")
    return "plugins" in parts[idx + 1 :]


def is_home_plugins_bind(path: str) -> bool:
    posix = os.path.normpath(os.path.expanduser(path)).replace("\\", "/")
    if posix.rstrip("/").endswith("/.grok/plugins/pstack"):
        return True
    bind = Path.home() / ".grok" / "plugins" / "pstack"
    return Path(posix) == Path(os.path.normpath(str(bind)))


def classify_path(path: str) -> PathKind:
    if is_marketplace_tree(path):
        return "marketplace"
    if is_home_plugins_bind(path):
        return "home-plugins-symlink"
    parts = Path(path).expanduser().parts
    if "installed-plugins" in parts:
        return "installed-plugins"
    root = Path(path)
    if (root / "plugin.json").is_file() and (root / "agents").is_dir():
        return "checkout"
    return "other"


def plugin_name_of(skill: dict) -> str | None:
    raw = skill.get("plugin_name")
    source = skill.get("source")
    if isinstance(source, dict):
        nested = source.get("plugin_name")
        if isinstance(nested, str) and nested:
            return nested
    if isinstance(raw, str) and raw:
        return raw
    return None


def skill_collides(skill: dict) -> bool:
    collides = skill.get("collidesWith")
    if collides is None:
        collides = skill.get("collides_with")
    return bool(collides)


def pstack_collision_names(data: dict) -> list[str]:
    names: list[str] = []
    for skill in data.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        if not skill_collides(skill):
            continue
        if plugin_name_of(skill) != "pstack":
            continue
        name = skill.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return sorted(set(names))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-json", type=Path)
    args = parser.parse_args()
    try:
        loaded = load_inspect(args.inspect_json)
    except json.JSONDecodeError:
        print("FAIL plugin-agents inspect JSON is not an object", file=sys.stderr)
        return 1
    if not isinstance(loaded, dict):
        print("FAIL plugin-agents inspect JSON is not an object", file=sys.stderr)
        return 1
    data = loaded
    names = agent_names(data)
    paths = enabled_pstack_paths(data)
    if not paths:
        print("FAIL plugin-agents no enabled pstack plugin path", file=sys.stderr)
        return 1

    stderr: list[str] = []
    path_blocked = False
    for path in paths:
        fault = KIND_FAIL.get(classify_path(path))
        if fault is not None:
            stderr.append(fault)
            path_blocked = True

    collisions = pstack_collision_names(data)
    if collisions:
        stderr.append("FAIL plugin-agents collidesWith " + ", ".join(collisions))

    missing_files = [
        path for path in paths if not (Path(path) / "agents" / "swarm-workers.md").is_file()
    ]
    agent_ok = NEED in names and not missing_files
    if not path_blocked and not agent_ok:
        stderr.append(f"FAIL plugin-agents missing {NEED}")

    if stderr:
        seen: list[str] = []
        for line in stderr:
            if line not in seen:
                seen.append(line)
        for line in seen:
            print(line, file=sys.stderr)
        for path in paths:
            print("enabled pstack path: " + path, file=sys.stderr)
        if not path_blocked:
            for path in missing_files:
                print("enabled pstack has no agents/swarm-workers.md", file=sys.stderr)
        if collisions:
            print(OVERLAY, file=sys.stderr)
        if path_blocked or not agent_ok:
            print(INSTALL, file=sys.stderr)
        return 1

    print(f"PASS plugin-agents {NEED}")
    print("enabled pstack path: " + paths[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
