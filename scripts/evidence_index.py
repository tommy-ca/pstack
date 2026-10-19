"""Evidence index row management and cross-check verification (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import json
import stat
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.host_identity import BUILTIN_HOSTS
from scripts.portability_schema import SurfaceRevisions, VerificationReceipt

ROOT = Path(__file__).resolve().parents[1]


def _file_or_denied(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.stat().st_mode)
    except PermissionError:
        return True
    except OSError:
        return False


def get_declared_hosts(root: Path = ROOT) -> List[str]:
    pkg_file = root / "pstack.package.json"
    if pkg_file.is_file():
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8"))
            targets = data.get("host_targets", [])
            if targets and isinstance(targets, list):
                return [str(t) for t in targets]
        except Exception:
            pass
    return list(BUILTIN_HOSTS)


def evidence_index_row(host: str, receipt: VerificationReceipt) -> Dict[str, Any]:
    revisions = receipt.surface_revisions
    return {
        "receipt": f".audit/evidence/{host}-receipt.json",
        "run_id": receipt.run_id,
        "timestamp": receipt.timestamp,
        "overall_verdict": receipt.overall_verdict,
        "planes": receipt.planes,
        "surface_revisions": asdict(revisions) if isinstance(revisions, SurfaceRevisions) else revisions,
    }


def rows_from_receipts(evidence_root: Path, root: Path = ROOT) -> Dict[str, Any]:
    rows: Dict[str, Any] = {}
    for host in get_declared_hosts(root):
        receipt_file = evidence_root / f"{host}-receipt.json"
        if not _file_or_denied(receipt_file):
            continue
        try:
            receipt = VerificationReceipt(**json.loads(receipt_file.read_text(encoding="utf-8")))
            receipt.validate()
            if receipt.host != host:
                raise ValueError(f"{receipt_file} is the receipt for {receipt.host!r}, not {host!r}")
        except Exception:
            continue
        rows[host] = evidence_index_row(host, receipt)
    return rows


def index_row_mismatch(host: str, index_file: Path, receipt_root: Path) -> Optional[str]:
    try:
        hosts = json.loads(index_file.read_text(encoding="utf-8")).get("hosts", {})
    except FileNotFoundError:
        return (
            f"evidence index {index_file} is missing; it is the inventory of every host's "
            f"durable receipt. Rebuild it with: "
            f"python3 scripts/verify-portable.py refresh-static --host all."
        )
    except Exception as err:
        return f"evidence index {index_file} unreadable: {type(err).__name__}: {err}"
    if not isinstance(hosts, dict):
        return f"evidence index {index_file} has a non-object 'hosts': {type(hosts).__name__}"
    row = hosts.get(host)
    if row is None:
        durable_file = receipt_root / ".audit" / "evidence" / f"{host}-receipt.json"
        if not _file_or_denied(durable_file):
            return None
        try:
            VerificationReceipt(**json.loads(durable_file.read_text(encoding="utf-8"))).validate()
        except Exception as err:
            return (
                f"index {index_file} has no row for {host} and its durable receipt "
                f"{durable_file} cannot be read as a usable receipt: "
                f"{type(err).__name__}: {err}. Repair or remove that receipt, then re-run."
            )
        return (
            f"index {index_file} has no row for {host} but its durable receipt "
            f"{durable_file} exists: the inventory is STALE/REBUILD-REQUIRED. Rebuild "
            f"the row with: python3 scripts/verify-portable.py refresh-static --host {host} "
            f"(a host claiming `candidate` writes no durable receipt, so an orphan left by "
            f"a demotion has to be removed instead)."
        )
    if not isinstance(row, dict):
        return f"index row for {host} in {index_file} is {type(row).__name__}, not an object"
    receipt_file = receipt_root / str(row.get("receipt") or f".audit/evidence/{host}-receipt.json")
    try:
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    except Exception as err:
        return f"index row for {host} names {receipt_file}, which cannot be read: {type(err).__name__}: {err}"
    for field_name in ("run_id", "timestamp", "planes", "surface_revisions"):
        if row.get(field_name) != receipt.get(field_name):
            return (
                f"index row for {host} disagrees with {receipt_file} on {field_name}: "
                f"row={row.get(field_name)!r} receipt={receipt.get(field_name)!r}"
            )
    return None


def check_evidence_action(hosts: List[str], root: Path, allow_stale: bool = False) -> int:
    all_ok = True
    index_file = root / ".audit" / "evidence" / "index.json"
    for h in hosts:
        profile_file = root / "profiles" / f"{h}.json"
        if not _file_or_denied(profile_file):
            print(f"[{h}] Profile not found at {profile_file}")
            all_ok = False
            continue
        try:
            d = json.loads(profile_file.read_text(encoding="utf-8"))
        except OSError as err:
            print(f"[{h}] FAIL: profile {profile_file} is unreadable: {type(err).__name__}: {err}")
            all_ok = False
            continue
        from scripts.portability_schema import (
            Binding,
            Evidence,
            HarnessProfile,
            check_evidence_durability,
        )

        b = [Binding(**x) for x in d.get("bindings", [])]
        e = [Evidence(**x) for x in d.get("evidence_ledger", [])]
        prof = HarnessProfile(
            host=d["host"],
            support_state=d["support_state"],
            bindings=b,
            skills_dir=d.get("skills_dir"),
            plugins_dir=d.get("plugins_dir"),
            plugin_manifest=d.get("plugin_manifest"),
            evidence_ledger=e,
            tool_mappings=d.get("tool_mappings"),
            skill_order=d.get("skill_order"),
            runtime_conventions=d.get("runtime_conventions"),
        )
        try:
            res = check_evidence_durability(prof, root, check_freshness=not allow_stale)
            if res["derived_support_state"] == "candidate":
                print(
                    f"[{h}] NOT_COVERED: no planes evaluated, derived support state: "
                    f"candidate (claimed: {res['claimed_support_state']})"
                )
            else:
                print(
                    f"[{h}] PASS: Evidence durable, derived support state: "
                    f"{res['derived_support_state']} (claimed: {res['claimed_support_state']})"
                )
        except Exception as err:
            print(f"[{h}] FAIL: {err}")
            if h == "omp" and "exceeds evidence-derived support state" in str(err):
                print(
                    "       OMP runtime evidence is only observed by a model-backed run: "
                    "regenerate the durable receipt with PSTACK_RUN_OMP_LIVE=1, then re-check."
                )
            all_ok = False
        mismatch = index_row_mismatch(h, index_file, root)
        if mismatch:
            print(f"[{h}] FAIL: {mismatch}")
            all_ok = False
    return 0 if all_ok else 1

