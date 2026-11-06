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
from scripts.setup_pstack import resolve_profiles_dir
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


def test_resolve_profiles_dir_prefers_packaged_then_fallback(tmp_path: Path) -> None:
    # 1. When packaged profiles exist, prefer packaged
    mock_root = tmp_path / "repo1"
    packaged = mock_root / "skills" / "setup-pstack" / "profiles"
    packaged.mkdir(parents=True)
    root_prof = mock_root / "profiles"
    root_prof.mkdir(parents=True)
    assert resolve_profiles_dir(mock_root) == packaged

    # 2. When packaged is absent, fall back to root profiles
    mock_root2 = tmp_path / "repo2"
    root_prof2 = mock_root2 / "profiles"
    root_prof2.mkdir(parents=True)
    assert resolve_profiles_dir(mock_root2) == root_prof2

    # 3. On live repo, resolves to packaged
    assert resolve_profiles_dir(ROOT) == CANONICAL_PROFILES
