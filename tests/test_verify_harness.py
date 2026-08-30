"""Drive the shipped static harness scanner (not a reimplementation)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "verify-harness.py"


def test_verify_harness_script_exists() -> None:
    assert SCANNER.is_file(), SCANNER


def test_verify_harness_passes_on_this_tree() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCANNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_babysit_and_shipping_do_not_use_cursor_dynamic_loop() -> None:
    babysit = (ROOT / "skills/poteto-mode/playbooks/babysit.md").read_text(
        encoding="utf-8"
    )
    shipping = (ROOT / "skills/poteto-mode/playbooks/shipping.md").read_text(
        encoding="utf-8"
    )
    assert "in dynamic mode" not in babysit
    assert "in dynamic mode" not in shipping
    assert "monitor" in babysit
    assert "scheduler_create" in babysit
    assert "monitor" in shipping
    assert "scheduler_create" in shipping


def test_poteto_mode_first_todo_requires_host_map() -> None:
    skill = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    assert "HARNESS.md" in skill
    assert "codex-tools.md" in skill
    assert "current host" in skill
    head = skill.split("## Principles", 1)[0]
    assert "mapping file for the current host" in head


def test_codex_map_matches_grok_call_sites() -> None:
    mapping = (
        ROOT / "skills/poteto-mode/references/codex-tools.md"
    ).read_text(encoding="utf-8")
    assert "skills retain Claude Code tool language" not in mapping
    assert "`task`" in mapping or "task" in mapping
    assert "spawn_agent" in mapping
    assert "ask_user_question" in mapping


def test_poteto_mode_copies_tui_spawn_names() -> None:
    skill = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "spawn_subagent" in skill
    assert "get_command_or_subagent_output" in skill
    assert "spawn_subagent" in harness
    assert "get_command_or_subagent_output" in harness
    assert "scheduler_create" in harness
    assert "EROFS" in harness
    assert "config.toml" in harness
    assert "marketplace add" in harness


def test_visual_parity_and_bug_fix_drive_real_surface() -> None:
    visual = (
        ROOT / "skills/poteto-mode/playbooks/visual-parity.md"
    ).read_text(encoding="utf-8")
    bug = (ROOT / "skills/poteto-mode/playbooks/bug-fix.md").read_text(
        encoding="utf-8"
    )
    assert "control skill" not in visual
    assert "control-cli" not in visual
    assert "scheduler_create" in visual
    assert "control skill" not in bug


def test_make_bot_ui_is_not_invocable() -> None:
    assert not (ROOT / "skills/make-bot-ui").exists()
    plugin = (ROOT / "plugin.json").read_text(encoding="utf-8")
    assert "make-bot-ui" not in plugin


def test_guide_teaches_sync_then_adapt() -> None:
    guide = (ROOT / "docs/guide/09-make-it-yours.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
    upstream = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert "atomic building blocks" in guide
    assert "adapt-harness.py" in guide
    assert "verify-harness.py" in guide
    assert "spawn_subagent" in guide
    assert "scheduler_create" in guide
    assert "make-bot-ui" in guide
    assert "control-cli" in guide
    assert "tommy-ca/pstack" in setup
    assert "aa2246740/pstack-grokbuild --trust" not in setup
    assert "grok plugin install pstack --trust" not in setup
    assert "cursor/plugins" in setup
    assert "spawn_subagent" in setup
    assert "adapt-harness.py" in upstream
    assert ".cursor/skills" not in guide
    assert "Cursor's built-in `create-skill`" not in guide
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    verify = (ROOT / "docs/guide/06-verify-and-ship.md").read_text(
        encoding="utf-8"
    )
    assert "tommy-ca/pstack --trust" in readme
    assert "aa2246740/pstack-grokbuild --trust" not in readme
    assert "spawn_subagent" in readme
    assert "xAI Official also lists" in readme
    assert "grok plugin install pstack --trust" not in readme
    assert ".cursor/skills" not in verify
    assert ".grok/skills/verify-" in verify
    assert ".cursor/skills" not in setup


def test_grok_spawn_types_are_plugin_qualified() -> None:
    """grok 1.0.13 registers plugin agents as plugin:name, not the bare stem."""
    effort = (
        ROOT / "skills/setup-pstack/references/resolve-effort.md"
    ).read_text(encoding="utf-8")
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    how = (ROOT / "skills/how/SKILL.md").read_text(encoding="utf-8")
    why = (ROOT / "skills/why/SKILL.md").read_text(encoding="utf-8")
    arena = (ROOT / "skills/arena/SKILL.md").read_text(encoding="utf-8")
    swarm = (ROOT / "skills/swarm/SKILL.md").read_text(encoding="utf-8")
    interrogate = (ROOT / "skills/interrogate/SKILL.md").read_text(
        encoding="utf-8"
    )
    architect = (ROOT / "skills/architect/SKILL.md").read_text(encoding="utf-8")
    no_comments = (ROOT / "skills/no-comments/SKILL.md").read_text(
        encoding="utf-8"
    )
    poteto = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    feature = (
        ROOT / "skills/poteto-mode/playbooks/feature.md"
    ).read_text(encoding="utf-8")
    assert "pstack:how-explorer" in how
    assert "pstack:how-explainer" in how
    assert "pstack:how-critics" in how
    assert "pstack:why-investigators" in why
    assert "pstack:why-synthesizer" in why
    assert "pstack:arena-runners" in arena
    assert "pstack:arena-cross-judge-pool" in arena
    assert "pstack:swarm-workers" in swarm
    assert "pstack:interrogate-reviewers" in interrogate
    assert "pstack:architect-runners" in architect
    assert "pstack:comment-sicko" in no_comments
    assert "pstack:feature" in feature
    assert "pstack:independent-verifier" in feature
    assert "pstack:<key>" in effort or "pstack:<role-key>" in effort
    assert "Send the **bare** name so it matches" not in effort
    assert "pstack:<key>" in harness or "pstack:<role" in harness
    assert "Send the **bare** role key so" not in harness
    assert "pstack:poteto-agent" in poteto


if __name__ == "__main__":
    test_verify_harness_script_exists()
    test_verify_harness_passes_on_this_tree()
    test_babysit_and_shipping_do_not_use_cursor_dynamic_loop()
    test_poteto_mode_first_todo_requires_host_map()
    test_codex_map_matches_grok_call_sites()
    test_poteto_mode_copies_tui_spawn_names()
    test_visual_parity_and_bug_fix_drive_real_surface()
    test_make_bot_ui_is_not_invocable()
    test_guide_teaches_sync_then_adapt()
    test_grok_spawn_types_are_plugin_qualified()
    print("PASS tests/test_verify_harness.py")
