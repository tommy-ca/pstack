import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_mise_toml_configuration() -> None:
    mise_path = ROOT / "mise.toml"
    assert mise_path.is_file(), "mise.toml must exist at repo root"

    with open(mise_path, "rb") as f:
        data = tomllib.load(f)

    assert "tools" in data, "mise.toml must declare tools"
    tools = data["tools"]
    assert tools.get("bun") == "1.4.4", "bun must be pinned in mise.toml"
    assert tools.get("python") == "3.12", "python must be pinned to 3.12 in mise.toml"
    assert tools.get("uv") == "0.13.7", "uv must be pinned in mise.toml"

    assert "tasks" in data, "mise.toml must declare tasks"
    tasks = data["tasks"]
    assert "test" in tasks, "mise.toml must declare test task"
    assert "test:offline" in tasks, "mise.toml must declare test:offline task"
    assert "test:scripts" in tasks, "mise.toml must declare test:scripts task"
    assert "plan:check" in tasks, "mise.toml must declare plan:check task"
    assert "verify:openspec" in tasks, "mise.toml must provide strict OpenSpec validation"
    assert "openspec:status" in tasks, "mise.toml must provide read-only intent flow inspection"
    assert "openspec_change.py verify" in tasks["verify:openspec"]["run"]
    assert "openspec_change.py --status --json" in tasks["openspec:status"]["run"]
    assert "verify:portable" in tasks, "mise.toml must declare verify:portable task"
    assert "verify:lifecycle" in tasks, "mise.toml must declare verify:lifecycle task"
    assert "verify:sync" in tasks, "mise.toml must declare verify:sync task"
    assert "verify:doctor" in tasks, "mise.toml must declare verify:doctor task"
    assert "verify:staleness" in tasks, "mise.toml must declare verify:staleness task"
    assert "verify:projection" in tasks, "mise.toml must declare verify:projection task"
    assert "verify:skills" in tasks, "mise.toml must declare verify:skills task"
    assert "verify:doctor:skills" in tasks, "mise.toml must declare verify:doctor:skills task"
    assert tasks["verify:doctor:skills"]["run"] == "uv run python scripts/scaffold_verification_skill.py --doctor-all"
    assert "verify:cleanup:skills" in tasks, "mise.toml must declare verify:cleanup:skills task"
    assert tasks["verify:cleanup:skills"]["run"] == "uv run python scripts/scaffold_verification_skill.py --cleanup-all"
    assert "verify:drivers" in tasks, "mise.toml must declare verify:drivers task"
    assert tasks["verify:drivers"]["run"] == "uv run python scripts/scaffold_verification_skill.py --drive-all"
    assert "worktree:check" in tasks, "mise.toml must declare worktree:check task"
    assert "worktree:audit" in tasks, "mise.toml must declare worktree:audit task"


def test_release_workflow_uses_uv() -> None:
    release_path = ROOT / ".github" / "workflows" / "release.yml"
    assert release_path.is_file(), "release.yml must exist"
    content = release_path.read_text(encoding="utf-8")
    assert "astral-sh/setup-uv" in content, "release.yml must set up uv"
    assert "uv run python" in content, "release.yml must use uv run python"


def test_driver_template_runtime_contracts() -> None:
    from scripts.verification_skill_templates import generate_driver_script
    script = generate_driver_script("test-app")
    assert 'PYTHON_EXEC="uv run python"' in script
    assert 'BUN_EXEC="bun"' in script



def test_mise_lockfile_exists() -> None:
    mise_lock = ROOT / "mise.lock"
    assert mise_lock.is_file(), "mise.lock must exist at repo root"
    content = mise_lock.read_text(encoding="utf-8")
    assert "bun" in content, "bun must be locked in mise.lock"
    assert "python" in content, "python must be locked in mise.lock"
    assert "uv" in content, "uv must be locked in mise.lock"


def test_pyproject_toml_configuration() -> None:
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist at repo root"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    assert project.get("name") == "pstack"
    assert project.get("requires-python") == ">=3.12"
    deps = project.get("dependencies", [])
    assert any(d.startswith("pytest") for d in deps), "pytest must be a dependency"
    assert any(d.startswith("jsonschema") for d in deps), "jsonschema must be a dependency"

    tool_uv = data.get("tool", {}).get("uv", {})
    assert tool_uv.get("package") is False, "tool.uv.package must be false for virtual workspace"


def test_uv_lockfile_exists() -> None:
    uv_lock = ROOT / "uv.lock"
    assert uv_lock.is_file(), "uv.lock must exist at repo root"
    content = uv_lock.read_text(encoding="utf-8")
    assert 'name = "pytest"' in content, "pytest must be in uv.lock"
    assert 'name = "jsonschema"' in content, "jsonschema must be in uv.lock"
