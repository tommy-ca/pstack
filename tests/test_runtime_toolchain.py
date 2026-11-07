import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
    assert "verify:portable" in tasks, "mise.toml must declare verify:portable task"
    assert "verify:lifecycle" in tasks, "mise.toml must declare verify:lifecycle task"
    assert "verify:sync" in tasks, "mise.toml must declare verify:sync task"


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
