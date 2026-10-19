"""Evidence index row management and cross-check verification (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import json
import stat
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.evidence_durability import preserve_observed_settlements
from scripts.host_identity import BUILTIN_HOSTS
from scripts.portability_schema import (
    Binding,
    Evidence,
    HarnessProfile,
    SurfaceRevisions,
    VerificationReceipt,
    check_evidence_durability,
    compute_surface_revisions,
    reduce_verdicts,
    settle_planes,
)

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


def receipt_payload(receipt: VerificationReceipt) -> Dict[str, Any]:
    """Serialized receipt, minus optional keys the schema types as strings.

    `adapter_version` is optional in the receipt schema, so an unset value is an
    absent key rather than a null a reader would have to special-case (#446).
    """
    data = asdict(receipt)
    if data.get("adapter_version") is None:
        data.pop("adapter_version", None)
    return data


def write_verification_evidence(
    receipt: VerificationReceipt,
    *,
    evidence_root: Path,
    run_dir: Path,
    host: str,
    update_durable: bool = True,
) -> Path:
    """Write structured run evidence receipt and optionally durable pointer (#613)."""
    evidence_root.mkdir(parents=True, exist_ok=True)
    receipt_file = run_dir / "receipt.json"
    data = receipt_payload(receipt)
    receipt_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    if update_durable:
        index_file = evidence_root / "index.json"
        index_data: Dict[str, Any] = {"version": 1, "hosts": {}}
        if _file_or_denied(index_file):
            try:
                index_data = json.loads(index_file.read_text(encoding="utf-8"))
                if not isinstance(index_data, dict) or not isinstance(index_data.get("hosts", {}), dict):
                    raise ValueError(
                        "expected an object with a 'hosts' object, got "
                        f"{type(index_data).__name__}"
                    )
            except Exception as err:
                sys.exit(
                    f"REFUSING to rewrite the unreadable evidence index at {index_file}: "
                    f"{type(err).__name__}: {err}. The index lists every host's durable "
                    f"receipt, so resetting it would silently drop the other hosts. Repair "
                    f"or remove the file, then re-run. This run's receipt is at {receipt_file}."
                )

        index_data.setdefault("hosts", {}).update(
            {
                h: row
                for h, row in rows_from_receipts(evidence_root).items()
                if h not in index_data["hosts"]
            }
        )

        durable_file = evidence_root / f"{host}-receipt.json"
        durable_data = data
        reusable = True
        if _file_or_denied(durable_file):
            try:
                previous = VerificationReceipt(**json.loads(durable_file.read_text(encoding="utf-8")))
                preserved = preserve_observed_settlements(previous, receipt)
            except Exception as err:
                reusable = False
                print(
                    f"REFUSING to overwrite the durable receipt at {durable_file}: "
                    f"{type(err).__name__}: {err}. This run's receipt is at {receipt_file}."
                )
            else:
                if preserved:
                    receipt.planes = settle_planes(receipt.scenarios)
                    receipt.overall_verdict = reduce_verdicts(receipt.planes.values())
                    durable_data = receipt_payload(receipt)
                    print(
                        f"Preserved prior observed_live settlement(s) from {previous.run_id}: "
                        f"{', '.join(preserved)}"
                    )
        if reusable:
            durable_file.write_text(json.dumps(durable_data, indent=2) + "\n", encoding="utf-8")

            index_data.setdefault("hosts", {})[host] = evidence_index_row(host, receipt)
            try:
                index_file.write_text(json.dumps(index_data, indent=2) + "\n", encoding="utf-8")
            except OSError as err:
                sys.exit(
                    f"FAILED to write the evidence index at {index_file}: "
                    f"{type(err).__name__}: {err}. The durable receipt at {durable_file} is "
                    f"already written, so the inventory trails it until the file is writable "
                    f"and this check is re-run."
                )
        print(f"Evidence captured at {receipt_file} (durable: {durable_file})")
    else:
        print(f"Evidence captured at {receipt_file}")

    return receipt_file


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


def check_staleness_action(
    hosts: List[str],
    evidence_dir: Path,
    root: Path,
    json_output: bool = False,
) -> int:
    staleness_report: Dict[str, Any] = {}
    all_fresh = True
    for h in hosts:
        current_revs = compute_surface_revisions(root, h)
        receipt_file = evidence_dir / f"{h}-receipt.json"
        if not _file_or_denied(receipt_file):
            profile_file = root / "profiles" / f"{h}.json"
            claimed_state = ""
            if _file_or_denied(profile_file):
                try:
                    claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
                except Exception:
                    pass
            if claimed_state == "candidate":
                staleness_report[h] = {
                    "host": h,
                    "receipt_exists": False,
                    "needs_regeneration": False,
                    "stale_planes": [],
                    "stale_reasons": {},
                    "support_state": "candidate",
                }
                continue
            staleness_report[h] = {
                "host": h,
                "receipt_exists": False,
                "needs_regeneration": True,
                "stale_planes": ["canonical", "adapter", "package", "runtime"],
                "stale_reasons": {"all": [f"Receipt file {receipt_file} not found"]},
            }
            all_fresh = False
            continue
        try:
            rdata = json.loads(receipt_file.read_text(encoding="utf-8"))
            receipt = VerificationReceipt(**rdata)
            stale_map = receipt.evaluate_plane_staleness(current_revs)
            stale_planes = [p for p, reasons in stale_map.items() if reasons]
            needs_regen = bool(stale_planes)
            if needs_regen:
                all_fresh = False
            staleness_report[h] = {
                "host": h,
                "receipt_exists": True,
                "run_id": receipt.run_id,
                "timestamp": receipt.timestamp,
                "overall_verdict": receipt.overall_verdict,
                "needs_regeneration": needs_regen,
                "stale_planes": stale_planes,
                "stale_reasons": {p: errs for p, errs in stale_map.items() if errs},
            }
        except Exception as err:
            staleness_report[h] = {
                "host": h,
                "receipt_exists": True,
                "needs_regeneration": True,
                "stale_planes": ["canonical", "adapter", "package", "runtime"],
                "stale_reasons": {"error": [str(err)]},
            }
            all_fresh = False

    if json_output:
        print(json.dumps(staleness_report, indent=2))
    else:
        print("\n================ Evidence Staleness Report ================")
        for h, info in staleness_report.items():
            status = "REGENERATE" if info["needs_regeneration"] else "FRESH"
            stale_str = ", ".join(info["stale_planes"]) if info["stale_planes"] else "None"
            print(f"Host: {h:<12} | Status: {status:<10} | Stale Planes: {stale_str}")
            for p, reasons in info.get("stale_reasons", {}).items():
                for r in reasons:
                    print(f"   - [{p}] {r}")
        print("===========================================================")
        print(f"Overall Matrix Evidence: {'ALL FRESH' if all_fresh else 'REGENERATION NEEDED'}\n")
    return 0 if all_fresh else 1

