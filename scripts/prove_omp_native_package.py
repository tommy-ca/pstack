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

Four negatives are recorded in the same run, because a positive arm does not
satisfy any of them and each is a named acceptance item of #298: a skill nested
below OMP's one-level discovery depth is not discovered; `omp plugin disable`
stops the package being advertised and `enable` restores it, with one unmanaged
sentinel file surviving link, disable, re-enable and uninstall; manifests whose
`omp` key is absent, null or mis-shaped load nothing (the absent key is still
listed and contributes nothing, which is the false positive this proof exists to
catch); and same-name user-scope and project-scope links are recorded as they
behave, since on omp 18.9.0 `--scope project` still writes into the config
root's `plugins/node_modules`, so the second link of the same name replaces the
first. The rows are recorded, not assumed: a change here is a change in what the
real binary does.

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
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers.omp_rpc import OmpRpcError, OmpRpcSession  # noqa: E402
from scripts.package_lifecycle import install_plugin  # noqa: E402

LIVE_AGENT_PROMPT = (
    'Use the task tool exactly once with the agent "{agent}" and this assignment: '
    "Report the single word CHILD_OK as your findings. Then reply with exactly PARENT_DONE"
)


def get_effective_home() -> Path:
    """Resolve the effective HOME, honoring fixture isolation env vars (#728)."""
    val = os.environ.get("PSTACK_FIXTURE_HOME") or os.environ.get("HOME")
    if val:
        return Path(val).resolve()
    return Path.home().resolve()


AMBIENT_PLUGINS = Path.home() / ".omp" / "plugins"
AMBIENT_AGENT_DIRS: Tuple[Path, ...] = (Path.home() / ".omp" / "agent" / "agents", ROOT / ".omp" / "agents")


def ambient_plugins() -> Path:
    if os.environ.get("PSTACK_FIXTURE_HOME"):
        return get_effective_home() / ".omp" / "plugins"
    return AMBIENT_PLUGINS


def ambient_agent_dirs() -> Tuple[Path, ...]:
    if os.environ.get("PSTACK_FIXTURE_HOME"):
        return (get_effective_home() / ".omp" / "agent" / "agents", ROOT / ".omp" / "agents")
    facade = sys.modules.get("p8_prove_omp_native_package") or sys.modules.get("prove_omp_native_package")
    if facade and hasattr(facade, "AMBIENT_AGENT_DIRS") and facade.AMBIENT_AGENT_DIRS != AMBIENT_AGENT_DIRS:
        return getattr(facade, "AMBIENT_AGENT_DIRS")
    return AMBIENT_AGENT_DIRS


# PI_CONFIG_DIR names a directory under HOME, not a path: `getBaseConfigRoot()`
# joins it onto the home directory. Passing an absolute path would silently
# create $HOME/<that path>, so the lever passes a dirname and resolves it the
# same way OMP does.
CONFIG_DIRNAME_PREFIX = ".pstack-omp-proof-"


def disposable_config_dirname() -> str:
    return f"{CONFIG_DIRNAME_PREFIX}{secrets.token_hex(4)}"


def config_root_for(dirname: str) -> Path:
    return get_effective_home() / dirname


def ambient_snapshot() -> Dict[str, Any]:
    plugins = ambient_plugins()
    lock = plugins / "omp-plugins.lock.json"
    node_modules = plugins / "node_modules"
    return {
        "lock": lock.read_text(encoding="utf-8") if lock.is_file() else None,
        "entries": sorted(p.name for p in node_modules.glob("*")) if node_modules.is_dir() else [],
    }


def ambient_defines_agent(name: str) -> bool:
    return any((directory / f"{name}.md").is_file() for directory in ambient_agent_dirs())


def plugin_entry(
    omp_bin: str, cwd: Path, config_dirname: str, package_name: str
) -> Optional[Dict[str, Any]]:
    """The plugin manager's own record for one package, or None when it lists nothing."""
    listing = run_omp(omp_bin, ["plugin", "list", "--json"], cwd=cwd, config_dirname=config_dirname)
    try:
        installed = json.loads(listing.stdout)
    except json.JSONDecodeError:
        return None
    for entry in installed.get("npm", []):
        if entry.get("name") == package_name:
            return entry
    return None


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
        env={"PI_CONFIG_DIR": config_dirname, "HOME": str(get_effective_home())},
    )
    try:
        session.start()
        deadline = time.time() + seconds
        last_frame_count = 0
        settle_start: Optional[float] = None
        while time.time() < deadline:
            update_frames = [f for f in session.frames if f.get("type") == "available_commands_update"]
            if update_frames:
                if len(update_frames) != last_frame_count:
                    last_frame_count = len(update_frames)
                    settle_start = time.time()
                elif settle_start is not None and (time.time() - settle_start >= 0.5):
                    # Settled: commands stabilized for at least 500ms (#728)
                    break
            time.sleep(0.05)
        names = {
            command.get("name", "")
            for frame in session.frames
            if frame.get("type") == "available_commands_update"
            for command in frame.get("commands") or []
        }
        return sorted(n for n in names if n.startswith("skill:"))
    finally:
        session.close()


def inject_probe_skill(package_dir: Path, label: str = "native") -> str:
    """Add a uniquely named skill to the temp copy so the delta names this package."""
    name = f"pstack-{label}-proof-{secrets.token_hex(3)}"
    skill_dir = package_dir / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: sentinel skill proving this package's skills tree is what loads\n---\n\n# Proof probe\n",
        encoding="utf-8",
    )
    return name


def inject_nested_skill(package_dir: Path) -> str:
    """Add a skill below the discovery depth, where OMP must not find it."""
    name = f"pstack-nested-proof-{secrets.token_hex(3)}"
    skill_dir = package_dir / "skills" / "nested-outer" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: nested skill that one-level discovery must not reach\n---\n\n# Nested probe\n",
        encoding="utf-8",
    )
    return name


SENTINEL_TEXT = "unmanaged file: link, disable, re-enable and uninstall must all leave it alone\n"


def unmanaged_sentinel(package_dir: Path) -> Path:
    """Place one file the package does not own where every lifecycle operation can see it."""
    sentinel = package_dir / "UNMANAGED-SENTINEL.txt"
    sentinel.write_text(SENTINEL_TEXT, encoding="utf-8")
    return sentinel


def sentinel_survived(sentinel: Path) -> bool:
    return sentinel.is_file() and sentinel.read_text(encoding="utf-8") == SENTINEL_TEXT


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


def disable_cycle(
    omp_bin: str,
    work_dir: Path,
    config_dirname: str,
    package_name: str,
    probe_skill: str,
    control: List[str],
    enabled_skills: List[str],
    sentinel: Path,
) -> Dict[str, Any]:
    """`omp plugin disable` must stop the package being advertised and `enable` restore it."""
    observation: Dict[str, Any] = {}
    disabled = run_omp(omp_bin, ["plugin", "disable", package_name], cwd=work_dir, config_dirname=config_dirname)
    observation["disable_exit_code"] = disabled.returncode
    entry = plugin_entry(omp_bin, work_dir, config_dirname, package_name)
    observation["enabled_after_disable"] = entry is not None and entry.get("enabled") is False
    off = advertised_skills(omp_bin, work_dir, config_dirname)
    observation["probe_hidden_while_disabled"] = f"skill:{probe_skill}" not in off
    observation["contributes_nothing_while_disabled"] = sorted(set(off) - set(control)) == []
    observation["sentinel_survived_disable"] = sentinel_survived(sentinel)

    enabled = run_omp(omp_bin, ["plugin", "enable", package_name], cwd=work_dir, config_dirname=config_dirname)
    observation["enable_exit_code"] = enabled.returncode
    entry = plugin_entry(omp_bin, work_dir, config_dirname, package_name)
    observation["enabled_after_enable"] = entry is not None and entry.get("enabled") is True
    back = advertised_skills(omp_bin, work_dir, config_dirname)
    observation["skills_restored_on_enable"] = sorted(set(back) - set(control)) == sorted(
        set(enabled_skills) - set(control)
    )
    observation["sentinel_survived_enable"] = sentinel_survived(sentinel)
    observation["ok"] = observation["disable_exit_code"] == 0 and observation["enable_exit_code"] == 0 and all(
        observation[key]
        for key in (
            "enabled_after_disable",
            "probe_hidden_while_disabled",
            "contributes_nothing_while_disabled",
            "sentinel_survived_disable",
            "enabled_after_enable",
            "skills_restored_on_enable",
            "sentinel_survived_enable",
        )
    )
    return observation


def precedence_matrix(
    omp_bin: str,
    config_dirname: str,
    config_root: Path,
    package_dir: Path,
    temp_root: Path,
    package_name: str,
) -> List[Dict[str, Any]]:
    """Record which scope wins when the same package name is linked at both scopes.

    Each row links one user-scope and one project-scope copy of the same package
    (distinct probe skills) in both orders, then reads the advertised skills from
    inside and from outside the project directory. Only one side may survive: a
    name that resolves to two packages at once is the ambiguity this matrix
    exists to catch. Which side wins, and whether resolution depends on the cwd,
    are recorded rather than assumed.
    """
    project = temp_root / "precedence-project"
    project.mkdir()
    (project / ".git").mkdir()
    outside = temp_root / "precedence-outside"
    outside.mkdir()
    rows: List[Dict[str, Any]] = []
    for order in (("user", "project"), ("project", "user")):
        sides: Dict[str, Dict[str, Any]] = {}
        for side in ("user", "project"):
            copy = temp_root / f"precedence-{'then'.join(order)}-{side}"
            shutil.copytree(package_dir, copy, symlinks=True)
            sides[side] = {"dir": copy, "probe": inject_probe_skill(copy, f"precedence-{side}")}
        codes = [
            run_omp(
                omp_bin,
                ["plugin", "link", str(sides[side]["dir"]), "--scope", side],
                cwd=project,
                config_dirname=config_dirname,
            ).returncode
            for side in order
        ]
        entry = plugin_entry(omp_bin, project, config_dirname, package_name)
        inside = advertised_skills(omp_bin, project, config_dirname)
        advertised = {side: f"skill:{sides[side]['probe']}" in inside for side in ("user", "project")}
        winners = [side for side in ("user", "project") if advertised[side]]
        survivor = winners[0] if len(winners) == 1 else None
        effective = (entry or {}).get("path") or ""
        rows.append(
            {
                "order": list(order),
                "link_exit_codes": codes,
                "entries_for_name": 1 if entry else 0,
                "effective_plugin_path": effective,
                "effective_plugin_path_inside_disposable": bool(effective) and Path(effective).is_relative_to(config_root),
                "user_probe_advertised": advertised["user"],
                "project_probe_advertised": advertised["project"],
                "survivor": survivor,
                "survivor_is_the_last_link": survivor == order[1],
                "survivor_advertised_outside_the_project": (
                    f"skill:{sides[survivor]['probe']}" in advertised_skills(omp_bin, outside, config_dirname)
                    if survivor
                    else False
                ),
                "project_dir_entries": sorted(p.name for p in project.iterdir()),
                "ok": survivor is not None and codes == [0, 0],
            }
        )
        run_omp(omp_bin, ["plugin", "uninstall", package_name], cwd=project, config_dirname=config_dirname)
    return rows


def omp_key_matrix(
    omp_bin: str, work_dir: Path, config_dirname: str, package_dir: Path, temp_root: Path, package_name: str
) -> List[Dict[str, Any]]:
    """`package.json#omp` is the enrollment key: absent or mis-shaped must load nothing.

    `omp plugin list` still lists a package whose manifest has no `omp` key, so the
    listing is recorded next to loadability; the negative is that the listed
    package contributes no skills at all.
    """
    variants: List[Tuple[str, Callable[[Dict[str, Any]], None], bool]] = [
        ("missing", lambda manifest: manifest.pop("omp", None), False),
        ("null", lambda manifest: manifest.update(omp=None), False),
        ("malformed_string", lambda manifest: manifest.update(omp=package_name), False),
        ("empty_object", lambda manifest: manifest.update(omp={}), True),
    ]
    control = advertised_skills(omp_bin, work_dir, config_dirname)
    rows: List[Dict[str, Any]] = []
    for variant, mutate, expected_to_load in variants:
        copy = temp_root / f"omp-key-{variant}"
        shutil.copytree(package_dir, copy, symlinks=True)
        manifest_file = copy / "package.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        mutate(manifest)
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        probe_skill = inject_probe_skill(copy, f"key-{variant}")
        link = run_omp(omp_bin, ["plugin", "link", str(copy)], cwd=work_dir, config_dirname=config_dirname)
        entry = plugin_entry(omp_bin, work_dir, config_dirname, package_name)
        after = advertised_skills(omp_bin, work_dir, config_dirname)
        row: Dict[str, Any] = {
            "variant": variant,
            "link_exit_code": link.returncode,
            "listed": entry is not None,
            "enabled": (entry or {}).get("enabled"),
            "expected_to_load": expected_to_load,
            "probe_advertised": f"skill:{probe_skill}" in after,
            "contributed_skills": sorted(set(after) - set(control)),
        }
        row["ok"] = row["probe_advertised"] == expected_to_load
        rows.append(row)
        run_omp(omp_bin, ["plugin", "uninstall", package_name], cwd=work_dir, config_dirname=config_dirname)
    return rows


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
    ambient_agent = get_effective_home() / ".omp" / "agent"
    agent_dir = config_root / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    for cfg_name in ("models.yml", "config.yml"):
        src = ambient_agent / cfg_name
        if src.is_file():
            shutil.copy(src, agent_dir / cfg_name)
    work_dir = temp_root / "work"
    work_dir.mkdir(parents=True)
    try:
        target = temp_root / "package"
        if package_dir is None:
            package_dir = install_plugin("omp", target_base=temp_root / "install")
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
        nested_probe = inject_nested_skill(target)
        sentinel = unmanaged_sentinel(target)

        link = run_omp(omp_bin, ["plugin", "link", str(target)], cwd=work_dir, config_dirname=config_dirname)
        report["link"] = {"exit_code": link.returncode, "stdout": link.stdout.strip()[:300]}

        entry = plugin_entry(omp_bin, work_dir, config_dirname, package_name)
        if entry is not None and entry.get("enabled"):
            report["enrolled"] = True
            report["listed_manifest"] = entry.get("manifest")
            report["effective_plugin_path"] = entry.get("path")
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

        negatives: Dict[str, Any] = {
            "nested_skill": {"name": nested_probe, "discovered": f"skill:{nested_probe}" in after},
            "sentinel": {"path": str(sentinel), "survived_link": sentinel_survived(sentinel)},
        }
        if report["enrolled"]:
            negatives["disable_cycle"] = disable_cycle(
                omp_bin, work_dir, config_dirname, package_name, probe_skill, control, after, sentinel
            )

        if live:
            report["agent"] = spawn_named_agent(omp_bin, work_dir, target, agent)

        run_omp(omp_bin, ["plugin", "uninstall", package_name], cwd=work_dir, config_dirname=config_dirname)
        negatives["sentinel"]["survived_uninstall"] = sentinel_survived(sentinel)
        if report["enrolled"]:
            negatives["precedence"] = precedence_matrix(
                omp_bin, config_dirname, config_root, package_dir, temp_root, package_name
            )
            negatives["omp_key"] = omp_key_matrix(
                omp_bin, work_dir, config_dirname, package_dir, temp_root, package_name
            )
        report["negatives"] = negatives
        report["ambient_unchanged"] = ambient_snapshot() == before

        skills_proved = f"skill:{probe_skill}" in report["contributed_skills"]
        negatives_ok: Optional[bool] = None
        if report["enrolled"]:
            negatives_ok = (
                negatives["nested_skill"]["discovered"] is False
                and negatives["sentinel"]["survived_link"] is True
                and negatives["sentinel"]["survived_uninstall"] is True
                and negatives["disable_cycle"]["ok"] is True
                and all(row["ok"] for row in negatives["precedence"])
                and all(row["ok"] for row in negatives["omp_key"])
            )
        report["negatives_ok"] = negatives_ok
        passed = (
            report["enrolled"]
            and skills_proved
            and report["effective_root_inside_disposable"] is True
            and report["ambient_unchanged"] is True
            and negatives_ok is not False
            and (not live or bool((report["agent"] or {}).get("resolved")))
        )
        report["verdict"] = "PASS" if passed else "FAIL"
        report["reason"] = (
            f"listed={report['enrolled']} (listing alone is not loadability), "
            f"this package contributed {report['contributed_skills']}, "
            f"effective root inside the disposable root={report['effective_root_inside_disposable']}, "
            f"ambient root unchanged={report['ambient_unchanged']}"
            + (f", negatives ok={negatives_ok}" if negatives_ok is not None else ", negatives not run (no enrolled package)")
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
            "negatives_ok",
            "ambient_unchanged",
            "reason",
        ):
            print(f"  {key}: {report.get(key)}")
        if report.get("agent"):
            print(f"  agent: {json.dumps(report['agent'])}")

    sys.exit(0 if report["verdict"] == "PASS" else (1 if report["verdict"] == "FAIL" else 2))


if __name__ == "__main__":
    main()
