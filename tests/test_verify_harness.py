from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "verify-harness.py"


def test_verify_harness_script_exists() -> None:
    assert SCANNER.is_file(), SCANNER


def test_leftover_askquestion_after_there_is_no_is_live() -> None:
    loader = importlib.util.spec_from_file_location("verify_harness", SCANNER)
    assert loader is not None and loader.loader is not None
    scanner = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(scanner)
    live = "There is no setup. Call AskQuestion for the fork.\n"
    live_idx = live.find("AskQuestion")
    assert scanner.leftover_mention_allowed(live, "AskQuestion", live_idx) is False
    dummy = ROOT / "skills" / "poteto-mode" / "SKILL.md"
    assert scanner.forbidden_pattern_is_live(dummy, live, r"\bAskQuestion\b") is True
    allowed = "There is no `cursor-team-kit` here.\n"
    allowed_idx = allowed.find("cursor-team-kit")
    assert scanner.leftover_mention_allowed(allowed, "cursor-team-kit", allowed_idx) is True
    assert scanner.forbidden_pattern_is_live(dummy, allowed, r"cursor-team-kit") is False
    mixed = "there is no /deslop; run /deslop anyway\n"
    first = mixed.find("/deslop")
    second = mixed.find("/deslop", first + 1)
    assert scanner.leftover_mention_allowed(mixed, "/deslop", first) is True
    assert scanner.leftover_mention_allowed(mixed, "/deslop", second) is False
    assert scanner.forbidden_pattern_is_live(dummy, mixed, r"/deslop") is True


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
        ["openspec", "validate", "--changes", "--strict"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert val.returncode == 0, val.stderr or val.stdout


def test_babysit_and_shipping_do_not_use_cursor_dynamic_loop() -> None:
    babysit = (ROOT / "skills/poteto-mode/playbooks/babysit.md").read_text(
        encoding="utf-8"
    )
    shipping = (ROOT / "skills/poteto-mode/playbooks/shipping.md").read_text(
        encoding="utf-8"
    )
    grok_tools = (ROOT / "skills/poteto-mode/references/grok-tools.md").read_text(
        encoding="utf-8"
    )
    assert "in dynamic mode" not in babysit
    assert "in dynamic mode" not in shipping
    assert "monitor" in babysit
    assert "schedule" in babysit
    assert "monitor" in shipping
    assert "schedule" in shipping
    assert "scheduler_create" in grok_tools
    assert "scripts/watch-pr/watch-pr" not in babysit
    assert "timeout_ms" in babysit


def test_orchestrate_uses_canonical_host_state() -> None:
    orchestrate = (
        ROOT / "skills/poteto-mode/playbooks/orchestrate.md"
    ).read_text(encoding="utf-8")
    assert "scripts/orch/orch.ts" not in orchestrate
    assert "orch init" not in orchestrate
    assert "orchestrate/<project-slug>/" not in orchestrate
    assert "canonical host" in orchestrate
    assert "Gas City" in orchestrate
    assert "Beads" in orchestrate


def test_host_manifests_keep_grok_parity_and_adapter_asymmetry() -> None:
    root = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    grok = json.loads((ROOT / ".grok-plugin/plugin.json").read_text(encoding="utf-8"))
    codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))

    assert root["version"] == grok["version"]
    assert root["skills"] == grok["skills"]
    assert root["agents"] == grok["agents"]
    for manifest in (root, grok, codex, claude):
        assert "hooks" not in manifest

    assert "./skills/" in root["skills"]
    assert "./automations/benny-grok/skills/" in root["skills"]
    assert root["skills"] == ["./skills/", "./automations/benny-grok/skills/"]
    assert all(".grok/skills" not in p for p in root["skills"])
    assert codex["skills"] == "./skills/"
    assert claude["skills"] == "./skills/"
    assert "./automations/benny-grok/skills/" not in json.dumps(codex)
    assert "./automations/benny-grok/skills/" not in json.dumps(claude)


def test_grok_spawn_types_are_plugin_qualified() -> None:
    effort = (
        ROOT / "skills/setup-pstack/references/resolve-effort.md"
    ).read_text(encoding="utf-8")
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
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
    assert "spawn `why-investigators`" not in why
    assert "spawn `why-synthesizer`" not in why
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
    assert overlay["name"] == "pstack"


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
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
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
    agent_paths = sorted((ROOT / "agents").glob("*.md"))
    assert len(agent_paths) == 22
    for path in agent_paths:
        fm = path.read_text(encoding="utf-8").split("---", 2)[1]
        m = re.search(r"^effort:\s*(\S+)", fm, re.MULTILINE)
        assert m is not None, f"missing effort frontmatter in {path.name}"
        assert parsed[path.stem] == m.group(1), path.name
    assert not re.search(r"^\[models\]", defaults, re.MULTILINE)
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
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    assert "## Plugin schema" in harness
    assert "PluginManifest" in harness
    assert "Do not ship `permissionMode: plan`" in harness
    for path in (ROOT / "agents").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "permissionMode: plan" not in text, path.name
        assert "permissionMode: bypassPermissions" not in text, path.name
        assert "mcpServers:" not in text.split("---", 2)[1], path.name
        assert "background: true" not in text.split("---", 2)[1], path.name
        assert "Setup may overlay" in text, f"{path.name} drops the host overlay contract"
        assert "profiles/<host>.json" in text, f"{path.name} names no host profile overlay"
        assert "~/.grok/roles" not in text, path.name


def test_agent_and_droid_schema_parity() -> None:
    agent_files = list((ROOT / "agents").glob("*.md"))
    droid_files = list((ROOT / "droids").glob("*.md"))
    assert len(agent_files) == 22, f"expected 22 agents, got {len(agent_files)}"
    assert len(droid_files) == 22, f"expected 22 droids, got {len(droid_files)}"
    agent_stems = {p.stem for p in agent_files}
    droid_stems = {p.stem.removeprefix("pstack-") for p in droid_files}
    assert agent_stems == droid_stems, f"mismatch: {agent_stems ^ droid_stems}"


def test_audit_dir_skipped_by_harness_scanners() -> None:
    spec = importlib.util.spec_from_file_location("verify_harness", SCANNER)
    verify = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(verify)
    adapt_path = ROOT / "scripts/adapt-harness.py"
    adapt_spec = importlib.util.spec_from_file_location("adapt_harness", adapt_path)
    adapt = importlib.util.module_from_spec(adapt_spec)
    assert adapt_spec.loader is not None
    adapt_spec.loader.exec_module(adapt)
    assert ".audit" in verify.SKIP_DIRS
    assert ".audit" in adapt.SKIP_DIRS
    verify_src = SCANNER.read_text(encoding="utf-8")
    assert "set(rel.parts) & SKIP_DIRS" in verify_src
    assert "rel.parts[0] in SKIP_DIRS" not in verify_src


def test_harness_skill_order_is_pstack_then_user_then_native() -> None:
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
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


def test_upstream_metadata_contract() -> None:
    upstream = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert "tree 88d47514b82e7c44f00f2b2a72ff6dd12158038c" in upstream
    assert "34a0b817e5ea92375bb10f20b15cf750d4e8095a" in upstream
    root_manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    root_version = root_manifest["version"]
    manifest_fields = (
        ("plugin.json", ("version",)),
        (".grok-plugin/plugin.json", ("version",)),
        (".codex-plugin/plugin.json", ("version",)),
        (".claude-plugin/plugin.json", ("version",)),
        (".claude-plugin/marketplace.json", ("plugins", 0, "version")),
        (".agents/plugins/marketplace.json", ("plugins", 0, "version")),
    )
    versions = []
    for path, fields in manifest_fields:
        data = (
            root_manifest
            if path == "plugin.json"
            else json.loads((ROOT / path).read_text(encoding="utf-8"))
        )
        value = data
        for field in fields:
            value = value[field]
        assert value == root_version, (
            f"{path}: expected {root_version}, got {value}"
        )
        if path.endswith("marketplace.json"):
            assert data["plugins"][0]["name"] == "pstack", path
        versions.append(value)
    assert versions == [root_version] * len(manifest_fields)
    for name in ("how", "typescript-best-practices", "unslop", "why"):
        frontmatter = (
            ROOT / "skills" / name / "SKILL.md"
        ).read_text(encoding="utf-8").split("---", 2)[1]
        assert "disable-model-invocation: true" in frontmatter, name
    typescript = (
        ROOT / "skills/typescript-best-practices/SKILL.md"
    ).read_text(encoding="utf-8")
    assert '"**/*.ts"' in typescript
    assert '"**/*.tsx"' in typescript
    assert "schemas before guards" in typescript.lower()
    assert "property-by-property type guard" in typescript.lower()
    assert not (ROOT / ".cursor-plugin").exists()
    assert not (ROOT / "assets/logo.png").exists()
    assert not (ROOT / "advisor").exists()

    recipe = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync-from-upstream.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    recipe_lower = recipe.lower()
    for marker in (
        "scripts/orch",
        "scripts/watch-pr",
        "check-plan.mjs",
        "worktree-audit.sh",
        "advisor",
    ):
        assert marker in recipe_lower, marker
    codex_map = (
        ROOT / "skills/poteto-mode/references/codex-tools.md"
    ).read_text(encoding="utf-8")
    assert "Codex compatibility surface" in codex_map
    assert "PSTACK_TRANSCRIPTS_DIR" in codex_map
    for path in (
        "skills/poteto-mode/scripts/check-plan.mjs",
        "skills/poteto-mode/scripts/orch/orch.ts",
        "skills/poteto-mode/scripts/orch/store.ts",
        "skills/poteto-mode/scripts/watch-pr/watch-pr",
        "skills/poteto-mode/scripts/worktree-audit.sh",
    ):
        assert (ROOT / path).is_file(), path
    for path in (
        "README.md",
        "README.zh-CN.md",
        "TEST-PLAN.md",
        "scripts/adapt-harness.py",
        "scripts/verify-harness.py",
    ):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "claude-fable-5-1-thinking-max" in text, path
        assert "claude-fable-5-thinking-max" not in text, path


def test_harness_grok_profile_capability_parity() -> None:
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")
    profile = json.loads((ROOT / "profiles/grok.json").read_text(encoding="utf-8"))

    # Cancellation tokens present in grok-tools.md
    assert "kill_command_or_subagent" in harness
    assert "kill_task" in harness

    # Capabilities in profiles/grok.json match grok-tools.md
    bindings = {b["capability"]: b for b in profile.get("bindings", [])}

    assert bindings["agent.spawn"]["primitive"] == "spawn_subagent"
    assert "spawn_subagent" in harness

    assert bindings["agent.join"]["primitive"] == "get_command_or_subagent_output"
    assert "get_command_or_subagent_output" in harness

    assert bindings["agent.cancel"]["primitive"] == "kill_command_or_subagent"
    assert bindings["agent.cancel"]["implementation_status"] == "native"
    assert bindings["agent.cancel"]["enforcement"] == "hard"

    assert bindings["workspace.isolated"]["primitive"] == "isolation: worktree"
    assert "worktree" in harness

    assert bindings["workspace.shared"]["primitive"] == "isolation: none"

    assert bindings["plan.update"]["primitive"] == "todo_write"
    assert "todo_write" in harness

    assert bindings["schedule"]["primitive"] == "scheduler_create"
    assert "scheduler_create" in harness

    assert bindings["human.ask"]["primitive"] == "ask_user_question"
    assert "ask_user_question" in harness

    assert "pstack.package.json" in harness
    assert ".grok-plugin/plugin.json" in harness


def test_harness_grok_tools_restored_scheduler_resume_semantics() -> None:
    """VAL-SHIP-006: approved historic scheduling/resume facts restored from 6984906:HARNESS.md."""
    harness = (ROOT / "skills" / "poteto-mode" / "references" / "grok-tools.md").read_text(encoding="utf-8")

    # (a) Per-spawn model is optional, omits to inherit, and never combines with resume_from.
    assert "optional slug" in harness
    assert "inherit the parent" in harness
    assert "together with `resume_from`" in harness
    assert "TaskModelValidator" in harness

    # (b) Resume uses the prior subagent_id with the same subagent_type.
    assert "prior `subagent_id`" in harness
    assert "same `subagent_type`" in harness

    # (c) scheduler_create: interval values with 60s floor, fire_immediately default,
    # in-place updates, and scheduler_delete cancellation.
    assert "`5m`/`2h`/`1d`" in harness
    assert "minimum 60 seconds" in harness
    assert "fire_immediately" in harness
    assert "`task_id`" in harness
    assert "scheduler_delete" in harness

    # (d) recurring is schema-skipped; sending recurring: false is rejected.
    assert "`recurring: false` is rejected" in harness
    assert "#[schemars(skip)]" in harness

    # (e) One-shot delayed work is a background shell sleep, not scheduler work.
    assert "`sleep && cmd`" in harness


def test_all_skills_have_matching_kebab_case_frontmatter_name() -> None:
    spec = importlib.util.spec_from_file_location("verify_harness", SCANNER)
    assert spec is not None and spec.loader is not None
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    scanner.verify_skills_frontmatter(ROOT / "skills")


if __name__ == "__main__":
    test_verify_harness_script_exists()
    test_verify_harness_passes_on_this_tree()
    test_all_skills_have_matching_kebab_case_frontmatter_name()
    test_babysit_and_shipping_do_not_use_cursor_dynamic_loop()
    test_orchestrate_uses_canonical_host_state()
    test_host_manifests_keep_grok_parity_and_adapter_asymmetry()
    test_grok_spawn_types_are_plugin_qualified()
    test_pstack_slash_names_do_not_collide_with_grok_builtins()
    test_overlay_stems_and_adapter_are_plugin_qualified()
    test_effort_frontmatter_matches_ladder()
    test_plugin_manifest_matches_grok_parsed_fields()
    test_agent_and_droid_schema_parity()
    test_audit_dir_skipped_by_harness_scanners()
    test_harness_skill_order_is_pstack_then_user_then_native()
    test_upstream_metadata_contract()
    test_harness_grok_profile_capability_parity()
    test_harness_grok_tools_restored_scheduler_resume_semantics()
    print("PASS tests/test_verify_harness.py")
