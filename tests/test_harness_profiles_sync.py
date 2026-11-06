"""Tests for harness profiles relocation and synchronization.

Verifies that:
1. All profiles in `profiles/` are byte-identical to `skills/setup-pstack/profiles/`.
2. Every profile parses cleanly into a valid HarnessProfile.
3. `resolve_profiles_dir` resolves the packaged skill location by default,
   and falls back to `profiles/` when the packaged directory is missing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from scripts.portability_schema import HarnessProfile
from scripts.portability_types import ValidationError
from scripts.setup_pstack import assert_profiles_parity, resolve_profiles_dir, sync_root_profiles_mirror
CANONICAL_PROFILES = ROOT / "skills" / "setup-pstack" / "profiles"
ROOT_PROFILES = ROOT / "profiles"


def test_packaged_profiles_directory_exists() -> None:
    assert CANONICAL_PROFILES.is_dir(), f"Missing {CANONICAL_PROFILES}"
    canonical_files = sorted(p.name for p in CANONICAL_PROFILES.glob("*.json"))
    assert len(canonical_files) >= 9, f"Expected at least 9 profiles, found {len(canonical_files)}"


def test_packaged_profiles_match_root_profiles_byte_for_byte() -> None:
    root_files = {p.name: p for p in ROOT_PROFILES.glob("*.json")}
    packaged_files = {p.name: p for p in CANONICAL_PROFILES.glob("*.json")}

    assert set(root_files.keys()) == set(packaged_files.keys()), (
        f"Mismatch between root profiles and packaged profiles:\n"
        f"Missing in packaged: {set(root_files.keys()) - set(packaged_files.keys())}\n"
        f"Extra in packaged: {set(packaged_files.keys()) - set(root_files.keys())}"
    )

    for name, root_path in root_files.items():
        packaged_path = packaged_files[name]
        assert root_path.read_bytes() == packaged_path.read_bytes(), (
            f"Profile {name} differs between {root_path} and {packaged_path}"
        )


def test_all_packaged_profiles_are_valid_harness_profiles() -> None:
    for path in sorted(CANONICAL_PROFILES.glob("*.json")):
        profile = HarnessProfile.from_file(path)
        profile.validate()
        assert profile.host, f"Missing host in {path.name}"
        assert profile.support_state, f"Missing support_state in {path.name}"


def test_resolve_profiles_dir(tmp_path: Path) -> None:
    # 1. When both packaged profiles and root mirror exist with byte parity, resolves to packaged
    mock_root = tmp_path / "repo1"
    packaged = mock_root / "skills" / "setup-pstack" / "profiles"
    packaged.mkdir(parents=True)
    root_prof = mock_root / "profiles"
    root_prof.mkdir(parents=True)
    (packaged / "test.json").write_text('{"host": "test"}', encoding="utf-8")
    (root_prof / "test.json").write_text('{"host": "test"}', encoding="utf-8")
    assert resolve_profiles_dir(mock_root) == packaged

    # 2. When repo profiles is absent (installed plugin distribution), use packaged profiles
    mock_root2 = tmp_path / "repo2"
    packaged2 = mock_root2 / "skills" / "setup-pstack" / "profiles"
    packaged2.mkdir(parents=True)
    assert resolve_profiles_dir(mock_root2) == packaged2

    # 3. When packaged profiles is absent (legacy fallback), use root profiles
    mock_root3 = tmp_path / "repo3"
    root_prof3 = mock_root3 / "profiles"
    root_prof3.mkdir(parents=True)
    assert resolve_profiles_dir(mock_root3) == root_prof3

    # 4. In workspace with matching profiles, resolves to CANONICAL_PROFILES
    assert resolve_profiles_dir(ROOT) == CANONICAL_PROFILES


def test_profiles_parity_fails_closed_on_drift(tmp_path: Path) -> None:
    mock_root = tmp_path / "drifted_repo"
    packaged = mock_root / "skills" / "setup-pstack" / "profiles"
    packaged.mkdir(parents=True)
    root_prof = mock_root / "profiles"
    root_prof.mkdir(parents=True)
    (packaged / "a.json").write_text('{"host": "a"}', encoding="utf-8")
    (root_prof / "a.json").write_text('{"host": "a"}', encoding="utf-8")

    # Mismatch in file set (extra file in packaged)
    (packaged / "b.json").write_text('{"host": "b"}', encoding="utf-8")
    with pytest.raises(ValidationError, match="Profile file set mismatch"):
        assert_profiles_parity(mock_root)

    # Byte mismatch in content
    (root_prof / "b.json").write_text('{"host": "drifted"}', encoding="utf-8")
    with pytest.raises(ValidationError, match="Profile content drift"):
        assert_profiles_parity(mock_root)


def test_sync_root_profiles_mirror(tmp_path: Path) -> None:
    mock_root = tmp_path / "sync_repo"
    packaged = mock_root / "skills" / "setup-pstack" / "profiles"
    packaged.mkdir(parents=True)
    (packaged / "x.json").write_text('{"host": "x"}', encoding="utf-8")
    (packaged / "y.json").write_text('{"host": "y"}', encoding="utf-8")

    count = sync_root_profiles_mirror(mock_root)
    assert count == 2
    root_prof = mock_root / "profiles"
    assert (root_prof / "x.json").read_text(encoding="utf-8") == '{"host": "x"}'
    assert (root_prof / "y.json").read_text(encoding="utf-8") == '{"host": "y"}'
    # Parity assertion passes
    assert_profiles_parity(mock_root)


def test_components_load_profiles_from_resolved_dir() -> None:
    from scripts.drivers import get_driver
    from scripts.scaffold_verification_skill import get_candidate_skills_dirs
    from scripts.surface_revisions import compute_surface_revisions

    # 1. HarnessDriver
    driver = get_driver("antigravity", ROOT)
    assert driver.profile_data.get("host") == "antigravity"

    # 2. get_candidate_skills_dirs
    dirs = get_candidate_skills_dirs(ROOT)
    assert isinstance(dirs, list)

    # 3. compute_surface_revisions
    revs = compute_surface_revisions(ROOT, "antigravity")
    assert revs.profile_hash != "missing"
