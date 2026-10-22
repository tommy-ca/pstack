from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

SWITCHER = "[English](README.md) · [简体中文](README.zh-CN.md)"
CJK = re.compile(r"[\u4e00-\u9fff]")


def test_verify_guide_names_monitor_boundary() -> None:
    guide = (ROOT / "docs/guide/06-verify-and-ship.md").read_text(encoding="utf-8")
    assert "bundled watcher" not in guide
    assert "`monitor`" in guide


def test_guide_teaches_sync_then_adapt() -> None:
    guide = (ROOT / "docs/guide/09-make-it-yours.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    upstream = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert "atomic building blocks" in guide
    assert "adapt-harness.py" in guide
    assert "verify-harness.py" in guide
    assert "sync-from-upstream.py" in guide
    index = (ROOT / "docs/guide/README.md").read_text(encoding="utf-8")
    assert "does not auto-enter" in index
    natives = (ROOT / "docs/guide/13-grok-natives.md").read_text(encoding="utf-8")
    assert "grok --worktree" in natives
    assert "grok -p" in natives
    assert "enter_plan_mode" in natives
    assert "skip" in natives.lower()
    assert "13-grok-natives.md" in index
    spec_n = (
        ROOT
        / "openspec/specs/pstack-grok-natives/spec.md"
    )
    assert spec_n.is_file()
    assert "adopt" in spec_n.read_text(encoding="utf-8").lower()
    assert "spawn_subagent" in guide
    assert "scheduler_create" in guide
    assert "make-bot-ui" in guide
    assert "control-cli" in guide
    assert "tommy-ca/pstack" in setup
    assert "aa2246740/pstack-grokbuild --trust" not in setup
    assert "grok plugin install pstack --trust" not in setup
    assert "cursor/plugins" in setup
    assert "spawn_subagent" in setup
    assert "automations/benny-grok" in setup
    assert "skills/` and `agents/` only" not in setup
    assert "grok-build-plugins" in guide
    assert "host mapping" in setup
    assert "not a plugin.json field" in setup
    assert "MAX_SUBAGENT_DEPTH" in harness
    assert "Skill order" in setup
    assert "pstack:independent-verifier" in setup
    assert "scheduler_create" in setup
    assert "Essential entries" in setup
    assert "/tdd" in setup
    assert "/how" in setup
    assert "/workflow" in setup
    assert "workspace" in setup
    assert "Daily driver" in setup
    spec_sb = (
        ROOT
        / "openspec/specs/pstack-sandbox-daily/spec.md"
    )
    assert spec_sb.is_file()
    assert "workspace" in spec_sb.read_text(encoding="utf-8")
    spec_q = (
        ROOT
        / "openspec/specs/pstack-quickstart/spec.md"
    )
    assert spec_q.is_file()
    assert "MAX_SUBAGENT_DEPTH" in spec_q.read_text(encoding="utf-8")
    spec = ROOT / "openspec/specs/pstack-harness-md/spec.md"
    assert spec.is_file()
    assert "not a PluginManifest field" in spec.read_text(encoding="utf-8")
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "HARNESS" not in json.dumps(plugin)
    port = (ROOT / "docs/guide/12-porting.md").read_text(encoding="utf-8")
    assert "24 principles" in port
    assert "host map" in port
    assert "Laziness Protocol" in port
    assert "Capability checklist" in port
    assert "Spawn a child" in port
    assert "Join / wait" in port
    assert "Overnight loop" in port
    assert "Write `gap`" in port or "write `gap`" in port.lower()
    assert "not loc" in port.lower() or "less code" in port.lower()
    assert "12-porting.md" in index
    spec_port = (
        ROOT / "openspec/specs/pstack-reference-port/spec.md"
    )
    assert spec_port.is_file()
    assert "host map" in spec_port.read_text(encoding="utf-8")
    assert "adapt-harness.py" in upstream
    assert "sync-from-upstream.py" in upstream
    pin = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync-from-upstream.py"), "--pin"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert pin.returncode == 0, pin.stderr
    sha = pin.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{40}", sha), sha
    plan = (ROOT / "TEST-PLAN.md").read_text(encoding="utf-8")
    assert f"tree `{sha}`" in plan, sha
    assert "46125561306434d8a1d7745d540d8932ab0cd2a2" not in plan
    recipe = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync-from-upstream.py"), "--recipe"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert recipe.returncode == 0, recipe.stderr
    assert sha in recipe.stdout
    assert "adapt-harness.py" in recipe.stdout
    assert "verify-harness.py" in recipe.stdout
    assert "verify.py run" in recipe.stdout
    assert "sync-from-upstream.py --pin" in recipe.stdout
    assert "Full sweep" in recipe.stdout
    assert "leftover-scanner" in recipe.stdout
    assert "upstream-pin" in recipe.stdout
    assert "absorbed-intent" in recipe.stdout
    assert "upstream-recipe" in recipe.stdout
    assert "refresh-hygiene" in recipe.stdout
    assert "release-tag" in recipe.stdout
    assert "verify-harness.py && python3 tests/test_verify_harness.py" not in recipe.stdout
    assert "make-bot-ui" in recipe.stdout
    assert "pstack:<role>" in recipe.stdout
    assert "upstream-cursor-plugins/pstack" in recipe.stdout
    assert "classification.tsv" in recipe.stdout
    assert "partition.py" in recipe.stdout
    assert "apply.py" in recipe.stdout
    assert "apply-check" in recipe.stdout
    assert "print --coverage" in recipe.stdout
    cache_table = (
        "--cache .worktrees/upstream-cursor-plugins --table "
        "/tmp/pstack-refresh/overlay.tsv"
    )
    assert cache_table in recipe.stdout
    assert recipe.stdout.count(cache_table) >= 3
    assert "seed --cache .worktrees/upstream-cursor-plugins" in recipe.stdout
    assert "--cache --table" not in recipe.stdout
    assert not (ROOT / ".grok/workflows").exists()
    rhai = ROOT / "skills/swarm/references/pstack-upstream-refresh.rhai"
    assert rhai.is_file()
    rhai_text = rhai.read_text(encoding="utf-8")
    assert "capability_mode" not in rhai_text
    assert 'agent_type: "pstack:swarm-workers"' in rhai_text
    assert 'agent_type: "pstack:interrogate-reviewers"' in rhai_text
    assert 'agent_type: "pstack:independent-verifier"' in rhai_text
    assert "pack.py" in recipe.stdout
    assert "scripts/orch/" in recipe.stdout
    assert "advisor" in recipe.stdout
    # The recipe forbids overwriting plugin.json, so the checked-out manifest must
    # still carry the port's own prerelease identity, never upstream's bare packaging.
    root_version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+-[a-z]+\.\d+", root_version), root_version
    default = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync-from-upstream.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert default.returncode == 0, default.stderr
    assert default.stdout == recipe.stdout
    logged = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync-from-upstream.py"), "--log"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert logged.returncode == 0, logged.stderr
    assert f"pin {sha}" in logged.stdout
    assert "up to date" in logged.stdout or re.search(
        r"^[0-9a-f]{7} ", logged.stdout, re.MULTILINE
    )
    sync_loader = importlib.util.spec_from_file_location(
        "sync_from_upstream_log", ROOT / "scripts/sync-from-upstream.py"
    )
    assert sync_loader is not None and sync_loader.loader is not None
    sync = importlib.util.module_from_spec(sync_loader)
    sync_loader.loader.exec_module(sync)
    cache = sync.remote_cache()
    if (cache / ".git").is_dir() or (cache / "HEAD").is_file():
        head = subprocess.run(
            ["git", "-C", str(cache), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        tip = subprocess.run(
            ["git", "-C", str(cache), "rev-parse", "origin/main"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert head == tip, (head, tip)
    assert ".cursor/skills" not in guide
    assert "Cursor's built-in `create-skill`" not in guide
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    verify = (ROOT / "docs/guide/06-verify-and-ship.md").read_text(
        encoding="utf-8"
    )
    assert "tommy-ca/pstack --trust" in readme
    assert "aa2246740/pstack-grokbuild --trust" not in readme
    assert "spawn_subagent" in readme
    assert "xAI Official" in readme
    assert "grok plugin install pstack --trust" not in readme
    assert ".cursor/skills" not in verify
    assert ".grok/skills/verify-" in verify
    assert ".cursor/skills" not in setup


def test_readme_locale_split() -> None:
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    zh_path = ROOT / "README.zh-CN.md"
    assert zh_path.is_file(), zh_path
    zh = zh_path.read_text(encoding="utf-8")
    assert SWITCHER in en
    assert SWITCHER in zh
    en_body = en.replace(SWITCHER, "")
    assert CJK.search(en_body) is None, "English README has CJK outside the switcher"
    assert CJK.search(zh) is not None
    for text in (en, zh):
        assert "tommy-ca/pstack --trust" in text
        assert "grok plugin install pstack --trust" not in text
        assert "spawn_subagent" in text
        assert "xAI Official" in text
        assert "cursor/plugins" in text
        assert "aa2246740/pstack-grokbuild --trust" not in text
        assert "pstack:poteto-agent" in text
        assert "pstack:comment-sicko" in text
        assert "pstack:independent-verifier" in text
        assert "plugins/pstack" in text
        assert "grok-build-plugins" in text


def test_first_session_names_sandbox_reload_and_slash() -> None:
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
    assert not (ROOT / "commands").exists()
    for text in (en, zh, setup):
        assert (
            "## First session" in text
            or "## Grok Build first session" in text
            or "## 第一次会话" in text
            or "## Grok Build 第一次会话" in text
        )
        assert "grok --sandbox off plugin enable pstack" in text
        assert "pstack:how-explorer" in text
        assert "/poteto-mode" in text
        assert "[plugins].enabled" in text
        assert "new session" in text or "新会话" in text
        assert "grok plugin install pstack --trust" not in text
        assert "sticky mode" not in text.lower()
        assert "粘滞模式" not in text
    poteto = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    fm = poteto.split("---", 2)[1]
    assert "mode: true" not in fm
    guide = (ROOT / "docs/guide/02-poteto-mode.md").read_text(encoding="utf-8")
    assert "sticky" not in guide.lower()
    assert "does not auto-enter" in guide
    assert "a mode mid-Feature" not in guide
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
    assert "sticky" not in setup.lower()


def test_forge_neutral_pr_path_without_graphite() -> None:
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    ref = ROOT / "skills/poteto-mode/references/github-pr-fallback.md"
    assert ref.is_file()
    text = ref.read_text(encoding="utf-8").lower()
    harness_lower = harness.lower()
    assert "github-pr-fallback.md" in harness
    assert "gh pr" in harness_lower
    assert "origin pr" in harness_lower
    assert "command -v gt" not in text
    assert "gh pr create" in text
    assert "gh pr view" in text
    assert "gh pr checks" in text
    assert "gh pr merge" in text
    assert "--auto" in text
    assert "protected trunk" in text
    assert "--base" in text
    opening = (ROOT / "skills/poteto-mode/playbooks/opening-a-pr.md").read_text(
        encoding="utf-8"
    ).lower()
    shipping = (ROOT / "skills/poteto-mode/playbooks/shipping.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "graphite-first" not in opening
    assert "gt submit" not in shipping
    assert "origin" in opening
    orchestrate = (
        ROOT / "skills/poteto-mode/playbooks/orchestrate.md"
    ).read_text(encoding="utf-8")
    orch = orchestrate.lower()
    assert "recompute it from `gt`" not in orch
    assert "may run `gt`" not in orch
    assert "gt tracking" not in orch
    assert "where gt knows" not in orch
    assert "github-pr-fallback.md" in orchestrate
    assert "origin pr" in orch or "gh pr" in orch
