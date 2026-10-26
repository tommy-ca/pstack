from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.verify_harness as scanner

SCANNER = ROOT / "scripts" / "verify_harness.py"


def test_archivable_intent_chain_guard_distinguishes_changes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        changes = Path(tmp)
        complete = changes / "complete"
        complete.mkdir()
        (complete / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
        incomplete = changes / "incomplete"
        incomplete.mkdir()
        (incomplete / "tasks.md").write_text("- [ ] 1.1 later\n", encoding="utf-8")
        archived = changes / "archive" / "historical"
        archived.mkdir(parents=True)
        (archived / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
        assert scanner.archivable_changes_missing_artifacts(changes) == [
            "complete/design.md",
            "complete/adr.md",
        ]


def test_archived_intent_chains_are_complete() -> None:
    missing = scanner.archived_changes_missing_artifacts(ROOT / "openspec/changes/archive")
    assert not missing, missing


def test_archived_change_missing_adr_artifact_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp)
        change = archive / "2026-10-13-pstack-fixture"
        (change / "specs" / "capability").mkdir(parents=True)
        (change / "specs" / "capability" / "spec.md").write_text(
            "## Purpose\nfixture\n", encoding="utf-8"
        )
        for artifact in ("proposal.md", "design.md", "tasks.md", ".openspec.yaml"):
            (change / artifact).write_text("x\n", encoding="utf-8")
        assert scanner.archived_changes_missing_artifacts(archive) == [
            "2026-10-13-pstack-fixture/adr.md"
        ]
        (change / "adr.md").write_text("x\n", encoding="utf-8")
        assert scanner.archived_changes_missing_artifacts(archive) == []


def test_archived_change_skip_specs_exempts_specs_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp)
        for name, manifest in (
            ("skipped", "schema: intent-driven\nskip_specs: true\n"),
            ("enforced", "schema: intent-driven\n"),
        ):
            change = archive / f"2026-10-13-{name}"
            change.mkdir(parents=True)
            for artifact in ("proposal.md", "design.md", "adr.md", "tasks.md"):
                (change / artifact).write_text("x\n", encoding="utf-8")
            (change / ".openspec.yaml").write_text(manifest, encoding="utf-8")
        assert scanner.archived_changes_missing_artifacts(archive) == [
            "2026-10-13-enforced/specs/**/*.md"
        ]
        # skip_specs exempts specs only; other required artifacts stay enforced.
        (archive / "2026-10-13-skipped" / "adr.md").unlink()
        assert scanner.archived_changes_missing_artifacts(archive) == [
            "2026-10-13-enforced/specs/**/*.md",
            "2026-10-13-skipped/adr.md",
        ]


def test_durable_specs_have_non_placeholder_purposes() -> None:
    for spec in sorted((ROOT / "openspec/specs").glob("*/spec.md")):
        text = spec.read_text(encoding="utf-8")
        assert "## Purpose\n" in text
        purpose = text.split("## Purpose\n", 1)[1].split("\n\n", 1)[0].strip()
        assert purpose and not purpose.startswith("TBD -"), spec


def test_benny_guard_denies_compound_merge_and_plain_push() -> None:
    script = ROOT / "automations/benny-grok/bin/fail-closed.sh"
    for command in (
        "git merge feature && git push origin main",
        "git push origin main && git merge feature",
    ):
        deny = subprocess.run(
            ["sh", str(script)],
            input=json.dumps({"toolInput": {"command": command}}),
            capture_output=True,
            text=True,
            check=False,
        )
        assert deny.returncode == 2, command
        assert json.loads(deny.stdout)["decision"] == "deny", command

    force_lease = subprocess.run(
        ["sh", str(script)],
        input=json.dumps(
            {"toolInput": {"command": "git push --force-with-lease origin main"}}
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert force_lease.returncode == 2
    assert json.loads(force_lease.stdout)["decision"] == "deny"


def test_openspec_intent_driven_schema_resolves() -> None:
    schema = ROOT / "openspec/schemas/intent-driven/schema.yaml"
    assert schema.is_file()
    text = schema.read_text(encoding="utf-8")
    assert "name: intent-driven" in text
    assert "id: adr" in text
    cfg = (ROOT / "openspec/config.yaml").read_text(encoding="utf-8")
    assert "schema: intent-driven" in cfg
    change = (
        ROOT
        / "openspec/changes/archive/2026-08-31-pstack-benny-atomic-blocks"
    )
    assert (change / "design.md").is_file()
    assert (change / "adr.md").is_file()
    proc = subprocess.run(
        ["openspec", "schema", "which", "intent-driven"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    combined = (proc.stderr or "") + (proc.stdout or "")
    assert "intent-driven" in combined.lower()
    assert "not found" not in combined.lower()
