#!/usr/bin/env python3
"""Prove one smallest end-to-end OMP vertical slice (#292).

Offline (default, no binary needed): project the pstack package for OMP into a
temp base, verify the manifest and skill/agent shape, compare the projected
`poteto-mode` router against the canonical one, plan the uninstall and run it
while user-authored sentinels stay put, and emit the four-plane receipt with the
runtime plane BLOCKED — no live evidence was observed.

Live (``--live``, or ``PSTACK_RUN_OMP_LIVE=1``): link the temp package into a
disposable OMP config root and read back the advertised skills (only the real
binary can prove `poteto-mode` is discovered from this package), then spawn one
`independent-verifier` child whose frontmatter carries ``model: "@review"``,
resolved through a run-local ``modelRoles.review`` overlay, join it over RPC v2
and reduce the frames to the typed settlement. A missing binary or an
unavailable model route is reported BLOCKED, never PASS.

Read-only is recorded as advisory: OMP exposes no hard read-only task mount and
the role declares ``capabilityMode: execute``, so the slice downgrades the claim
rather than pretending a write denial it never observed.

Usage:
    python3 scripts/prove-omp-vertical-slice.py [--live] [--review-model M] [--out DIR] [--keep] [--json]

Exit codes: 0 PASS, 1 FAIL, 2 BLOCKED.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_module(name: str, rel: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_pl = _load_module("package_lifecycle", "scripts/package-lifecycle.py")
_vp = _load_module("verify_portable", "scripts/verify-portable.py")
# The package lever already owns the disposable-root discovery helpers (link,
# advertised skills, ambient snapshot). Reusing them keeps one definition of how
# the ambient root is isolated instead of two that can drift apart.
_pkg = _load_module("prove_omp_native_package", "scripts/prove-omp-native-package.py")

from scripts.drivers.omp import _assistant_text, _model_route_error  # noqa: E402
from scripts.drivers.omp_rpc import (  # noqa: E402
    OmpRpcError,
    OmpRpcSession,
    reduce_child_settlement,
)
from scripts.portability_schema import (  # noqa: E402
    ScenarioResult,
    VerificationReceipt,
    compute_surface_revisions,
)

LIVE_GATE_ENV = "PSTACK_RUN_OMP_LIVE"
PACKAGE_NAME = "pstack"
ROUTER_SKILL = "poteto-mode"
DEFAULT_AGENT = "independent-verifier"
REVIEW_ROLE = "review"
CONFIG_DIRNAME_PREFIX = ".pstack-omp-slice-"
LIVE_MAX_SECONDS = 240.0
SENTINELS = ("user-notes.md", "local/keep.txt")
OWNED_PROBE_PATHS = ("package.json", f"skills/{ROUTER_SKILL}/SKILL.md")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
PARENT_LITERAL = re.compile(r"PARENT[\s_]*DONE", re.IGNORECASE)
SLICE_PROMPT = (
    'Use the task tool exactly once with the agent "{agent}" and this assignment: '
    "Reply with exactly CHILD_OK as your findings. Then reply with exactly PARENT_DONE"
)
run_omp = _pkg.run_omp
advertised_skills = _pkg.advertised_skills
ambient_snapshot = _pkg.ambient_snapshot
ambient_defines_agent = _pkg.ambient_defines_agent
READ_ONLY = {
    "enforcement": "advisory",
    "observed_negative_write_probe": False,
    "reason": (
        "OMP exposes no hard read-only task mount (profiles/omp.json workspace.readonly is "
        "advisory) and the verifier role declares capabilityMode: execute, so the slice "
        "downgrades read-only instead of claiming a denial it did not observe"
    ),
}


# --- shared -----------------------------------------------------------------


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(root: Path = ROOT, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def omp_version(omp_bin: Optional[str]) -> str:
    if not omp_bin:
        return ""
    try:
        proc = subprocess.run(
            [omp_bin, "--version"], capture_output=True, text=True, check=False, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def role_selectors(text: str, key: str = "modelRoles") -> Dict[str, str]:
    """Read one indentation-delimited role block, so the lever needs no YAML dependency."""
    roles: Dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        if re.match(rf"^{key}:\s*$", line):
            inside = True
            continue
        if not inside:
            continue
        if not line.strip():
            continue
        if not line[:1].isspace():
            break
        match = re.match(r"^\s+([\w.-]+):\s*(\S+)\s*$", line)
        if match:
            roles[match.group(1)] = match.group(2)
    return roles


def ambient_review_selector() -> str:
    """Ambient default for the review role: the user's task/default selector, or ''.

    Only a default, never an override: the run writes its own explicit overlay so
    the user's providers, credentials and model settings stay untouched.
    """
    config = Path.home() / ".omp" / "agent" / "config.yml"
    if not config.is_file():
        return ""
    roles = role_selectors(config.read_text(encoding="utf-8"))
    return roles.get("task") or roles.get("default") or ""


def write_review_overlay(run_dir: Path, selector: str) -> Path:
    path = run_dir / "review-role.yml"
    path.write_text(f"modelRoles:\n  {REVIEW_ROLE}: {selector}\n", encoding="utf-8")
    return path


def bind_review_role(agent_file: Path, role: str = REVIEW_ROLE) -> Dict[str, Any]:
    """Bind the slice's agent copy to a model role.

    The shipped role frontmatter declares no ``model:`` yet, so the binding is
    made on the temp copy: moving the shipped package artifact to prove the
    mechanism would change the package instead of testing it.
    """
    text = agent_file.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if match is None:
        raise OSError(f"agent file has no frontmatter: {agent_file}")
    before = match.group(1)
    if re.search(r"^model:", before, re.M):
        after = re.sub(r"^model:.*$", f'model: "@{role}"', before, flags=re.M)
    else:
        after = f'{before}\nmodel: "@{role}"'
    agent_file.write_text(f"---\n{after}\n---\n{text[match.end():]}", encoding="utf-8")
    return {"role": role, "file": str(agent_file), "before": before, "after": after}


def write_sentinels(plugin_dir: Path) -> List[str]:
    """User-authored files inside the plugin dir the uninstall must not touch."""
    for rel in SENTINELS:
        path = plugin_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"user-authored sentinel: {rel}\n", encoding="utf-8")
    return list(SENTINELS)


def uninstall_plan(plugin_dir: Path) -> Dict[str, Any]:
    record = plugin_dir / ".pstack-managed-files.json"
    owned: List[str] = []
    if record.is_file():
        owned = list(json.loads(record.read_text(encoding="utf-8")).get("managed_files", []))
    return {
        "owned": sorted(owned),
        "preserved": sorted(_pl.get_unmanaged_paths(plugin_dir, set(owned))),
    }


# --- offline half -----------------------------------------------------------


def offline_slice(run_dir: Path, agent: str) -> Dict[str, Any]:
    """Projection, manifest shape and uninstall plan: no binary, no model route."""
    started = time.time()
    base = run_dir / "install"
    plugin_dir = _pl.install_plugin("omp", target_base=base)
    desc, _ = _pl.load_package_descriptor()
    shape_ok, shape_errors = _pl.verify_plugin_at_dir("omp", plugin_dir, desc)
    manifest = json.loads((plugin_dir / "package.json").read_text(encoding="utf-8"))
    manifest_ok = manifest.get("name") == PACKAGE_NAME and isinstance(manifest.get("omp"), dict)

    router = plugin_dir / "skills" / ROUTER_SKILL / "SKILL.md"
    canonical_router = ROOT / "skills" / ROUTER_SKILL / "SKILL.md"
    projected_router_sha = sha256_file(router) if router.is_file() else ""
    router_ok = (
        bool(projected_router_sha)
        and canonical_router.is_file()
        and router.resolve() != canonical_router.resolve()
        and projected_router_sha == sha256_file(canonical_router)
    )

    agent_file = plugin_dir / "agents" / f"{agent}.md"
    frontmatter = ""
    if agent_file.is_file():
        match = FRONTMATTER.match(agent_file.read_text(encoding="utf-8"))
        frontmatter = match.group(1) if match else ""
    declared = {r.get("id"): r.get("default_model_role") for r in desc.roles}
    role_ok = bool(frontmatter) and agent in declared and "capabilityMode:" in frontmatter
    hardcoded_selector = bool(re.search(r"^model:\s*[\w.-]+/", frontmatter, re.M))

    sentinels = write_sentinels(plugin_dir)
    plan = uninstall_plan(plugin_dir)
    uninstall_ok, uninstall_errors = _pl.uninstall_plugin("omp", target_base=base)
    preserved = [rel for rel in sentinels if (plugin_dir / rel).is_file()]
    owned_removed = [rel for rel in OWNED_PROBE_PATHS if not (plugin_dir / rel).exists()]

    return {
        "plugin_dir": str(plugin_dir),
        "duration_s": round(time.time() - started, 3),
        "shape_ok": shape_ok,
        "shape_errors": shape_errors,
        "manifest": manifest,
        "manifest_ok": manifest_ok,
        "router_matches_canonical": router_ok,
        "router_sha256": projected_router_sha,
        "agent_frontmatter": frontmatter,
        "agent_role_declared": role_ok,
        "declared_model_role": declared.get(agent),
        "hardcoded_provider_selector": hardcoded_selector,
        "plan": plan,
        "plan_ok": plan["preserved"] == sorted(SENTINELS) and bool(plan["owned"]),
        "uninstall_ok": uninstall_ok,
        "uninstall_errors": uninstall_errors,
        "sentinels_preserved": preserved == sentinels,
        "owned_paths_removed": owned_removed == list(OWNED_PROBE_PATHS),
    }


# --- live half --------------------------------------------------------------


def run_omp(omp_bin: str, args: List[str], *, cwd: Path, config_dirname: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [omp_bin, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
        env={**os.environ, "PI_CONFIG_DIR": config_dirname},
    )


def advertised_skills(omp_bin: str, cwd: Path, config_dirname: str, seconds: float = 30.0) -> List[str]:
    session = OmpRpcSession(
        omp_bin=omp_bin, cwd=cwd, max_seconds=seconds + 15, env={"PI_CONFIG_DIR": config_dirname}
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


def spawn_slice_child(
    omp_bin: str,
    work_dir: Path,
    package_dir: Path,
    overlay: Path,
    run_dir: Path,
    agent: str,
    seconds: float,
) -> Dict[str, Any]:
    """Spawn one role child over RPC v2 and join it, bounded by the session deadline."""
    result: Dict[str, Any] = {"requested": agent, "settled": False, "settlement": None}
    session = OmpRpcSession(
        omp_bin=omp_bin,
        cwd=work_dir,
        max_seconds=seconds,
        log_path=run_dir / "slice-rpc.jsonl",
        extra_args=["-e", str(package_dir), "--config", str(overlay)],
    )
    frames: List[Dict[str, Any]] = []
    try:
        session.start()
        descriptor = session.negotiate()
        session.subscribe_subagents("events")
        admission = session.prompt(SLICE_PROMPT.format(agent=agent))
        settled = session.wait_settled(prompt_id=admission.get("id"))
        frames = session.frames
    except (OmpRpcError, OSError) as exc:
        result["failure"] = f"{type(exc).__name__}: {exc}"
        return result
    finally:
        result["exit_code"] = session.close()

    lifecycles = []
    for frame in frames:
        if frame.get("type") != "subagent_lifecycle":
            continue
        payload = frame.get("payload") or {}
        lifecycles.append(
            {
                "child_id": payload.get("id"),
                "agent": payload.get("agent"),
                "agentSource": payload.get("agentSource"),
                "status": payload.get("status"),
                "payload_keys": sorted(payload.keys()),
            }
        )
    result.update(
        {
            "settled": settled,
            "protocol_version": descriptor.get("protocol_version"),
            "effective_rpc": descriptor.get("effective_rpc"),
            "route_error": _model_route_error(frames),
            "settlement": reduce_child_settlement(frames, timed_out=not settled),
            "parent_literal": bool(PARENT_LITERAL.search(_assistant_text(frames))),
            "child_token_seen": "CHILD_OK" in json.dumps(frames),
            "lifecycles": lifecycles,
        }
    )
    return result


def live_slice(
    omp_bin: str,
    package_dir: Path,
    run_dir: Path,
    agent: str,
    selector: str,
    seconds: float,
) -> Dict[str, Any]:
    """Link the package into a disposable root, then spawn/join one role child."""
    observation: Dict[str, Any] = {
        "agent": agent,
        "role": REVIEW_ROLE,
        "selector": selector,
        "ambient_defines_agent": ambient_defines_agent(agent),
        "binding": bind_review_role(package_dir / "agents" / f"{agent}.md"),
    }
    overlay = write_review_overlay(run_dir, selector)
    observation["overlay"] = str(overlay)
    observation["overlay_roles"] = role_selectors(overlay.read_text(encoding="utf-8"))

    config_dirname = f"{CONFIG_DIRNAME_PREFIX}{secrets.token_hex(4)}"
    config_root = Path.home() / config_dirname
    if config_root.exists():
        raise OSError(f"disposable config root already exists: {config_root}")
    work_dir = run_dir / "work"
    work_dir.mkdir(parents=True)
    before = ambient_snapshot()
    started = time.time()
    try:
        control = advertised_skills(omp_bin, work_dir, config_dirname)
        link = run_omp(omp_bin, ["plugin", "link", str(package_dir)], cwd=work_dir, config_dirname=config_dirname)
        observation["link"] = {"exit_code": link.returncode, "stdout": link.stdout.strip()[:300]}
        listing = run_omp(omp_bin, ["plugin", "list", "--json"], cwd=work_dir, config_dirname=config_dirname)
        try:
            installed = json.loads(listing.stdout)
        except json.JSONDecodeError:
            installed = {}
        entry = next(
            (
                e
                for e in installed.get("npm", [])
                if e.get("name") == PACKAGE_NAME and e.get("enabled")
            ),
            None,
        )
        observation["enrolled"] = entry is not None
        effective = (entry or {}).get("path") or ""
        observation["effective_plugin_path"] = effective
        # PI_CONFIG_DIR is a dirname under HOME, so an assertion here keeps a future
        # change from writing into the user's own plugin directory.
        observation["discovery_root_inside_disposable"] = bool(effective) and Path(effective).is_relative_to(config_root)

        after = advertised_skills(omp_bin, work_dir, config_dirname)
        observation["router_advertised"] = f"skill:{ROUTER_SKILL}" in after
        # The ambient trees can already provide the router name, so the delta is
        # recorded but never the proof. Attribution comes from the router file
        # inside the enrolled plugin path, byte-compared with this package's copy.
        observation["router_in_ambient_control"] = f"skill:{ROUTER_SKILL}" in control
        observation["router_from_this_package"] = f"skill:{ROUTER_SKILL}" in (set(after) - set(control))
        observation["contributed_skills"] = sorted(set(after) - set(control))[:15]
        package_router = package_dir / "skills" / ROUTER_SKILL / "SKILL.md"
        linked_router = Path(effective) / "skills" / ROUTER_SKILL / "SKILL.md" if effective else None
        observation["linked_router"] = str(linked_router) if linked_router else ""
        observation["linked_router_matches_package"] = bool(
            linked_router
            and linked_router.is_file()
            and package_router.is_file()
            and sha256_file(linked_router) == sha256_file(package_router)
        )

        child_started = time.time()
        observation["child"] = spawn_slice_child(
            omp_bin, work_dir, package_dir, overlay, run_dir, agent, seconds
        )
        observation["child_seconds"] = round(time.time() - child_started, 3)
    finally:
        run_omp(omp_bin, ["plugin", "uninstall", PACKAGE_NAME], cwd=work_dir, config_dirname=config_dirname)
        listed = run_omp(omp_bin, ["plugin", "list", "--json"], cwd=work_dir, config_dirname=config_dirname)
        observation["uninstalled"] = PACKAGE_NAME not in listed.stdout
        observation["source_sentinels_intact"] = all((package_dir / rel).is_file() for rel in SENTINELS)
        observation["ambient_unchanged"] = ambient_snapshot() == before
        observation["session_seconds"] = round(time.time() - started, 3)
        shutil.rmtree(config_root, ignore_errors=True)
    return observation


# --- receipt ----------------------------------------------------------------


def runtime_row(child: Dict[str, Any], selector: str, seconds: float) -> ScenarioResult:
    settlement = child.get("settlement")
    failure = child.get("failure") or ""
    route_error = child.get("route_error") or ""
    unmet: List[str] = []
    if settlement is None:
        unmet.append("no single terminal child lifecycle")
    elif settlement["terminal_outcome"] != "success":
        unmet.append(f"child outcome {settlement['terminal_outcome']}")
    if not child.get("settled"):
        unmet.append("session did not settle after the prompt")
    if child.get("exit_code") not in (0, None):
        unmet.append(f"process exit {child['exit_code']}")
    if child.get("protocol_version") != 2:
        unmet.append(f"negotiated protocol v{child.get('protocol_version')}")
    if not child.get("parent_literal"):
        unmet.append("parent reply did not carry PARENT_DONE")
    role_resolved = bool(settlement) and settlement["model"] == selector
    if settlement and not role_resolved:
        unmet.append(f"child model {settlement['model']!r} != review selector {selector!r}")

    if settlement:
        snippet = (
            f"child={settlement['child_id']} outcome={settlement['terminal_outcome']} "
            f"model={settlement['model']} effective_rpc={settlement['effective_rpc']} "
            f"child_token_seen={bool(child.get('child_token_seen'))}"
        )
    else:
        snippet = "no single terminal child lifecycle observed"

    verdict = "PASS"
    if failure or route_error:
        verdict = "BLOCKED"
        snippet = f"BLOCKED: {failure or route_error} ({snippet})"
    elif unmet:
        verdict = "FAIL"
        snippet = f"{snippet}; unmet: {'; '.join(unmet)}"

    return ScenarioResult(
        id="slice-runtime-child-spawn",
        description=(
            "Live OMP RPC v2 spawn/join of one read-only verifier role whose frontmatter "
            "model role resolved through the run's modelRoles overlay"
        ),
        plane="runtime",
        command=f"omp --mode rpc -e {child.get('requested')} --config review-role.yml (prompt -> 1 task child)",
        exit_code=child["exit_code"] if child.get("exit_code") is not None else 1,
        stdout_snippet=snippet,
        verdict=verdict,
        duration_s=seconds,
        evidence_level="observed_live" if verdict == "PASS" else "offline",
        settlement=settlement,
    )


def slice_scenarios(
    offline: Dict[str, Any], live: Optional[Dict[str, Any]], live_blocked: str, selector: str
) -> List[ScenarioResult]:
    scenario_list = [
        ScenarioResult(
            id="slice-router-canonical",
            description="The projected poteto-mode router is byte-identical to the canonical router skill",
            plane="canonical",
            command=f"sha256(skills/{ROUTER_SKILL}/SKILL.md) in projection == canonical",
            exit_code=0 if offline["router_matches_canonical"] else 1,
            stdout_snippet=(
                f"projected router sha256={offline['router_sha256'][:16]} canonical="
                f"{sha256_file(ROOT / 'skills' / ROUTER_SKILL / 'SKILL.md')[:16]}"
            ),
            verdict="PASS" if offline["router_matches_canonical"] else "FAIL",
            duration_s=0.0,
            evidence_level="offline",
        ),
        ScenarioResult(
            id="slice-adapter-role-declaration",
            description=(
                "The packaged verifier agent carries role frontmatter, the descriptor declares its "
                "portable model role, and no provider selector is hardcoded; OMP-side resolution is "
                "the live role-resolution row"
            ),
            plane="adapter",
            command=f"frontmatter(agents/{DEFAULT_AGENT}.md) + pstack.package.json roles[]",
            exit_code=0 if (offline["agent_role_declared"] and not offline["hardcoded_provider_selector"]) else 1,
            stdout_snippet=(
                f"declared_role={offline['declared_model_role']} "
                f"hardcoded_provider_selector={offline['hardcoded_provider_selector']}"
            ),
            verdict="PASS"
            if (offline["agent_role_declared"] and not offline["hardcoded_provider_selector"])
            else "FAIL",
            duration_s=0.0,
            evidence_level="offline",
        ),
        ScenarioResult(
            id="slice-package-projection",
            description="Install writes an OMP package whose manifest and skill/agent shape verify",
            plane="package",
            command="python3 scripts/package-lifecycle.py install --host omp (temp base) + verify",
            exit_code=0 if (offline["shape_ok"] and offline["manifest_ok"]) else 1,
            stdout_snippet=(
                f"manifest={offline['manifest'].get('name')} omp_key="
                f"{isinstance(offline['manifest'].get('omp'), dict)} errors={offline['shape_errors']}"
            ),
            verdict="PASS" if (offline["shape_ok"] and offline["manifest_ok"]) else "FAIL",
            duration_s=offline["duration_s"],
            evidence_level="offline",
        ),
        ScenarioResult(
            id="slice-package-uninstall-sentinel",
            description=(
                "The uninstall plan removes only owned paths and preserves user-authored sentinels"
            ),
            plane="package",
            command="python3 scripts/package-lifecycle.py uninstall --host omp (temp base)",
            exit_code=0 if (offline["uninstall_ok"] and offline["sentinels_preserved"] and offline["owned_paths_removed"]) else 1,
            stdout_snippet=(
                f"plan_owned={len(offline['plan']['owned'])} plan_preserved={offline['plan']['preserved']} "
                f"sentinels_preserved={offline['sentinels_preserved']} owned_removed={offline['owned_paths_removed']}"
            ),
            verdict="PASS"
            if (offline["uninstall_ok"] and offline["sentinels_preserved"] and offline["owned_paths_removed"])
            else "FAIL",
            duration_s=0.0,
            evidence_level="offline",
        ),
    ]

    if live is not None:
        discovery_ok = bool(
            live.get("enrolled")
            and live.get("discovery_root_inside_disposable")
            and live.get("router_advertised")
            and live.get("linked_router_matches_package")
        )
        scenario_list.append(
            ScenarioResult(
                id="slice-package-native-discovery",
                description=(
                    "The real OMP binary enrolls the linked package, advertises its poteto-mode "
                    "router, and the enrolled plugin path carries this package's router bytes"
                ),
                plane="package",
                command="omp plugin link <temp package>; omp plugin list --json; rpc available_commands_update",
                exit_code=0 if discovery_ok else 1,
                stdout_snippet=(
                    f"enrolled={live.get('enrolled')} disposable_root={live.get('discovery_root_inside_disposable')} "
                    f"router_advertised={live.get('router_advertised')} "
                    f"linked_router_matches_package={live.get('linked_router_matches_package')} "
                    f"ambient_control_had_router={live.get('router_in_ambient_control')}"
                ),
                verdict="PASS" if discovery_ok else "FAIL",
                duration_s=0.0,
                evidence_level="observed_live",
            )
        )
        child = live.get("child") or {}
        route_error = child.get("route_error") or ""
        if route_error or child.get("failure"):
            role_verdict, role_snippet = "BLOCKED", f"BLOCKED: {route_error or child.get('failure')}"
        else:
            settlement = child.get("settlement")
            resolved = settlement["model"] if settlement else ""
            role_verdict = "PASS" if resolved == selector else "FAIL"
            role_snippet = f"selector={selector} observed_model={resolved or 'none'}"
        scenario_list.append(
            ScenarioResult(
                id="slice-adapter-role-resolution",
                description=(
                    "The child's frontmatter model role resolved through the run-local modelRoles "
                    "overlay to the selected model"
                ),
                plane="adapter",
                command="rpc subagent_progress resolvedModelIdentity for the prompted child",
                exit_code=0 if role_verdict == "PASS" else 1,
                stdout_snippet=role_snippet,
                verdict=role_verdict,
                duration_s=0.0,
                evidence_level="observed_live" if role_verdict == "PASS" else "offline",
            )
        )

    if live is None:
        scenario_list.append(
            ScenarioResult(
                id="slice-runtime-child-spawn",
                description="Live child spawn/join was not observed: no live model route was attempted",
                plane="runtime",
                command="omp --mode rpc --live (not run)",
                exit_code=1,
                stdout_snippet=f"BLOCKED: {live_blocked or 'live gate closed'}",
                verdict="BLOCKED",
                duration_s=0.0,
                evidence_level="offline",
            )
        )
    else:
        scenario_list.append(
            runtime_row(
                live.get("child") or {},
                selector,
                float(live.get("child_seconds") or 0.0),
            )
        )
    return scenario_list


def build_receipt(
    out_dir: Path,
    scenarios: List[ScenarioResult],
    head: str,
    host_version: str,
    artifacts: List[str],
) -> tuple[VerificationReceipt, Path]:
    planes = {
        plane: _vp.reduce_verdicts([s.verdict for s in scenarios if s.plane == plane])
        for plane in ("canonical", "adapter", "package", "runtime")
    }
    receipt = VerificationReceipt(
        run_id=f"omp-slice-{head[:12]}-{secrets.token_hex(3)}",
        host="omp",
        host_version=host_version or "not-observed",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        overall_verdict=_vp.reduce_verdicts(planes.values()),
        planes=planes,
        surface_revisions=compute_surface_revisions(ROOT, "omp"),
        scenarios=scenarios,
        artifacts=artifacts,
        claim=(
            "one OMP vertical slice (package -> poteto-mode -> model role -> child -> uninstall) "
            f"at exact head {head}"
        ),
        kind="runtime",
    )
    receipt.validate()
    path = out_dir / "slice-receipt.json"
    path.write_text(json.dumps(asdict(receipt), indent=2) + "\n", encoding="utf-8")
    # Round-trip so a shape or serialization regression fails here, not in a consumer.
    VerificationReceipt(**json.loads(path.read_text(encoding="utf-8"))).validate()
    return receipt, path


# --- orchestration ----------------------------------------------------------


def prove(
    live_requested: bool,
    agent: str,
    selector_override: str,
    keep: bool,
    out_dir: Optional[Path],
    max_seconds: float,
) -> Dict[str, Any]:
    omp_bin = shutil.which("omp")
    head = git_revision(ROOT, "rev-parse", "HEAD")
    selector = selector_override or ambient_review_selector()
    report: Dict[str, Any] = {
        "lever": "prove-omp-vertical-slice",
        "issue": 292,
        "verdict": "BLOCKED",
        "reason": "",
        "live_requested": bool(live_requested),
        "exact_head": head,
        "branch": git_revision(ROOT, "rev-parse", "--abbrev-ref", "HEAD"),
        "omp_bin": omp_bin,
        "omp_version": omp_version(omp_bin),
        "review_selector": selector,
        "readonly": READ_ONLY,
        "offline": None,
        "live": None,
        "receipt": None,
        "receipt_path": None,
        "run_dir": None,
    }

    temp_root = Path(tempfile.mkdtemp(prefix="pstack-omp-slice-"))
    run_dir = temp_root / "run"
    run_dir.mkdir(parents=True)
    live_blocked = ""
    offline: Optional[Dict[str, Any]] = None
    live: Optional[Dict[str, Any]] = None
    failure = ""
    try:
        offline = offline_slice(run_dir, agent)
        if live_requested:
            if omp_bin is None:
                live_blocked = "omp binary not found on PATH"
            elif not selector:
                live_blocked = (
                    "no model route: pass --review-model or configure an ambient task/default model role"
                )
            else:
                installed = _pl.install_plugin("omp", target_base=temp_root / "install")
                package = temp_root / "package"
                shutil.copytree(installed, package, symlinks=True)
                write_sentinels(package)
                live = live_slice(omp_bin, package, run_dir, agent, selector, max_seconds)
    except (OmpRpcError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        failure = f"{type(exc).__name__}: {exc}"

    report["offline"] = offline
    report["live"] = live

    if offline is None:
        report["verdict"] = "BLOCKED"
        report["reason"] = failure or "the offline half did not complete"
        report["run_dir"] = str(temp_root) if keep else None
        if not keep:
            shutil.rmtree(temp_root, ignore_errors=True)
        return report
    if failure:
        live_blocked = live_blocked or failure

    artifacts = []
    target_dir = out_dir or run_dir
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.append(str(target_dir / "slice-receipt.json"))
    for name in ("review-role.yml", "slice-rpc.jsonl"):
        source = run_dir / name
        if not source.is_file():
            continue
        destination = target_dir / name
        if destination != source:
            shutil.copy2(source, destination)
        artifacts.append(str(destination))

    scenarios = slice_scenarios(offline, live, live_blocked, selector)
    receipt, receipt_path = build_receipt(
        target_dir, scenarios, head, report["omp_version"], artifacts
    )
    report["verdict"] = receipt.overall_verdict
    report["planes"] = dict(receipt.planes)
    report["receipt"] = asdict(receipt)
    report["receipt_path"] = str(receipt_path)
    uninstall_rows = [s for s in scenarios if s.id == "slice-package-uninstall-sentinel"]
    live_note = "live=not requested"
    if live_requested:
        live_note = f"live={'observed' if live else 'skipped'}"
        if live_blocked and not live:
            live_note += f" ({live_blocked})"
    report["reason"] = (
        f"package projection={'PASS' if offline['shape_ok'] and offline['manifest_ok'] else 'FAIL'}, "
        f"uninstall={uninstall_rows[0].verdict if uninstall_rows else 'UNTESTED'}, "
        f"router={'PASS' if offline['router_matches_canonical'] else 'FAIL'}, {live_note}, "
        f"runtime={receipt.planes['runtime']}"
    )
    report["run_dir"] = str(temp_root) if keep else None
    if not keep:
        shutil.rmtree(temp_root, ignore_errors=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help=f"Also link/observe the real binary and spawn one child (or set {LIVE_GATE_ENV}=1)",
    )
    parser.add_argument("--agent", default=DEFAULT_AGENT, help="Packaged role agent the live arm spawns")
    parser.add_argument(
        "--review-model",
        default="",
        help="Selector for the run-local modelRoles.review overlay (default: ambient task/default role)",
    )
    parser.add_argument("--out", type=Path, help="Write the receipt (and RPC log) to this directory")
    parser.add_argument("--keep", action="store_true", help="Keep the temp run directory for inspection")
    parser.add_argument("--max-seconds", type=float, default=LIVE_MAX_SECONDS, help="Live session deadline")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON")
    args = parser.parse_args()

    live = args.live or os.environ.get(LIVE_GATE_ENV) == "1"
    report = prove(live, args.agent, args.review_model, args.keep, args.out, args.max_seconds)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"OMP vertical slice: {report['verdict']}")
        print(f"  exact_head: {report['exact_head']}")
        print(f"  planes: {report.get('planes')}")
        print(f"  receipt: {report.get('receipt_path')}")
        print(f"  reason: {report['reason']}")
        if report.get("offline"):
            print(f"  uninstall plan: {json.dumps(report['offline']['plan']['preserved'])} preserved")
        if report.get("live"):
            print(f"  child: {json.dumps((report['live'].get('child') or {}).get('settlement'))}")

    sys.exit(0 if report["verdict"] == "PASS" else (1 if report["verdict"] == "FAIL" else 2))


if __name__ == "__main__":
    main()
