from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-plugin-agents.py"
FIXTURES = ROOT / "tests" / "fixtures"


def run_check(inspect: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect-json", str(inspect)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_inspect(tmp_path: Path, payload: dict) -> Path:
    inspect = tmp_path / "inspect.json"
    inspect.write_text(json.dumps(payload), encoding="utf-8")
    return inspect


def tree_with_swarm_workers(root: Path) -> Path:
    agents = root / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "swarm-workers.md").write_text("swarm-workers\n", encoding="utf-8")
    return root


def test_enabled_tree_without_swarm_workers_fails(tmp_path: Path) -> None:
    foreign = tmp_path / "enabled-tree"
    (foreign / "agents").mkdir(parents=True)
    payload = {
        "agents": [
            {"name": "pstack:poteto-agent"},
            {"name": "pstack:comment-sicko"},
        ],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(foreign)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 1, got.stdout + got.stderr
    assert "pstack:swarm-workers" in got.stderr
    assert "agents/swarm-workers.md" in got.stderr
    assert "tommy-ca/pstack" in got.stderr


def test_name_without_enabled_path_fails() -> None:
    got = run_check(FIXTURES / "inspect-name-only.json")
    assert got.returncode == 1, got.stdout + got.stderr
    assert "no enabled pstack plugin path" in got.stderr


def test_checkout_pstack_passes(tmp_path: Path) -> None:
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"


def test_marketplace_path_fails_even_with_swarm_workers(tmp_path: Path) -> None:
    foreign = tree_with_swarm_workers(
        tmp_path / "claude" / "plugins" / "marketplaces" / "pstack-claude" / "plugins" / "pstack"
    )
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(foreign)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 1, got.stdout + got.stderr
    assert got.stderr.splitlines()[0] == "FAIL plugin-agents marketplace path"
    assert str(foreign) in got.stderr
    assert "PASS plugin-agents pstack:swarm-workers" not in got.stdout


def test_home_plugins_bind_fails_even_with_swarm_workers(tmp_path: Path) -> None:
    bind = tree_with_swarm_workers(tmp_path / ".grok" / "plugins" / "pstack")
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(bind)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 1, got.stdout + got.stderr
    assert got.stderr.splitlines()[0] == "FAIL plugin-agents ~/.grok/plugins/pstack bind"
    assert str(bind) in got.stderr
    assert "PASS plugin-agents pstack:swarm-workers" not in got.stdout


def test_pstack_skill_collidesWith_fails_on_clean_tree(tmp_path: Path) -> None:
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
        ],
        "skills": [
            {
                "name": "poteto-mode",
                "source": {
                    "type": "user",
                    "path": str(tmp_path / "user" / "poteto-mode" / "SKILL.md"),
                },
                "collidesWith": "poteto-mode",
                "invocableAs": "user:poteto-mode",
            },
            {
                "name": "poteto-mode",
                "source": {
                    "type": "plugin",
                    "plugin_name": "pstack",
                    "path": str(ROOT / "skills" / "poteto-mode" / "SKILL.md"),
                },
                "collidesWith": "poteto-mode",
                "invocableAs": "pstack:poteto-mode",
            },
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 1, got.stdout + got.stderr
    assert got.stderr.splitlines()[0] == "FAIL plugin-agents collidesWith poteto-mode"
    assert "Do not copy plugin skills into ~/.grok/skills" in got.stderr
    assert "PASS plugin-agents pstack:swarm-workers" not in got.stdout


def test_non_pstack_collidesWith_still_passes(tmp_path: Path) -> None:
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
        ],
        "skills": [
            {
                "name": "ponytail",
                "source": {
                    "type": "plugin",
                    "plugin_name": "ponytail",
                    "path": str(tmp_path / "ponytail" / "SKILL.md"),
                },
                "collidesWith": "ponytail",
                "invocableAs": "ponytail:ponytail",
            },
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"


def test_marketplace_beside_checkout_fails(tmp_path: Path) -> None:
    market = tree_with_swarm_workers(
        tmp_path / "plugins" / "marketplaces" / "pstack-claude" / "plugins" / "pstack"
    )
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
            {"name": "pstack", "enabled": True, "path": str(market)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 1, got.stdout + got.stderr
    assert "FAIL plugin-agents marketplace path" in got.stderr
    assert "PASS plugin-agents pstack:swarm-workers" not in got.stdout


def test_disabled_marketplace_does_not_block_checkout(tmp_path: Path) -> None:
    market = tree_with_swarm_workers(
        tmp_path / "plugins" / "marketplaces" / "pstack-claude" / "plugins" / "pstack"
    )
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
            {"name": "pstack", "enabled": False, "path": str(market)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"


def test_installed_plugins_tree_passes(tmp_path: Path) -> None:
    tree = tree_with_swarm_workers(tmp_path / "installed-plugins" / "pstack-6ff43f58")
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(tree)},
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"


def test_tilde_installed_plugins_path_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    tree = tree_with_swarm_workers(
        tmp_path / ".grok" / "installed-plugins" / "pstack-6ff43f58"
    )
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {
                "name": "pstack",
                "enabled": True,
                "path": "~/.grok/installed-plugins/pstack-6ff43f58",
            },
        ],
    }
    got = run_check(write_inspect(tmp_path, payload))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"
    assert str(tree) in got.stdout or "~/.grok/installed-plugins/pstack-6ff43f58" in got.stdout


def test_committed_marketplace_fixture_fails() -> None:
    got = run_check(FIXTURES / "inspect-marketplace.json")
    assert got.returncode == 1, got.stdout + got.stderr
    assert got.stderr.splitlines()[0] == "FAIL plugin-agents marketplace path"


def test_committed_home_bind_fixture_fails() -> None:
    got = run_check(FIXTURES / "inspect-home-bind.json")
    assert got.returncode == 1, got.stdout + got.stderr
    assert got.stderr.splitlines()[0] == "FAIL plugin-agents ~/.grok/plugins/pstack bind"


def test_committed_collidesWith_fixture_fails() -> None:
    got = run_check(FIXTURES / "inspect-collidesWith.json")
    assert got.returncode == 1, got.stdout + got.stderr
    assert "FAIL plugin-agents collidesWith" in got.stderr
    assert "PASS plugin-agents pstack:swarm-workers" not in got.stdout
