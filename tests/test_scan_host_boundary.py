import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scan-host-boundary.py"
PROFILES_DIR = ROOT / "profiles"

loader = importlib.util.spec_from_file_location("scan_host_boundary", SCRIPT)
assert loader is not None and loader.loader is not None
scan_host_boundary = importlib.util.module_from_spec(loader)
sys.modules["scan_host_boundary"] = scan_host_boundary
loader.loader.exec_module(scan_host_boundary)

extract_forbidden_vocabulary = scan_host_boundary.extract_forbidden_vocabulary
run_scan = scan_host_boundary.run_scan
scan_file = scan_host_boundary.scan_file
is_exempt = scan_host_boundary.is_exempt



def test_clean_tree_passes():
    """The clean repository tree must have zero host boundary leaks."""
    vocab, violations, count = run_scan(ROOT, PROFILES_DIR)
    assert len(vocab) >= 20
    assert count >= 50
    assert violations == [], f"Found unexpected violations: {violations}"


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
