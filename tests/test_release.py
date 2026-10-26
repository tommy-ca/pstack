import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_version_is_semver_prerelease() -> None:
    assert (ROOT / "plugin.json").is_file()
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))[
        "version"
    ]
    assert re.fullmatch(r"\d+\.\d+\.\d+-[a-z]+\.\d+", version), version
    assert re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}", version) is None
    assert re.search(r"-pstack\.\d+$", version) is None, version


def test_port_base_tracks_upstream_packaging() -> None:
    recipe = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync_from_upstream.py"), "--recipe"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert recipe.returncode == 0, recipe.stderr
    match = re.search(
        r"official pstack packaging (\d+\.\d+\.\d+)",
        recipe.stdout,
    )
    assert match is not None
    packaging = match.group(1)
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))[
        "version"
    ]
    assert re.fullmatch(rf"{re.escape(packaging)}-[a-z]+\.\d+", version), (
        version
    )


if __name__ == "__main__":
    test_plugin_version_is_semver_prerelease()
    test_port_base_tracks_upstream_packaging()
    print("PASS tests/test_release.py")
