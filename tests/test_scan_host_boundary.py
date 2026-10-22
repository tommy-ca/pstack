import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scan-host-boundary.py"
PROFILES_DIR = ROOT / "profiles"
BOUNDARY_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "boundary"

loader = importlib.util.spec_from_file_location("scan_host_boundary", SCRIPT)
assert loader is not None and loader.loader is not None
scan_host_boundary = importlib.util.module_from_spec(loader)
sys.modules["scan_host_boundary"] = scan_host_boundary
loader.loader.exec_module(scan_host_boundary)

extract_forbidden_vocabulary = scan_host_boundary.extract_forbidden_vocabulary
run_scan = scan_host_boundary.run_scan
scan_file = scan_host_boundary.scan_file
is_exempt = scan_host_boundary.is_exempt
main = scan_host_boundary.main

VOCAB = extract_forbidden_vocabulary(PROFILES_DIR)
REVIEWED = scan_host_boundary.REVIEWED_PROHIBITIONS[0]
REAL_SKILL = ROOT / REVIEWED.path


def _fixture(tmp_path: Path, rel_path: str, text: str) -> Path:
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _reviewed_line(root: Path = ROOT) -> str:
    """The real SKILL.md line carrying the reviewed prohibition, found by content."""
    return next(
        line
        for line in (root / REVIEWED.path).read_text(encoding="utf-8").splitlines()
        if REVIEWED.sentence in line
    )



def test_clean_tree_passes():
    """The clean repository tree must have zero host boundary leaks."""
    vocab, violations, count = run_scan(ROOT, PROFILES_DIR)
    assert len(vocab) >= 20
    assert count >= 130
    assert violations == [], f"Found unexpected violations: {violations}"


def test_agents_and_droids_scanned_without_violations():
    """Agents and droids directories must be scanned with zero violations."""
    vocab, violations, count = run_scan(ROOT, PROFILES_DIR, target_dirs=[ROOT / "agents", ROOT / "droids"])
    assert count == 44
    assert violations == []


def test_dynamic_vocabulary_extraction():
    """Vocabulary must dynamically extract primitives and default models from profiles."""
    vocab = extract_forbidden_vocabulary(PROFILES_DIR)
    assert "grok-4.6" in vocab
    assert "spawn_subagent" in vocab
    assert "pi_spawn" in vocab
    assert "task.spawn" in vocab
    assert "spawn_agent" in vocab
    assert "scheduler_create" in vocab
    assert "MAX_SUBAGENT_DEPTH" in vocab


def test_declared_paths_come_from_plugins_dir_and_setup_block():
    """plugins_dir always; setup.catalog and setup.overlay only when declared."""
    vocab = extract_forbidden_vocabulary(BOUNDARY_FIXTURES / "profiles")
    assert {
        "~/.overlay-host/plugins",
        "~/.overlay-host/pstack-models.toml",
        "~/.overlay-host/roles",
        "~/.plain-host/plugins",
    } <= set(vocab)
    assert "~/.plain-host/pstack-models.toml" not in vocab


def test_declared_setup_overlay_flags_a_shared_surface(tmp_path: Path) -> None:
    """An overlay a profile declares is a host write target the gate catches."""
    vocab = extract_forbidden_vocabulary(BOUNDARY_FIXTURES / "profiles")
    f = _fixture(
        tmp_path,
        "skills/sample/SKILL.md",
        "Write `~/.overlay-host/roles/pstack:feature.toml` with every role.\n",
    )
    assert [v.token for v in scan_file(f, tmp_path, vocab)] == ["~/.overlay-host/roles"]


def test_detects_forbidden_primitives_in_fixture(tmp_path: Path):
    """The scanner must detect forbidden primitives when present in a portable file."""
    vocab = extract_forbidden_vocabulary(PROFILES_DIR)
    test_file = tmp_path / "skills" / "sample" / "SKILL.md"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(
        """# Sample Skill
1. Use spawn_subagent to start a worker.
2. Ten lanes on `grok-4.6` at the PR head.
3. Arm scheduler_create as heartbeat.
4. Also try pi_spawn or task.spawn.
""",
        encoding="utf-8",
    )

    violations = scan_file(test_file, tmp_path, vocab)
    tokens_found = {v.token for v in violations}
    assert "spawn_subagent" in tokens_found
    assert "grok-4.6" in tokens_found
    assert "scheduler_create" in tokens_found
    assert "pi_spawn" in tokens_found
    assert "task.spawn" in tokens_found
    assert len(violations) == 5


def test_typed_exemptions():
    """Exemptions must protect adapter references, profiles, and tests while leaving skills unexempt."""
    assert is_exempt("skills/poteto-mode/references/grok-tools.md") is not None
    assert is_exempt("skills/setup-pstack/SKILL.md") is not None
    assert is_exempt("profiles/grok.json") is not None
    assert is_exempt("tests/test_scan_host_boundary.py") is not None
    assert is_exempt("scripts/scan-host-boundary.py") is not None
    assert is_exempt("skills/poteto-mode/scripts/node_modules/typescript/README.md") is not None

    # Portable shared surfaces must NOT be exempt
    assert is_exempt("skills/poteto-mode/SKILL.md") is None
    assert is_exempt("skills/poteto-mode/playbooks/feature.md") is None
    assert is_exempt("skills/swarm/SKILL.md") is None
    assert is_exempt("schemas/portability/binding.schema.json") is None


def test_cli_execution():
    """The scanner CLI must exit 0 on the clean codebase with --check."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scan-host-boundary.py"), "--check", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "violations_count" in proc.stdout
    assert '"violations_count": 0' in proc.stdout


def test_cli_exits_1_on_a_leak(tmp_path: Path, monkeypatch, capsys):
    """The CLI contract: --check turns a violation into a non-zero exit."""
    tree = tmp_path / "tree"
    (tree / "skills" / "sample").mkdir(parents=True)
    (tree / "skills" / "sample" / "SKILL.md").write_text("Call spawn_subagent.\n", encoding="utf-8")
    monkeypatch.setattr(scan_host_boundary, "ROOT", tree)
    monkeypatch.setattr(sys, "argv", ["scan-host-boundary.py", "--check", "--json"])
    assert main() == 1
    assert '"violations_count": 1' in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["scan-host-boundary.py", "--no-check", "--json"])
    assert main() == 0
    assert '"violations_count": 1' in capsys.readouterr().out


def test_corrupt_profile_aborts_the_scan(tmp_path: Path):
    """A profile the gate cannot parse is a named error, never a silent vocabulary gap."""
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "broken.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(scan_host_boundary.BoundaryInputError, match="broken.json"):
        extract_forbidden_vocabulary(profiles)


def test_cli_aborts_on_a_corrupt_profile(tmp_path: Path, monkeypatch, capsys):
    """The CLI reports the corrupt input by name and exits 2, not 0."""
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "bad.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(scan_host_boundary, "PROFILES_DIR", profiles)
    monkeypatch.setattr(sys, "argv", ["scan-host-boundary.py"])
    assert main() == 2
    captured = capsys.readouterr()
    assert "bad.json" in captured.err


def test_unreadable_in_scope_file_aborts_the_scan(tmp_path: Path):
    """An in-scope file the gate cannot read is a named error, never a pass."""
    target = tmp_path / "skills" / "sample" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.mkdir()
    with pytest.raises(scan_host_boundary.BoundaryInputError, match="SKILL.md"):
        scan_file(target, tmp_path, {})


def test_install_path_flags_shared_surface_without_prohibition(tmp_path: Path) -> None:
    """A host install path action on a shared surface is a violation, no intent needed."""
    f = tmp_path / "skills" / "sample" / "SKILL.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("Open `~/.grok/installed-plugins/pstack-foo/skills/x/SKILL.md` to route.\n", encoding="utf-8")
    vs = scan_file(f, tmp_path, extract_forbidden_vocabulary(PROFILES_DIR))
    assert any(v.token == "~/.grok/installed-plugins" for v in vs)


def test_negated_install_path_still_flags(tmp_path: Path) -> None:
    """#707's own repro: a negated install-path sentence is flagged outside the carve-out."""
    f = tmp_path / "skills" / "poteto-mode" / "SKILL.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("Do not open `~/.grok/installed-plugins/pstack-foo/skills/x/`.\n", encoding="utf-8")
    vs = scan_file(f, tmp_path, extract_forbidden_vocabulary(PROFILES_DIR))
    assert any(v.token == "~/.grok/installed-plugins" for v in vs)


def test_reviewed_prohibition_passes_wherever_it_sits(tmp_path: Path) -> None:
    """The carve-out follows the sentence, so moving it within the file changes nothing."""
    real_line = _reviewed_line()
    assert REVIEWED.sentence in real_line
    for filler in (0, 400):
        root = tmp_path / f"shifted-{filler}"
        f = _fixture(root, REVIEWED.path, "\n".join(["f"] * filler + [real_line]) + "\n")
        assert scan_file(f, root, VOCAB) == [], f"verdict changed after {filler} filler lines"


def test_reworded_reviewed_prohibition_fails_closed(tmp_path: Path) -> None:
    """Drifting the reviewed sentence is a violation, not a crash and not a pass."""
    reworded = REVIEWED.sentence.replace("Do not open", "Never open")
    f = _fixture(tmp_path, REVIEWED.path, reworded + "\n")
    assert [v.token for v in scan_file(f, tmp_path, VOCAB)] == ["~/.grok/installed-plugins"]


def test_reviewed_prohibition_excuses_only_its_own_host_path() -> None:
    """The reviewed sentence may not smuggle a second kind of host vocabulary past the gate."""
    assert [token for token in VOCAB if token in REVIEWED.sentence] == ["~/.grok/installed-plugins"]


def test_prefixed_install_path_before_prohibition_still_flags(tmp_path: Path) -> None:
    """A second actionable path ahead of the reviewed sentence is not suppressed."""
    real_line = _reviewed_line()
    f = _fixture(
        tmp_path,
        REVIEWED.path,
        "Open `~/.grok/installed-plugins/evil/` to route. " + real_line + "\n",
    )
    vs = scan_file(f, tmp_path, VOCAB)
    assert [v.token for v in vs] == ["~/.grok/installed-plugins"]


def test_moving_lines_never_changes_the_verdict(tmp_path: Path) -> None:
    """Every verdict is content-addressed: prepending lines only shifts line numbers."""
    body = ["Head", "Start each lane with spawn_subagent.", "Ten lanes on `grok-4.6`.", "Tail"]
    first = _fixture(tmp_path / "a", "skills/sample/SKILL.md", "\n".join(body) + "\n")
    moved = _fixture(tmp_path / "b", "skills/sample/SKILL.md", "\n".join(["", ""] + body) + "\n")
    before = [(v.line_number, v.token) for v in scan_file(first, tmp_path / "a", VOCAB)]
    after = [(v.line_number, v.token) for v in scan_file(moved, tmp_path / "b", VOCAB)]

    assert [token for _, token in before] == [token for _, token in after]
    assert [line for line, _ in after] == [line + 2 for line, _ in before]


def test_portable_router_selects_the_active_host_not_grok() -> None:
    """Shared router must not impose Grok setup or skill order on other hosts."""
    router = (ROOT / "skills/poteto-mode/SKILL.md").read_text(encoding="utf-8")
    skill_order = router.split("- **Skill order.**", 1)[1].split("\n", 1)[0]
    assert "profiles/<host>.json" in skill_order
    assert "references/<host>-tools.md" in skill_order
    assert "current host" in skill_order
    for inherited_default in (
        "profiles/grok.json",
        "references/grok-tools.md",
        "~/.grok/skills",
        "Grok Build's",
        "Grok Build:",
    ):
        assert inherited_default not in router, inherited_default
    assert "playbooks/authoring-a-skill.md" in router
    assert "undeclared or unproven native capability is a GAP" in router


def test_grok_setup_is_explicitly_adapter_scoped() -> None:
    """A shared skill name may expose Grok setup only with a visible native guard."""
    setup = (ROOT / "skills/setup-pstack/SKILL.md").read_text(encoding="utf-8")
    assert "**Host scope: Grok Build adapter only.**" in setup
    assert "do not run Grok probes or create `~/.grok/` files" in setup
    assert "profiles/<host>.json" in setup


def test_legacy_grok_doctor_does_not_claim_native_host_proof() -> None:
    doctor = (ROOT / "scripts/verify-harness.py").read_text(encoding="utf-8")
    tiers = (ROOT / "docs/verification-test-tiers.md").read_text(encoding="utf-8")
    maintain = (ROOT / "skills/maintain-verification-skill/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "static doctor for shared pstack structure and Grok adapter compatibility" in doctor
    assert "NOT a six-host native conformance verdict" in doctor
    assert "Legacy Grok doctor is not cross-host runtime proof" in tiers
    assert "thermo-nuclear-review" in maintain
    assert "thermo-nuclear-code-quality-review" in maintain
    assert "independent verifier has not actually checked the current patch" in maintain



@pytest.mark.parametrize(
    "line, token",
    [
        (
            "Open `~/.grok/installed-plugins/pstack-x/skills/a/SKILL.md` before editing.",
            "~/.grok/installed-plugins",
        ),
        ("Route verification work to Grok Build.", "Grok Build"),
        ("Start each lane with spawn_subagent.", "spawn_subagent"),
        ("Ten lanes on `grok-4.6` at the PR head.", "grok-4.6"),
    ],
)
def test_the_gate_fails_on_each_kind_of_host_detail(tmp_path: Path, line: str, token: str) -> None:
    """Install path, routing directive, host primitive and concrete model each fail a fixture."""
    f = _fixture(tmp_path, "skills/sample/SKILL.md", line + "\n")
    assert token in {v.token for v in scan_file(f, tmp_path, VOCAB)}


@pytest.mark.parametrize(
    "line",
    [
        "Route verification work to Grok Build.",
        "Use Grok Build to author the skill.",
        "hand to Grok Build's `/create-skill` and run its loop.",
        "Fall back to Grok Build when the lane stalls.",
        "Send the failing diff via Grok Build.",
    ],
)
def test_a_bare_host_routing_directive_flags(tmp_path: Path, line: str) -> None:
    """Any clause that sends work to a host is a leak, including the possessive form."""
    f = _fixture(tmp_path, "skills/sample/SKILL.md", line + "\n")
    assert [v.token for v in scan_file(f, tmp_path, VOCAB)] == ["Grok Build"]


@pytest.mark.parametrize(
    "line",
    [
        "Grok Build's `/create-skill`: skill authoring process and writing guidelines.",
        "Every host, including Grok Build, reads `profiles/<host>.json`.",
        "Do not route work to Grok Build.",
        "Do not open the installed copy; read `skills/poteto-mode/playbooks/` instead.",
    ],
)
def test_a_host_mention_is_not_a_routing_directive(tmp_path: Path, line: str) -> None:
    """A mention, a comparison and a negated instruction are not leaks."""
    f = _fixture(tmp_path, "skills/sample/SKILL.md", line + "\n")
    assert scan_file(f, tmp_path, VOCAB) == []


@pytest.mark.parametrize(
    "line",
    [
        "Do not read the installed copy. Hand the review to Grok Build.",
        "Do not use host emulation. Open Grok Build plugins first.",
    ],
)
def test_a_negation_does_not_whitewash_a_later_directive(
    tmp_path: Path, line: str
) -> None:
    """Negation is clause-scoped: a directive in another clause still flags."""
    f = _fixture(tmp_path, "skills/sample/SKILL.md", line + "\n")
    assert [v.token for v in scan_file(f, tmp_path, VOCAB)] == ["Grok Build"]
