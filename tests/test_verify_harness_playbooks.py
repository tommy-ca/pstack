from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

NO_WRITE_AGENT_STEMS = frozenset(
    {
        "how-explorer",
        "how-explainer",
        "how-critics",
        "interrogate-reviewers",
        "arena-cross-judge-pool",
        "independent-verifier",
        "comment-sicko",
    }
)
POSTURE_NOWRITE_STEMS = frozenset(
    {
        "why-investigators",
        "why-synthesizer",
        "reflect-judgment",
        "reflect-tooling",
    }
)


def test_autopilot_is_parent_fanout_and_skips_goal() -> None:
    full = (ROOT / "skills/poteto-mode/playbooks/autopilot-full.md").read_text(
        encoding="utf-8"
    )
    stack = (ROOT / "skills/poteto-mode/playbooks/autopilot-stack.md").read_text(
        encoding="utf-8"
    )
    for text in (full, stack):
        assert "arm a `/goal`" not in text
        assert "depth is 1" in text.lower() or "depth" in text.lower()
        assert "pstack:comment-sicko" in text
    spec = (
        ROOT
        / "openspec/specs/pstack-depth-1-overnight/spec.md"
    )
    assert spec.is_file()
    assert "MAX_SUBAGENT_DEPTH" in spec.read_text(encoding="utf-8")


def test_poteto_mode_first_todo_requires_host_map() -> None:
    skill = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    head = skill.split("## Principles", 1)[0]
    first_todo = head.split("Remaining triggers:", 1)[0]
    assert "identify the active host" in first_todo
    assert "`profiles/<host>.json`" in first_todo
    assert "`references/<host>-tools.md`" in first_todo
    assert "current host" in skill
    assert re.search(r"[A-Za-z0-9]+-tools\.md", skill) is None


def test_codex_map_matches_grok_call_sites() -> None:
    mapping = (
        ROOT / "skills/poteto-mode/references/codex-tools.md"
    ).read_text(encoding="utf-8")
    assert "skills retain Claude Code tool language" not in mapping
    assert "`task`" in mapping or "task" in mapping
    assert "spawn_agent" in mapping
    assert "ask_user_question" in mapping
    assert "Codex compatibility utilities" in mapping
    assert "not a Grok durable orchestration surface" in mapping


def test_poteto_mode_copies_tui_spawn_names() -> None:
    skill = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    grok_tools = (ROOT / "skills/poteto-mode/references/grok-tools.md").read_text(
        encoding="utf-8"
    )
    assert "agent.spawn" in skill or "subagents" in skill.lower()
    assert "spawn_subagent" in grok_tools
    assert "get_command_or_subagent_output" in grok_tools
    assert "spawn_subagent" in harness
    assert "get_command_or_subagent_output" in harness
    assert "scheduler_create" in harness
    assert "EROFS" in harness
    assert "config.toml" in harness
    assert "herdr integration install grok" in harness
    assert "HERDR_AGENT=grok" in harness
    assert "herdr:grok" in harness
    assert "agent_status" in harness
    assert "workspace" in harness
    assert "read-only" in harness
    assert "strict" in harness
    assert "herdr-install" not in harness
    assert "HERDR_SOCKET_PATH" in harness


def test_herdr_workspace_gate_is_documented() -> None:
    plan = (ROOT / "TEST-PLAN.md").read_text(encoding="utf-8")
    assert "Gate 0a. Herdr callback from the built-in workspace sandbox" in plan
    assert "source-managed Bash/Zsh helper" in plan
    assert 'test -r "$HOME/.bashrc.d/30-herdr-grok.sh"' in plan
    assert 'herdr pane run "$HINTED_PANE" grok --sandbox workspace --no-alt-screen' in plan
    assert 'herdr pane run "$NOHINT_PANE" command grok --sandbox workspace --no-alt-screen' in plan
    assert "HERDR_AGENT=grok" in plan
    assert "herdr:grok" in plan
    assert "agent_status == \"unknown\"" in plan
    assert "herdr agent list" in plan
    assert "herdr workspace close" in plan
    assert "[ ] Gate 0a PASS" in plan
    assert "Required: 0, 0a" in plan
    assert "TUI `spawn_subagent`" in plan
    assert 'remaining="$(jq --arg hinted' in plan
    assert 'workspace-list-before-close.json' in plan
    assert 'workspace-list-after-close.json' in plan
    assert 'test "$remaining" = 0' in plan
    assert 'HINTED_WORKSPACE="$(jq -r' in plan
    assert '"$HERDR_EVIDENCE/hinted-create.json")"' in plan
    assert 'NOHINT_WORKSPACE="$(jq -r' in plan
    assert '"$HERDR_EVIDENCE/nohint-create.json")"' in plan
    assert 'test -n "$HINTED_WORKSPACE"' in plan
    assert 'test -n "$NOHINT_WORKSPACE"' in plan


def test_visual_parity_and_bug_fix_drive_real_surface() -> None:
    visual = (
        ROOT / "skills/poteto-mode/playbooks/visual-parity.md"
    ).read_text(encoding="utf-8")
    bug = (ROOT / "skills/poteto-mode/playbooks/bug-fix.md").read_text(
        encoding="utf-8"
    )
    grok_tools = (ROOT / "skills/poteto-mode/references/grok-tools.md").read_text(
        encoding="utf-8"
    )
    assert "control skill" not in visual
    assert "control-cli" not in visual
    assert "schedule" in visual
    assert "scheduler_create" in grok_tools
    assert "control skill" not in bug


def test_make_bot_ui_is_not_invocable() -> None:
    assert not (ROOT / "skills/make-bot-ui").exists()
    plugin = (ROOT / "plugin.json").read_text(encoding="utf-8")
    assert "make-bot-ui" not in plugin


def test_benny_is_source_and_has_grok_remap() -> None:
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "hooks" not in plugin
    assert "fail-closed" not in json.dumps(plugin)
    skills_field = plugin.get("skills")
    skill_paths = (
        [skills_field] if isinstance(skills_field, str) else list(skills_field)
    )
    assert "./automations/benny-grok/skills/" in skill_paths
    assert "./skills/" in skill_paths
    assert not (ROOT / "skills/setup-benny").exists()
    assert not (ROOT / "skills/triage-issue-reports").exists()
    assert not (ROOT / "skills/reproduce-and-fix-issues").exists()
    pack = ROOT / "automations/benny"
    assert (pack / "FOR_AGENTS.md").is_file()
    triage = (pack / "skills/triage-issue-reports/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "[benny:bug]" in triage
    assert not (pack / "grok").exists()
    live_root = ROOT / "automations/benny-grok"
    assert live_root.is_dir()
    readme = (live_root / "README.md").read_text(encoding="utf-8")
    assert "grok plugin enable pstack" in readme
    assert "grok -p" in readme
    assert "mkdir -p .grok/hooks" not in readme
    assert "/automate" not in readme
    assert ".cursor/automations" not in readme
    assert "scheduler_create" in readme
    script = live_root / "bin/fail-closed.sh"
    deny = subprocess.run(
        ["sh", str(script)],
        input=json.dumps(
            {"toolInput": {"command": "gh pr merge 1 --merge"}}
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert deny.returncode == 2
    assert json.loads(deny.stdout)["decision"] == "deny"
    for command in (
        "git merge feature && git push origin main",
        "git push origin main && git merge feature",
    ):
        compound_deny = subprocess.run(
            ["sh", str(script)],
            input=json.dumps({"toolInput": {"command": command}}),
            capture_output=True,
            text=True,
            check=False,
        )
        assert compound_deny.returncode == 2, command
        assert json.loads(compound_deny.stdout)["decision"] == "deny", command
    force_lease = subprocess.run(
        ["sh", str(script)],
        input=json.dumps(
            {"toolInput": {"command": "git push --force-with-lease origin main"}}
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert force_lease.returncode == 2
    assert json.loads(force_lease.stdout)["decision"] == "deny"

    allow = subprocess.run(
        ["sh", str(script)],
        input=json.dumps({"toolInput": {"command": "gh pr view 1"}}),
        capture_output=True,
        text=True,
        check=False,
    )
    assert allow.returncode == 0
    assert json.loads(allow.stdout)["decision"] == "allow"
    slackish = subprocess.run(
        ["sh", str(script)],
        input=json.dumps(
            {"toolInput": {"command": "use_tool slack__post_message"}}
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert slackish.returncode == 0
    assert json.loads(slackish.stdout)["decision"] == "allow"
    safety = (
        ROOT
        / "openspec/specs/benny-safety/spec.md"
    ).read_text(encoding="utf-8")
    assert "prompt-enforced" in safety
    remap = (
        ROOT
        / "openspec/specs/benny-grok-remap/spec.md"
    ).read_text(encoding="utf-8")
    assert "prompt-enforced" in remap
    assert "upstream reference" in remap
    assert "plugin enable" in remap
    live_triage = (
        live_root / "skills/benny-triage/SKILL.md"
    ).read_text(encoding="utf-8")
    live_repro = (
        live_root / "skills/benny-repro/SKILL.md"
    ).read_text(encoding="utf-8")
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    assert "automations/benny-grok" in harness
    assert "automations/benny/grok" not in harness
    live = f"{readme}\n{live_triage}\n{live_repro}"
    assert "/automate" not in live
    assert "trigger.thread_ts" not in live
    assert "trigger.ts" not in live
    assert ".cursor/automations" not in live
    assert "spawn_subagent" in live_triage
    assert "pstack:" in live_triage
    assert "scheduler_create" in live
    assert "spawn_subagent" in live_repro
    assert "pstack:" in live_repro
    assert "name: benny-triage" in live_triage
    assert "name: benny-repro" in live_repro
    design = (
        ROOT
        / "openspec/changes/archive/2026-08-31-pstack-benny-atomic-blocks/design.md"
    ).read_text(encoding="utf-8")
    assert "automations/benny-grok/skills" in design
    assert "Installing Benny SKILL.md files under plugin `skills/`." not in design
    assert "grok/triage.md" not in design
    assert "grok/repro.md" not in design
    adr4 = ROOT / "adr/0004-benny-live-path-is-plugin-skills.md"
    assert adr4.is_file()
    assert "Supersedes: ADR-0002" in adr4.read_text(encoding="utf-8")
    pack_spec = (
        ROOT
        / "openspec/specs/benny-pack/spec.md"
    ).read_text(encoding="utf-8")
    assert "./automations/benny-grok/skills/" in pack_spec
    assert "THEN `skills` is `./skills/`" not in pack_spec


def test_playbooks_are_not_plugin_rhai_workflows() -> None:
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "workflows" not in plugin
    assert not (ROOT / ".grok/workflows").exists()
    rhai = list((ROOT / "skills/poteto-mode/playbooks").glob("*.rhai"))
    assert rhai == []
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    assert "not a plugin component" in harness
    spec = (
        ROOT
        / "openspec/specs/pstack-playbooks-not-rhai/spec.md"
    )
    assert spec.is_file()
    assert "MUST NOT" in spec.read_text(encoding="utf-8")
    adr = ROOT / "adr/0005-playbooks-are-not-rhai-workflows.md"
    assert adr.is_file()
    assert "/poteto-mode" in adr.read_text(encoding="utf-8")
    guide = (ROOT / "docs/guide/11-grok-workflows.md").read_text(encoding="utf-8")
    assert "agent_type" in guide
    assert "pstack:how-explorer" in guide
    rhai_example = re.search(r"```rhai\n(.*?)```", guide, re.S)
    assert rhai_example, "docs/guide/11-grok-workflows.md missing rhai example"
    example = rhai_example.group(1)
    assert 'agent_type: "pstack:how-explorer"' in example
    assert "capability_mode" not in example
    assert ".grok/workflows" in guide
    assert "PluginManifest" in guide
    assert "/workflow" in guide
    assert "not a plugin" in guide.lower() or "not a plugin.json" in guide
    index = (ROOT / "docs/guide/README.md").read_text(encoding="utf-8")
    assert "11-grok-workflows.md" in index
    spec = (
        ROOT
        / "openspec/specs/pstack-grok-workflows/spec.md"
    )
    assert spec.is_file()
    assert "agent_type" in spec.read_text(encoding="utf-8")


def test_nowrite_agents_use_capability_mode_execute() -> None:
    agents = list((ROOT / "agents").glob("*.md"))
    assert agents, "agents/ is empty"
    found = {path.stem for path in agents}
    missing_execute = NO_WRITE_AGENT_STEMS - found
    missing_posture = POSTURE_NOWRITE_STEMS - found
    assert not missing_execute, (
        f"execute-sandbox stems missing from agents/: {sorted(missing_execute)}"
    )
    assert not missing_posture, (
        f"prompt-posture stems missing from agents/: {sorted(missing_posture)}"
    )
    execute_re = re.compile(r"^capabilityMode:\s*execute\s*$", re.MULTILINE)
    for path in agents:
        fm = path.read_text(encoding="utf-8").split("---", 2)[1]
        if path.stem in NO_WRITE_AGENT_STEMS:
            assert execute_re.search(fm), (
                f"{path.relative_to(ROOT)}: no-write agent must set "
                "capabilityMode: execute"
            )
            continue
        if path.stem in POSTURE_NOWRITE_STEMS:
            assert "capabilityMode:" not in fm, (
                f"{path.relative_to(ROOT)}: prompt posture, not a sandbox; "
                "do not set capabilityMode"
            )
            continue
        assert "capabilityMode:" not in fm, (
            f"{path.relative_to(ROOT)}: writer must omit capabilityMode"
        )
