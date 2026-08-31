"""Drive the shipped static harness scanner (not a reimplementation)."""

from __future__ import annotations

import json
import re
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
    val = subprocess.run(
        ["grok", "plugin", "validate", str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert val.returncode == 0, val.stderr + val.stdout
    assert "Plugin manifest is valid" in val.stdout


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
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "automations/benny-grok" in harness
    assert "automations/benny/grok" not in harness
    live = "\n".join([readme, live_triage, live_repro])
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
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
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


def test_openspec_intent_driven_schema_resolves() -> None:
    schema = ROOT / "openspec/schemas/intent-driven/schema.yaml"
    assert schema.is_file()
    text = schema.read_text(encoding="utf-8")
    assert "name: intent-driven" in text
    assert "id: adr" in text
    cfg = (ROOT / "openspec/config.yaml").read_text(encoding="utf-8")
    assert "schema: intent-driven" in cfg
    change = (
        ROOT
        / "openspec/changes/archive/2026-08-31-pstack-benny-atomic-blocks"
    )
    assert (change / "design.md").is_file()
    assert (change / "adr.md").is_file()
    proc = subprocess.run(
        ["openspec", "schema", "which", "intent-driven"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    combined = (proc.stderr or "") + (proc.stdout or "")
    assert "intent-driven" in combined.lower()
    assert "not found" not in combined.lower()


def test_guide_teaches_sync_then_adapt() -> None:
    guide = (ROOT / "docs/guide/09-make-it-yours.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
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
    spec = ROOT / "openspec/specs/pstack-harness-md/spec.md"
    assert spec.is_file()
    assert "not a PluginManifest field" in spec.read_text(encoding="utf-8")
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "HARNESS" not in json.dumps(plugin)
    port = (ROOT / "docs/guide/12-porting.md").read_text(encoding="utf-8")
    assert "21 principles" in port
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
    assert "make-bot-ui" in recipe.stdout
    assert "pstack:<role>" in recipe.stdout
    assert "upstream-cursor-plugins/pstack" in recipe.stdout
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
        r"^[0-9a-f]{7} ", logged.stdout, re.M
    )
    cache = ROOT / ".worktrees" / "upstream-cursor-plugins"
    if (cache / ".git").is_dir():
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


SWITCHER = "[English](README.md) · [简体中文](README.zh-CN.md)"
CJK = re.compile(r"[\u4e00-\u9fff]")


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
    """Operator first page: enable EROFS, reload, slash-only poteto-mode."""
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs/guide/01-setup.md").read_text(encoding="utf-8")
    assert not (ROOT / "commands").exists()
    for text in (en, zh, setup):
        assert "## First session" in text or "## 第一次会话" in text
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


# grok 1.0.13 pager builtins from 04-slash-commands.md. Skills with these
# names lose /name to the builtin (qualified as pstack:name).
GROK_BUILTIN_SLASH = {
    "new",
    "resume",
    "dashboard",
    "compact",
    "context",
    "session-info",
    "fork",
    "rewind",
    "copy",
    "export",
    "quit",
    "home",
    "delete",
    "rename",
    "model",
    "effort",
    "always-approve",
    "auto",
    "multiline",
    "history",
    "compact-mode",
    "vim-mode",
    "edit-prompt",
    "minimal",
    "fullscreen",
    "plan",
    "view-plan",
    "memory",
    "flush",
    "dream",
    "remember",
    "hooks",
    "plugins",
    "marketplace",
    "skills",
    "imagine",
    "imagine-video",
    "loop",
    "goal",
    "deep-research",
    "workflow",
    "workflows",
    "theme",
    "feedback",
    "btw",
    "mcps",
    "doctor",
    "release-notes",
    "docs",
    "tutorial",
    "import-claude",
    "config-agents",
    "personas",
    "login",
    "logout",
    "usage",
    "privacy",
    "settings",
    "timestamps",
    "howto",
}


def test_pstack_slash_names_do_not_collide_with_grok_builtins() -> None:
    names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    hit = sorted(names & GROK_BUILTIN_SLASH)
    assert hit == [], hit
    assert not (ROOT / "commands").exists()
    agents = {p.stem for p in (ROOT / "agents").glob("*.md")}
    assert "explore" not in agents
    assert "plan" not in agents
    assert "general-purpose" not in agents


def test_overlay_stems_and_adapter_are_plugin_qualified() -> None:
    plan = (ROOT / "TEST-PLAN.md").read_text(encoding="utf-8")
    assert "~/.grok/roles/feature.toml" not in plan
    assert "~/.grok/roles/pstack:feature.toml" in plan
    assert "~/.grok/roles/pstack:bug-fix.toml" in plan
    assert "~/.grok/roles/pstack:how-explainer.toml" in plan
    assert "~/.grok/roles/pstack:independent-verifier.toml" in plan
    assert 'roles/${key}.toml' not in plan
    assert 'roles/pstack:${key}.toml' in plan
    adapt = (ROOT / "scripts/adapt-harness.py").read_text(encoding="utf-8")
    assert 'subagent_type: "pstack:comment-sicko"' in adapt
    assert "', 'subagent_type: \"comment-sicko\"')" not in adapt
    overlay = json.loads(
        (ROOT / ".grok-plugin/plugin.json").read_text(encoding="utf-8")
    )
    root_manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "displayName" not in overlay
    assert overlay["version"] == root_manifest["version"]
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "~/.grok/roles/<pstack-role>.toml" not in harness
    assert "~/.grok/roles/pstack:<key>.toml" in harness
    setup = (ROOT / "skills/setup-pstack/SKILL.md").read_text(encoding="utf-8")
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    for text in (en, zh, setup):
        assert "~/.grok/roles/*.toml" not in text
        assert "~/.grok/roles/pstack:" in text or "pstack:<" in text
    assert "files under `~/.grok/roles/`" not in setup
    assert "matching files under `~/.grok/roles/`" not in setup
    checklist = [ln for ln in plan.splitlines() if "Gate 4a PASS" in ln and "feature.toml" in ln]
    assert checklist, "missing Gate 4a checklist line"
    assert "pstack:feature.toml" in checklist[0]
    assert "bare or `pstack:`" not in plan
    assert "(`how-explorer`, `swarm-workers`" not in plan
    assert "`pstack:how-explorer`" in plan
    root_ver = root_manifest["version"]
    claude_mkt = json.loads(
        (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
    )
    assert claude_mkt["plugins"][0]["version"] == root_ver
    upstream = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    this_port = [ln.strip() for ln in upstream.splitlines() if ln.startswith("version ")]
    assert this_port, "UPSTREAM missing this-port version line"
    assert this_port[-1] == f"version {root_ver}", this_port


def test_effort_frontmatter_matches_ladder() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/effort_ladder.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    ladder = (ROOT / "skills/setup-pstack/references/effort-ladder.md").read_text(
        encoding="utf-8"
    )
    defaults = (
        ROOT / "skills/setup-pstack/references/defaults.toml"
    ).read_text(encoding="utf-8")
    resolve = (
        ROOT / "skills/setup-pstack/references/resolve-effort.md"
    ).read_text(encoding="utf-8")
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "use one of: xhigh, high, medium, low" in ladder
    assert "grok 1.0.13" in ladder
    assert "pstack:<role-key>" in defaults or "pstack:<key>" in defaults
    assert "Spawn subagent_type = the role key" not in defaults
    assert "may also write the bare stem" not in resolve
    iv = (ROOT / "agents/independent-verifier.md").read_text(encoding="utf-8")
    assert "effort: xhigh" in iv
    assert "capabilityMode: execute" in iv
    assert "grok 1.0.13" in harness
    parsed: dict[str, str] = {}
    in_effort = False
    for line in defaults.splitlines():
        if line.strip() == "[effort]":
            in_effort = True
            continue
        if in_effort:
            if line.startswith("["):
                break
            m = re.match(r'^([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"', line)
            if m:
                parsed[m.group(1)] = m.group(2)
    for path in (ROOT / "agents").glob("*.md"):
        fm = path.read_text(encoding="utf-8").split("---", 2)[1]
        m = re.search(r"^effort:\s*(\S+)", fm, re.M)
        if not m:
            assert path.stem in {"comment-sicko", "poteto-agent"}, path.name
            continue
        assert parsed[path.stem] == m.group(1), path.name
    assert not re.search(r"^\[models\]", defaults, re.M)
    assert (ROOT / "skills/figure-it-out/SKILL.md").is_file()
    assert not (ROOT / "skills/poteto-mode/playbooks/figure-it-out.md").exists()
    assert "playbooks/figure-it-out.md" not in harness
    setup_spec = (
        ROOT
        / "openspec/specs/pstack-setup-overlays/spec.md"
    ).read_text(encoding="utf-8")
    assert "top-level" in setup_spec
    assert "`[models]` table" in setup_spec or "MUST NOT use a `[models]` table" in setup_spec


def test_plugin_manifest_matches_grok_parsed_fields() -> None:
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "displayName" not in manifest
    assert manifest["name"] == "pstack"
    assert isinstance(manifest.get("repository"), str)
    assert isinstance(manifest.get("author"), dict)
    assert "commands" not in manifest
    assert not (ROOT / "commands").exists()
    assert not (ROOT / "hooks").exists()
    assert not (ROOT / ".mcp.json").exists()
    assert not (ROOT / ".lsp.json").exists()
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "## Plugin schema" in harness
    assert "PluginManifest" in harness
    assert "Do not ship `permissionMode: plan`" in harness
    for path in (ROOT / "agents").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "permissionMode: plan" not in text, path.name
        assert "permissionMode: bypassPermissions" not in text, path.name
        assert "mcpServers:" not in text.split("---", 2)[1], path.name
        assert "background: true" not in text.split("---", 2)[1], path.name
        if "Setup may overlay via" in text:
            assert "~/.grok/roles/pstack:" in text, path.name


def test_harness_skill_order_is_pstack_then_user_then_native() -> None:
    harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    poteto = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    tdd = (ROOT / "skills/tdd/SKILL.md").read_text(encoding="utf-8")
    interrogate = (ROOT / "skills/interrogate/SKILL.md").read_text(
        encoding="utf-8"
    )
    babysit = (
        ROOT / "skills/poteto-mode/playbooks/babysit.md"
    ).read_text(encoding="utf-8")
    how = (ROOT / "skills/how/SKILL.md").read_text(encoding="utf-8")
    bug_fix = (
        ROOT / "skills/poteto-mode/playbooks/bug-fix.md"
    ).read_text(encoding="utf-8")
    figure = (ROOT / "skills/figure-it-out/SKILL.md").read_text(
        encoding="utf-8"
    )
    authoring = (
        ROOT / "skills/poteto-mode/playbooks/authoring-a-skill.md"
    ).read_text(encoding="utf-8")
    adapt = (ROOT / "scripts/adapt-harness.py").read_text(encoding="utf-8")
    assert "## Skill order" in harness
    assert "## Native first" not in harness
    assert "pstack, then user, then bundled and builtin" in harness
    assert "Use built-in `explore`" not in harness
    assert "pstack:how-explorer" in harness
    table_babysit = [ln for ln in harness.splitlines() if ln.startswith("| Babysit |")]
    assert table_babysit, "missing Babysit row"
    assert "/pr-babysit" not in table_babysit[0]
    assert "Skill order" in poteto or "pstack first" in poteto
    assert "before `/pr-babysit`" not in poteto
    assert "Use it first" in tdd
    assert "Skip both" in tdd or "skip both" in tdd
    assert "does not apply" not in tdd
    assert tdd.find("/tdd") < tdd.find("/test-driven-development")
    assert "Use it first" in interrogate
    assert "/review" in interrogate
    assert "use `/review`" not in interrogate.lower()
    assert "Do not route to `/pr-babysit`" in babysit
    assert "pstack:how-explorer" in how
    idx_p = how.find("pstack:how-explorer")
    idx_e = how.find("builtin `explore`")
    assert idx_p != -1
    if idx_e != -1:
        assert idx_p < idx_e
    assert "/tdd" in bug_fix
    assert "Skip both" in bug_fix or "skip both" in bug_fix
    assert "Use it first" in figure
    assert "Apply this playbook" in authoring or "this playbook" in authoring[:400]
    assert "pstack:how-explorer" in adapt


if __name__ == "__main__":
    test_verify_harness_script_exists()
    test_verify_harness_passes_on_this_tree()
    test_babysit_and_shipping_do_not_use_cursor_dynamic_loop()
    test_poteto_mode_first_todo_requires_host_map()
    test_codex_map_matches_grok_call_sites()
    test_poteto_mode_copies_tui_spawn_names()
    test_visual_parity_and_bug_fix_drive_real_surface()
    test_make_bot_ui_is_not_invocable()
    test_benny_is_source_and_has_grok_remap()
    test_playbooks_are_not_plugin_rhai_workflows()
    test_openspec_intent_driven_schema_resolves()
    test_guide_teaches_sync_then_adapt()
    test_grok_spawn_types_are_plugin_qualified()
    test_readme_locale_split()
    test_first_session_names_sandbox_reload_and_slash()
    test_pstack_slash_names_do_not_collide_with_grok_builtins()
    test_overlay_stems_and_adapter_are_plugin_qualified()
    test_effort_frontmatter_matches_ladder()
    test_plugin_manifest_matches_grok_parsed_fields()
    test_harness_skill_order_is_pstack_then_user_then_native()
    print("PASS tests/test_verify_harness.py")
