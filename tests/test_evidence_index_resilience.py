from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.evidence_test_helpers import (
    _disposable_copy,
    _omp_live_root,
    _proof_bar_refresh,
    _run_gate,
    _stat_denied_copy,
)


@pytest.mark.parametrize("shape", ["[]", '{"version": 1, "hosts": []}'])
def test_a_wrong_shaped_evidence_index_is_refused_not_crashed(tmp_path: Path, shape: str) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_file.write_text(shape, encoding="utf-8")

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    with pytest.raises(SystemExit) as exit_info:
        second.evidence(second_receipt, update_durable=True)

    assert "REFUSING to rewrite the unreadable evidence index" in str(exit_info.value.code)
    assert str(index_file) in str(exit_info.value.code)
    assert durable.read_bytes() == durable_before
    assert index_file.read_text(encoding="utf-8") == shape
    run_receipt = json.loads((second.run_dir / "receipt.json").read_text(encoding="utf-8"))
    assert run_receipt["run_id"] == second_receipt.run_id != first_receipt.run_id


def test_a_corrupt_evidence_index_is_refused_not_reset(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    index_file = evidence_root / "index.json"
    index_file.write_text(
        json.dumps({"version": 1, "hosts": {"grok": {"run_id": "grok-run"}}}), encoding="utf-8"
    )
    corrupt_bytes = b'{ "version": 1, "hosts": { "grok": { "run_id": "grok-run"'
    index_file.write_bytes(corrupt_bytes)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)

    with pytest.raises(SystemExit) as exit_info:
        verifier.evidence(receipt, update_durable=True)

    assert str(index_file) in str(exit_info.value.code)
    assert index_file.read_bytes() == corrupt_bytes


def test_a_stat_denied_evidence_index_is_refused_not_crashed(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_before = index_file.read_bytes()

    denied = tmp_path / "denied"
    denied.mkdir()
    real_index = denied / "index.json"
    real_index.write_bytes(index_before)
    index_file.unlink()
    index_file.symlink_to(real_index)
    denied.chmod(0o000)

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    try:
        with pytest.raises(SystemExit) as exit_info:
            second.evidence(second_receipt, update_durable=True)
        assert "REFUSING to rewrite the unreadable evidence index" in str(exit_info.value.code)
        assert str(index_file) in str(exit_info.value.code)
        assert durable.read_bytes() == durable_before
        assert (second.run_dir / "receipt.json").is_file()
    finally:
        denied.chmod(0o755)

    assert real_index.read_bytes() == index_before


def test_a_stat_denied_durable_receipt_is_refused_not_crashed(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_before = index_file.read_bytes()

    denied = tmp_path / "denied"
    denied.mkdir()
    real_durable = denied / "omp-receipt.json"
    real_durable.write_bytes(durable_before)
    durable.unlink()
    durable.symlink_to(real_durable)
    denied.chmod(0o000)

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    try:
        second.evidence(second_receipt, update_durable=True)
    finally:
        denied.chmod(0o755)

    assert durable.read_bytes() == durable_before
    assert index_file.read_bytes() == index_before
    assert (second.run_dir / "receipt.json").is_file()


def test_a_stat_denied_profile_is_refused_not_reported_absent(tmp_path: Path) -> None:
    copy_root, _, denied = _stat_denied_copy(tmp_path, "profiles/grok.json")
    try:
        res = _run_gate(copy_root, "check-evidence", "--host", "grok")
    finally:
        denied.chmod(0o755)

    assert res.returncode == 1, res.stdout + res.stderr
    assert "Traceback" not in res.stderr
    assert "Profile not found" not in res.stdout
    assert "profiles/grok.json" in res.stdout and "Permission denied" in res.stdout


def test_a_stat_denied_staleness_receipt_is_refused_not_reported_absent(tmp_path: Path) -> None:
    copy_root, _, denied = _stat_denied_copy(tmp_path, ".audit/evidence/grok-receipt.json")
    try:
        res = _run_gate(copy_root, "check-staleness", "--host", "grok")
    finally:
        denied.chmod(0o755)

    assert res.returncode == 1, res.stdout + res.stderr
    assert "Traceback" not in res.stderr
    assert "not found" not in res.stdout
    assert "grok-receipt.json" in res.stdout and "Permission denied" in res.stdout


def test_a_stat_denied_recorded_receipt_is_refused_not_reported_missing(tmp_path: Path) -> None:
    copy_root, _, denied = _stat_denied_copy(tmp_path, ".audit/evidence/grok-receipt.json")
    try:
        res = _run_gate(copy_root, "check-evidence", "--host", "grok")
    finally:
        denied.chmod(0o755)

    assert res.returncode == 1, res.stdout + res.stderr
    assert "Traceback" not in res.stderr
    assert "is missing" not in res.stdout
    assert "cannot be read" in res.stdout and "grok-receipt.json" in res.stdout
    assert "Permission denied" in res.stdout


def test_a_missing_evidence_index_is_initialized_for_this_host(tmp_path: Path) -> None:
    """A fresh evidence root has no inventory to protect, so the first host creates it."""
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    index_file = evidence_root / "index.json"
    assert not index_file.is_file()
    verifier, receipt = _proof_bar_refresh(root, evidence_root)

    verifier.evidence(receipt, update_durable=True)

    index = json.loads(index_file.read_text(encoding="utf-8"))
    assert sorted(index["hosts"]) == ["omp"]
    assert index["hosts"]["omp"]["run_id"] == receipt.run_id


def test_repeated_refreshes_keep_the_run_that_observed(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable_file = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"

    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    first_durable = json.loads(durable_file.read_text(encoding="utf-8"))
    assert first_durable["run_id"] == first_receipt.run_id

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    second.evidence(second_receipt, update_durable=True)
    second_durable = json.loads(durable_file.read_text(encoding="utf-8"))
    assert second_durable["run_id"] == second_receipt.run_id
    second_scenario = next(s for s in second_durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert second_scenario["preserved_from"] == "previous-live-run"


def test_check_evidence_names_the_omp_live_remedy(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    profile = json.loads((copy_root / "profiles" / "omp.json").read_text(encoding="utf-8"))
    spawn = next(b for b in profile["bindings"] if b["capability"] == "agent.spawn")
    assert spawn["verification_status"] == "verified"
    assert spawn["evidence_ref"]["scenario"] == "runtime-child-spawn-omp"

    receipt_path = copy_root / ".audit" / "evidence" / "omp-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    live_rows = [s for s in receipt["scenarios"] if s["evidence_level"] == "observed_live"]
    assert {s["id"] for s in live_rows} == {
        "runtime-child-spawn-omp",
        "runtime-child-cancel-omp",
        "runtime-isolation-omp",
    }
    for scenario in live_rows:
        scenario["evidence_level"] = "static"
        scenario["settlement"] = None
    receipt["planes"]["runtime"] = "UNTESTED"
    receipt["overall_verdict"] = "UNTESTED"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), "check-evidence", "--host", "omp"],
        capture_output=True,
        text=True,
        cwd=copy_root,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "carries no observed_live settlement" in proc.stdout
    assert "PSTACK_RUN_OMP_LIVE=1" in proc.stdout


def test_a_corrupt_index_refusal_leaves_the_durable_receipt_untouched(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)
    verifier.evidence(receipt, update_durable=True)

    durable_file = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    durable_before = durable_file.read_bytes()
    assert json.loads(index_file.read_text(encoding="utf-8"))["hosts"]["omp"]["run_id"] == json.loads(
        durable_before
    )["run_id"]

    corrupt = b'{ "version": 1, "hosts": { BAD'
    index_file.write_bytes(corrupt)
    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    with pytest.raises(SystemExit):
        second.evidence(second_receipt, update_durable=True)

    assert durable_file.read_bytes() == durable_before
    assert index_file.read_bytes() == corrupt
    assert json.loads((second.run_dir / "receipt.json").read_text(encoding="utf-8"))["run_id"] == second_receipt.run_id


def test_check_evidence_cli_refuses_a_profile_that_violates_a_domain_rule(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [
        sys.executable,
        str(copy_root / "scripts" / "verify-portable.py"),
        "check-evidence",
        "--host",
        "grok",
    ]
    clean = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert clean.returncode == 0, clean.stdout + clean.stderr

    profile_file = copy_root / "profiles" / "grok.json"
    d = json.loads(profile_file.read_text(encoding="utf-8"))
    d["support_state"] = "supported"
    for binding in d["bindings"]:
        binding["verification_status"] = "verified"
        if binding["capability"] == "workspace.shared":
            binding["implementation_status"] = "gap"
    profile_file.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")

    res = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "[grok] FAIL" in res.stdout
    assert "cannot have gap on mandatory capability workspace.shared" in res.stdout


def test_a_missing_index_is_rebuilt_from_the_durable_receipts(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py")]
    index_file = copy_root / ".audit" / "evidence" / "index.json"

    index_file.unlink()
    named = subprocess.run(command + ["check-evidence", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert named.returncode == 1, named.stdout + named.stderr
    assert "is missing" in named.stdout and "refresh-static --host all" in named.stdout

    rebuilt = subprocess.run(command + ["refresh-static", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert "Traceback" not in (rebuilt.stdout + rebuilt.stderr), rebuilt.stdout + rebuilt.stderr
    hosts = json.loads(index_file.read_text(encoding="utf-8"))["hosts"]
    assert sorted(hosts) == ["antigravity", "codex", "grok", "omp", "opencode"]
    for host, row in hosts.items():
        receipt = json.loads((copy_root / row["receipt"]).read_text(encoding="utf-8"))
        assert row["run_id"] == receipt["run_id"], host
        assert row["timestamp"] == receipt["timestamp"], host
        assert row["planes"] == receipt["planes"], host
        assert row["surface_revisions"] == receipt["surface_revisions"], host

    all_hosts = subprocess.run(command + ["check-evidence", "--host", "all"], capture_output=True, text=True, cwd=copy_root)
    assert all_hosts.returncode == 0, all_hosts.stdout + all_hosts.stderr


def test_the_projection_skips_receipt_bytes_a_row_cannot_stand_on(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py")]
    index_file = copy_root / ".audit" / "evidence" / "index.json"

    index_file.unlink()
    (copy_root / ".audit" / "evidence" / "codex-receipt.json").write_text('{"run_id": "x"}\n', encoding="utf-8")
    rebuilt = subprocess.run(command + ["refresh-static", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert "Traceback" not in (rebuilt.stdout + rebuilt.stderr), rebuilt.stdout + rebuilt.stderr
    hosts = sorted(json.loads(index_file.read_text(encoding="utf-8"))["hosts"])
    assert hosts == ["antigravity", "grok", "omp", "opencode"]

    orphan = subprocess.run(command + ["check-evidence", "--host", "codex"], capture_output=True, text=True, cwd=copy_root)
    assert orphan.returncode == 1, orphan.stdout + orphan.stderr
    assert "codex-receipt.json" in orphan.stdout


def test_a_missing_row_comes_back_from_the_receipt_on_the_next_run(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py")]
    index_file = copy_root / ".audit" / "evidence" / "index.json"

    index = json.loads(index_file.read_text(encoding="utf-8"))
    del index["hosts"]["grok"]
    del index["hosts"]["codex"]
    index_file.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    reported = subprocess.run(command + ["check-evidence", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert reported.returncode == 1, reported.stdout + reported.stderr
    assert "STALE/REBUILD-REQUIRED" in reported.stdout
    assert json.loads(index_file.read_text(encoding="utf-8"))["hosts"].keys() == {"omp", "opencode", "antigravity"}

    rebuilt = subprocess.run(command + ["refresh-static", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert "Traceback" not in (rebuilt.stdout + rebuilt.stderr), rebuilt.stdout + rebuilt.stderr
    hosts = json.loads(index_file.read_text(encoding="utf-8"))["hosts"]
    assert sorted(hosts) == ["antigravity", "codex", "grok", "omp", "opencode"]
    for host, row in hosts.items():
        receipt = json.loads((copy_root / row["receipt"]).read_text(encoding="utf-8"))
        assert row["run_id"] == receipt["run_id"] and row["planes"] == receipt["planes"], host

    green = subprocess.run(command + ["check-evidence", "--host", "all"], capture_output=True, text=True, cwd=copy_root)
    assert green.returncode == 0, green.stdout + green.stderr


def test_a_denied_index_write_is_named_not_raised(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py")]
    index_file = copy_root / ".audit" / "evidence" / "index.json"
    before = index_file.read_bytes()

    index_file.chmod(0o444)
    try:
        denied = subprocess.run(command + ["refresh-static", "--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    finally:
        index_file.chmod(0o644)

    output = denied.stdout + denied.stderr
    assert denied.returncode == 1, output
    assert "FAILED to write the evidence index" in output
    assert "Traceback" not in output
    assert index_file.read_bytes() == before
    assert "grok-receipt.json" in output
