#!/usr/bin/env python3
"""Prove the OMP install is a package the real OMP binary actually loads.

Renders the OMP install into a temp package directory, links it against a
disposable OMP config root, and reads back what OMP discovered: the plugin
manager's own listing and the RPC session's advertised skills. PI_CONFIG_DIR
names a directory under HOME rather than a path, so the root is a
`.pstack-omp-proof-*` dirname this run creates, asserts the link landed inside,
and removes afterwards. That root still shares the ambient `~/.agents` trees, so
the skill gate is a control/treatment delta on a sentinel skill injected into
the temp copy, never the presence of a name the ambient tree already provides.
The listing is reported for the record and is not loadability evidence on its
own: OMP lists a package whose `package.json` lacks the `omp` key, and then
loads nothing from it.

With ``--live`` the lever also spawns one packaged role agent and requires the
lifecycle frame to name that agent from this package.

The ambient OMP root is snapshotted before and after, everything created under
the isolated root is removed with OMP's own uninstall, and a missing binary is
reported as BLOCKED rather than FAIL.

Usage:
    python3 scripts/prove-omp-native-package.py [--package-dir DIR] [--live] [--json]

Exit codes: 0 PASS, 1 FAIL, 2 BLOCKED.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("package_lifecycle", ROOT / "scripts" / "package-lifecycle.py")
assert _spec is not None and _spec.loader is not None
_pl = importlib.util.module_from_spec(_spec)
sys.modules["package_lifecycle"] = _pl
_spec.loader.exec_module(_pl)

from scripts.drivers.omp_rpc import OmpRpcError, OmpRpcSession  # noqa: E402

LIVE_AGENT_PROMPT = (
    'Use the task tool exactly once with the agent "{agent}" and this assignment: '
    "Report the single word CHILD_OK as your findings. Then reply with exactly PARENT_DONE"
)
AMBIENT_PLUGINS = Path.home() / ".omp" / "plugins"
AMBIENT_AGENT_DIRS = (Path.home() / ".omp" / "agent" / "agents", ROOT / ".omp" / "agents")
# PI_CONFIG_DIR names a directory under HOME, not a path: `getBaseConfigRoot()`
# joins it onto the home directory. Passing an absolute path would silently
# create $HOME/<that path>, so the lever passes a dirname and resolves it the
# same way OMP does.
CONFIG_DIRNAME_PREFIX = ".pstack-omp-proof-"


def disposable_config_dirname() -> str:
    return f"{CONFIG_DIRNAME_PREFIX}{secrets.token_hex(4)}"


def config_root_for(dirname: str) -> Path:
    return Path.home() / dirname


def ambient_snapshot() -> Dict[str, Any]:
    lock = AMBIENT_PLUGINS / "omp-plugins.lock.json"
    node_modules = AMBIENT_PLUGINS / "node_modules"
    return {
        "lock": lock.read_text(encoding="utf-8") if lock.is_file() else None,
        "entries": sorted(p.name for p in node_modules.glob("*")) if node_modules.is_dir() else [],
    }


def ambient_defines_agent(name: str) -> bool:
    return any((directory / f"{name}.md").is_file() for directory in AMBIENT_AGENT_DIRS)


def run_omp(omp_bin: str, args: List[str], *, cwd: Path, config_dirname: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [omp_bin, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={**os.environ, "PI_CONFIG_DIR": config_dirname},
    )


def advertised_skills(omp_bin: str, cwd: Path, config_dirname: str, seconds: float = 30.0) -> List[str]:
    session = OmpRpcSession(
        omp_bin=omp_bin,
        cwd=cwd,
        max_seconds=seconds + 15,
        env={"PI_CONFIG_DIR": config_dirname},
    )
    try:
        session.start()
        deadline = time.time() + seconds
        while time.time() < deadline:
            if any(f.get("type") == "available_commands_update" for f in session.frames):
                break
            time.sleep(0.2)
        names = {
            command.get("name", "")
            for frame in session.frames
            if frame.get("type") == "available_commands_update"
            for command in frame.get("commands") or []
        }
        return sorted(n for n in names if n.startswith("skill:"))
    finally:
        session.close()


def inject_probe_skill(package_dir: Path) -> str:
    """Add a uniquely named skill to the temp copy so the delta names this package."""
    name = f"pstack-native-proof-{secrets.token_hex(3)}"
    skill_dir = package_dir / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: sentinel skill proving this package's skills tree is what loads\n---\n\n# Proof probe\n",
        encoding="utf-8",
    )
    return name


def spawn_named_agent(
    omp_bin: str, cwd: Path, package_dir: Path, agent: str, seconds: float = 180.0
) -> Dict[str, Any]:
    """Spawn one named packaged agent and report the lifecycle evidence for it.

    The agent arm runs against the ambient config root because that is where the
    model route lives, and exposes this package with ``-e <dir>``. That root is
    read for discovery and written by OMP itself (logs, agent databases and run
    state live under it), so the link arm above is what proves the disposable
    root, and this arm only claims the spawn.
    """
    session = OmpRpcSession(
        omp_bin=omp_bin,
        cwd=cwd,
        max_seconds=seconds,
        extra_args=["-e", str(package_dir)],
    )
    observation: Dict[str, Any] = {
        "requested": agent,
        "config_root": "ambient (model route)",
        "extension_root": str(package_dir),
        "ambient_defines_it": ambient_defines_agent(agent),
        "lifecycles": [],
        "settled": False,
        "prompt_result": None,
    }
    try:
        session.start()
        session.negotiate()
        session.subscribe_subagents("events")
        admission = session.prompt(LIVE_AGENT_PROMPT.format(agent=agent))
        observation["settled"] = session.wait_settled(prompt_id=admission.get("id"))
        for frame in session.frames:
            if frame.get("type") == "subagent_lifecycle":
                payload = frame.get("payload") or {}
                if not observation["lifecycles"]:
                    observation["payload_keys"] = sorted(payload.keys())
                observation["lifecycles"].append(
                    {
                        "child_id": payload.get("id"),
                        "agent": payload.get("agent"),
                        "agentSource": payload.get("agentSource"),
                        "status": payload.get("status"),
                    }
                )
            elif frame.get("type") == "prompt_result" and frame.get("id") == admission.get("id"):
                observation["prompt_result"] = {
                    "status": frame.get("status"),
                    "sessionSettled": frame.get("sessionSettled"),
                    "error": (frame.get("error") or {}).get("message") if isinstance(frame.get("error"), dict) else frame.get("error"),
                }
    finally:
        session.close()
    started = [item for item in observation["lifecycles"] if item.get("agent") == agent]
    observation["sources"] = sorted({item.get("agentSource") for item in started if item.get("agentSource")})
    # A start alone would also be satisfied by an agent of the same name from
    # anywhere on the discovery path, so the proof needs the extension-root tag
    # and no ambient definition of that name.
    observation["resolved"] = any(
        item.get("status") == "started" and item.get("agentSource") == "user" for item in started
    ) and not observation["ambient_defines_it"]
    return observation


def prove(package_dir: Optional[Path], live: bool, agent: str, keep: bool) -> Dict[str, Any]:
    omp_bin = shutil.which("omp")
    report: Dict[str, Any] = {
        "omp_bin": omp_bin,
        "package_dir": str(package_dir) if package_dir else None,
        "enrolled": False,
        "listed_manifest": None,
        "control_skills": 0,
        "contributed_skills": [],
        "router_skill_advertised": False,
        "agent": None,
        "ambient_unchanged": None,
        "verdict": "BLOCKED",
        "reason": "omp binary not found on PATH",
    }
    if omp_bin is None:
        return report

    before = ambient_snapshot()
    temp_root = Path(tempfile.mkdtemp(prefix="pstack-omp-proof-"))
    config_dirname = disposable_config_dirname()
    config_root = config_root_for(config_dirname)
    if config_root.exists():
        raise OSError(f"disposable config root already exists: {config_root}")
    work_dir = temp_root / "work"
    work_dir.mkdir(parents=True)
    try:
        target = temp_root / "package"
        if package_dir is None:
            package_dir = _pl.install_plugin("omp", target_base=temp_root / "install")
            target = temp_root / "copy"
            shutil.copytree(package_dir, target, symlinks=True)
        else:
            shutil.copytree(package_dir, target, symlinks=True)
        package_name = "pstack"
        manifest_file = target / "package.json"
        if manifest_file.is_file():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            package_name = manifest.get("name", package_name)
            report["package_manifest"] = manifest
        report["package_dir"] = str(target)

        control = advertised_skills(omp_bin, work_dir, config_dirname)
        report["control_skills"] = len(control)

        probe_skill = inject_probe_skill(target)
        report["probe_skill"] = probe_skill

        link = run_omp(omp_bin, ["plugin", "link", str(target)], cwd=work_dir, config_dirname=config_dirname)
        report["link"] = {"exit_code": link.returncode, "stdout": link.stdout.strip()[:300]}

        listing = run_omp(omp_bin, ["plugin", "list", "--json"], cwd=work_dir, config_dirname=config_dirname)
        try:
            installed = json.loads(listing.stdout)
        except json.JSONDecodeError:
            installed = {}
        for entry in installed.get("npm", []):
            if entry.get("name") == package_name and entry.get("enabled"):
                report["enrolled"] = True
                report["listed_manifest"] = entry.get("manifest")
                report["effective_plugin_path"] = entry.get("path")
                break
        # The link must land in the disposable root this run owns. PI_CONFIG_DIR
        # is a dirname under HOME, so an assertion here is what keeps a future
        # change from writing into the user's own plugin directory.
        effective = report.get("effective_plugin_path") or ""
        report["effective_root_inside_disposable"] = bool(effective) and Path(effective).is_relative_to(config_root)
        if report["enrolled"] and not report["effective_root_inside_disposable"]:
            raise OSError(
                f"effective plugin path {effective!r} is not inside the disposable root {config_root}"
            )

        after = advertised_skills(omp_bin, work_dir, config_dirname)
        report["contributed_skills"] = sorted(set(after) - set(control))
        report["displaced_ambient_skills"] = [
            name for name in report["contributed_skills"] if name.startswith("skill:agents/")
        ]
        report["router_skill_advertised"] = "skill:poteto-mode" in after

        if live:
            report["agent"] = spawn_named_agent(omp_bin, work_dir, target, agent)

        run_omp(omp_bin, ["plugin", "uninstall", package_name], cwd=work_dir, config_dirname=config_dirname)
        report["ambient_unchanged"] = ambient_snapshot() == before

        skills_proved = f"skill:{probe_skill}" in report["contributed_skills"]
        passed = (
            report["enrolled"]
            and skills_proved
            and report["effective_root_inside_disposable"] is True
            and report["ambient_unchanged"] is True
            and (not live or bool((report["agent"] or {}).get("resolved")))
        )
        report["verdict"] = "PASS" if passed else "FAIL"
        report["reason"] = (
            f"listed={report['enrolled']} (listing alone is not loadability), "
            f"this package contributed {report['contributed_skills']}, "
            f"effective root inside the disposable root={report['effective_root_inside_disposable']}, "
            f"ambient root unchanged={report['ambient_unchanged']}"
            + (f", packaged agent resolved={bool((report['agent'] or {}).get('resolved'))}" if live else "")
        )
    except (OmpRpcError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        report["verdict"] = "BLOCKED"
        report["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        if not keep:
            shutil.rmtree(temp_root, ignore_errors=True)
            shutil.rmtree(config_root, ignore_errors=True)
        else:
            report["temp_root"] = str(temp_root)
            report["config_root"] = str(config_root)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, help="Copy and inspect a prepared package instead of installing one")
    parser.add_argument("--live", action="store_true", help="Also spawn one packaged role agent (needs a model route)")
    parser.add_argument("--agent", default="independent-verifier", help="Packaged agent name the live arm spawns")
    parser.add_argument("--keep", action="store_true", help="Keep the isolated root for inspection")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON")
    args = parser.parse_args()

    report = prove(args.package_dir, args.live, args.agent, args.keep)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"OMP native package proof: {report['verdict']}")
        for key in (
            "package_dir",
            "enrolled",
            "effective_root_inside_disposable",
            "listed_manifest",
            "control_skills",
            "contributed_skills",
            "router_skill_advertised",
            "ambient_unchanged",
            "reason",
        ):
            print(f"  {key}: {report.get(key)}")
        if report.get("agent"):
            print(f"  agent: {json.dumps(report['agent'])}")

    sys.exit(0 if report["verdict"] == "PASS" else (1 if report["verdict"] == "FAIL" else 2))


if __name__ == "__main__":
    main()
