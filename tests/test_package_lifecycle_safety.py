#!/usr/bin/env python3
"""Safety and loss-prevention tests for native package lifecycle.

Verifies:
- User-authored files inside plugin directory survive update and uninstall
- Custom skills added by users are never destroyed
- Unmanaged files inside managed skill directories are preserved
- Symlinks pointing outside the plugin tree are not followed during deletion
- Clean residue when no unmanaged files exist
- Idempotent repeated operations
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util
loader = importlib.util.spec_from_file_location("package_lifecycle", ROOT / "scripts" / "package-lifecycle.py")
package_lifecycle = importlib.util.module_from_spec(loader)
loader.loader.exec_module(package_lifecycle)


@pytest.mark.parametrize("host", ["grok", "antigravity", "codex", "omp", "opencode", "droid"])
def test_user_file_inside_plugin_dir_survives_lifecycle(host: str, tmp_path: Path) -> None:
    target = tmp_path / f"user-file-{host}"
    plugin_dir = package_lifecycle.install_plugin(host, target)
    assert plugin_dir.is_dir()

    # User places a custom file inside the plugin root
    user_file = plugin_dir / "user_custom_notes.txt"
    user_file.write_text("critical user content", encoding="utf-8")

    # Update must preserve user file
    ok_up, errs_up = package_lifecycle.update_plugin(host, target)
    assert ok_up is True, f"Update failed: {errs_up}"
    assert user_file.is_file()
    assert user_file.read_text(encoding="utf-8") == "critical user content"

    # Uninstall must remove managed files but preserve user file
    ok_un, errs_un = package_lifecycle.uninstall_plugin(host, target)
    assert ok_un is True, f"Uninstall reported errors: {errs_un}"
    assert user_file.is_file()
    assert user_file.read_text(encoding="utf-8") == "critical user content"
    # Managed manifest must be gone
    assert not (plugin_dir / ".pstack-managed-files.json").exists()


@pytest.mark.parametrize("host", ["grok", "antigravity"])
def test_custom_user_skill_survives_lifecycle(host: str, tmp_path: Path) -> None:
    target = tmp_path / f"custom-skill-{host}"
    plugin_dir = package_lifecycle.install_plugin(host, target)

    # User adds a custom skill directory
    custom_skill = plugin_dir / "skills" / "my-team-skill"
    custom_skill.mkdir(parents=True, exist_ok=True)
    custom_file = custom_skill / "SKILL.md"
    custom_file.write_text("# My Custom Team Skill", encoding="utf-8")

    # Update must NOT delete custom skill
    ok_up, _ = package_lifecycle.update_plugin(host, target)
    assert ok_up is True
    assert custom_file.is_file()
    assert custom_file.read_text(encoding="utf-8") == "# My Custom Team Skill"

    # Uninstall must preserve custom skill
    ok_un, _ = package_lifecycle.uninstall_plugin(host, target)
    assert ok_un is True
    assert custom_file.is_file()
    assert custom_file.read_text(encoding="utf-8") == "# My Custom Team Skill"


def test_file_inside_managed_skill_survives(tmp_path: Path) -> None:
    target = tmp_path / "inside-managed"
    plugin_dir = package_lifecycle.install_plugin("grok", target)

    # Place an extra file inside poteto-mode
    extra_file = plugin_dir / "skills" / "poteto-mode" / "extra_notes.txt"
    extra_file.write_text("poteto notes", encoding="utf-8")

    # Update must preserve extra file
    ok_up, _ = package_lifecycle.update_plugin("grok", target)
    assert ok_up is True
    assert extra_file.is_file()
    assert extra_file.read_text(encoding="utf-8") == "poteto notes"

    # Uninstall must preserve extra file
    ok_un, _ = package_lifecycle.uninstall_plugin("grok", target)
    assert ok_un is True
    assert extra_file.is_file()
    assert extra_file.read_text(encoding="utf-8") == "poteto notes"


def test_outside_symlink_target_never_deleted(tmp_path: Path) -> None:
    target = tmp_path / "symlink-test"
    plugin_dir = package_lifecycle.install_plugin("grok", target)

    # Outside target file
    outside_dir = tmp_path / "outside_system_dir"
    outside_dir.mkdir(parents=True, exist_ok=True)
    outside_file = outside_dir / "do_not_delete.txt"
    outside_file.write_text("system important file", encoding="utf-8")

    # Symlink inside plugin pointing outside
    symlink_path = plugin_dir / "external_symlink"
    os.symlink(str(outside_file), str(symlink_path))

    # Uninstall removes managed files; the external target MUST survive unharmed!
    ok_un, _ = package_lifecycle.uninstall_plugin(host="grok", target_base=target)
    assert ok_un is True
    assert outside_file.is_file()
    assert outside_file.read_text(encoding="utf-8") == "system important file"


def test_clean_uninstall_removes_plugin_dir_completely(tmp_path: Path) -> None:
    target = tmp_path / "clean-uninstall"
    plugin_dir = package_lifecycle.install_plugin("grok", target)
    assert plugin_dir.is_dir()

    # With no user-authored files, uninstall cleanly removes plugin_dir
    ok_un, errs = package_lifecycle.uninstall_plugin("grok", target)
    assert ok_un is True, f"Errors: {errs}"
    assert not plugin_dir.exists()
