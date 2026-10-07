"""Executable lookup and shim dispatch from isolated directories."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import CodexDriver, DroidDriver
from scripts.drivers.base import find_executable


@pytest.fixture
def dispatcher(tmp_path: Path) -> Path:
    binary = tmp_path / "dispatcher"
    binary.write_text('#!/bin/sh\nprintf "%s-fixture 1.0\\n" "${0##*/}"\n')
    binary.chmod(0o755)
    return binary


@pytest.mark.parametrize("name", ["codex", "droid"])
@pytest.mark.parametrize("route", ["PATH", "direct", "recursive"])
@pytest.mark.parametrize("relative", [False, True])
def test_find_executable_preserves_absolute_shim_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatcher: Path,
    name: str, route: str, relative: bool,
) -> None:
    physical = tmp_path / "physical directory"
    physical.mkdir()
    alias = tmp_path / "shim directory"
    alias.symlink_to(physical, target_is_directory=True)
    shim = alias / ("nested/version" if route == "recursive" else "") / name
    shim.parent.mkdir(parents=True, exist_ok=True)
    shim.symlink_to(dispatcher)
    execution_dir = tmp_path / "execution"
    execution_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    search_dir = alias.relative_to(tmp_path) if relative else alias
    monkeypatch.setenv("PATH", str(search_dir) if route == "PATH" else "")

    selected = find_executable(name, [] if route == "PATH" else [search_dir])

    assert selected == shim
    result = subprocess.run(
        [str(selected), "--version"], cwd=execution_dir,
        capture_output=True, text=True, check=True,
    )
    assert result.stdout == f"{name}-fixture 1.0\n"


@pytest.mark.parametrize("driver_class,name", [(CodexDriver, "codex"), (DroidDriver, "droid")])
@pytest.mark.parametrize("path_entry", ["bin", ".", "absolute"])
def test_driver_executes_path_shim_from_different_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatcher: Path,
    driver_class, name: str, path_entry: str,
) -> None:
    caller = tmp_path / "caller"
    caller.mkdir()
    directory = caller if path_entry == "." else caller / "bin"
    directory.mkdir(exist_ok=True)
    shim = directory / name
    shim.symlink_to(dispatcher)
    execution_dir = tmp_path / "execution"
    execution_dir.mkdir()
    monkeypatch.chdir(caller)
    monkeypatch.setenv("PATH", str(directory) if path_entry == "absolute" else path_entry)

    driver = driver_class(execution_dir)

    assert driver.is_available()[0] is True
    assert driver.get_version() == f"{name}-fixture 1.0"
    assert driver.get_binary_path() == shim


@pytest.mark.parametrize("driver_class,name,install_dir", [
    (CodexDriver, "codex", ".local/share/mise/installs"),
    (CodexDriver, "codex", ".local/bin"),
    (DroidDriver, "droid", ".local/bin"),
    (DroidDriver, "droid", ".factory/bin"),
])
@pytest.mark.parametrize("recursive", [False, True])
def test_driver_executes_fallback_shim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatcher: Path,
    driver_class, name: str, install_dir: str, recursive: bool,
) -> None:
    fixture_home = tmp_path / "fixture home"
    shim = fixture_home / install_dir / ("nested/version" if recursive else "") / name
    shim.parent.mkdir(parents=True)
    shim.symlink_to(dispatcher)
    execution_dir = tmp_path / "execution"
    execution_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fixture_home)
    monkeypatch.setenv("PATH", "")

    driver = driver_class(execution_dir)

    assert driver.get_version() == f"{name}-fixture 1.0"
    assert driver.get_binary_path() == shim


def test_find_executable_preserves_search_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatcher: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    nested = first / "nested"
    nested.mkdir(parents=True)
    second.mkdir()
    direct = first / "codex"
    direct.symlink_to(dispatcher)
    (nested / "codex").symlink_to(dispatcher)
    (second / "codex").symlink_to(dispatcher)
    monkeypatch.setenv("PATH", str(second))

    assert find_executable("codex", [first]) == second / "codex"
    monkeypatch.setenv("PATH", "")
    assert find_executable("codex", [first, second]) == direct
    assert find_executable("codex", [tmp_path / "missing", second, first]) == second / "codex"


@pytest.mark.parametrize("invalid", ["broken", "non-executable", "directory"])
def test_find_executable_skips_invalid_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatcher: Path, invalid: str,
) -> None:
    candidate = tmp_path / "codex"
    if invalid == "broken":
        candidate.symlink_to(tmp_path / "absent")
    elif invalid == "non-executable":
        candidate.write_text("#!/bin/sh\nexit 0\n")
        candidate.chmod(0o644)
    else:
        candidate.mkdir()
    monkeypatch.setenv("PATH", str(tmp_path))
    assert find_executable("codex", [tmp_path]) is None

    nested = tmp_path / "nested" / "codex"
    nested.parent.mkdir()
    nested.symlink_to(dispatcher)
    assert find_executable("codex", [tmp_path]) == nested
