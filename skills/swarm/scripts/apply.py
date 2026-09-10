#!/usr/bin/env python3
"""Copy permitted port / new-skill-lever blobs from the upstream cache.

Does not classify. Does not fetch. Write permits come from partition.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path

PARTITION_SCRIPT = Path(__file__).resolve().with_name("partition.py")


def _load_partition():
    spec = importlib.util.spec_from_file_location("swarm_partition", PARTITION_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"missing partition.py: {PARTITION_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _load_partition()


def apply_copies(
    decisions: Sequence[P.WriteDecision],
    cache: Path,
    dest_root: Path,
    tip: str,
    *,
    dry_run: bool,
) -> P.ApplyReport:
    copied: list[str] = []
    skipped: list[str] = []
    refused: list[P.WriteDecision] = []
    for decision in decisions:
        if decision.action == "skip":
            skipped.append(decision.row.path)
            continue
        if decision.action != "copy":
            refused.append(decision)
            continue
        if not dry_run:
            blob = P.read_upstream_blob(cache, tip, decision.row.path)
            if blob is None:
                refused.append(
                    P.WriteDecision(decision.row, "refuse", "missing-source-blob")
                )
                continue
            dest = dest_root / decision.row.path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
        copied.append(decision.row.path)
    return P.ApplyReport(tuple(copied), tuple(skipped), tuple(refused), dry_run)


def format_apply_plan(report: P.ApplyReport) -> str:
    lines: list[str] = []
    for path in report.copied:
        lines.append(f"copy\t{path}")
    for path in report.skipped:
        lines.append(f"skip\t{path}")
    for decision in report.refused:
        lines.append(f"refuse\t{decision.row.path}\t{decision.reason}")
    return "\n".join(lines) + ("\n" if lines else "")


def apply_main(argv: Sequence[str] | None = None) -> P.ApplyReport:
    root = P.repo_root_from_script(PARTITION_SCRIPT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--table", type=Path)
    parser.add_argument("--dest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pin")
    parser.add_argument("--tip")
    args = parser.parse_args(list(argv) if argv is not None else None)
    cache = P.resolve_cache(root, args.cache)
    dest_root = Path(args.dest) if args.dest is not None else root
    table = P.read_table(args.table or P.default_table_path(root))
    _pin, tip = P._resolve_range(table, root, cache, args.pin, args.tip)
    decisions = P.write_decisions(table, dest_root, cache, tip)
    report = apply_copies(decisions, cache, dest_root, tip, dry_run=args.dry_run)
    sys.stdout.write(format_apply_plan(report))
    return report


if __name__ == "__main__":
    try:
        apply_main()
    except SystemExit as exc:
        if isinstance(exc.code, str):
            sys.stderr.write(exc.code + "\n")
            raise SystemExit(2) from None
        raise
