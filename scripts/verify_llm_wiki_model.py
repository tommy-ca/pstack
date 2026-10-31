#!/usr/bin/env python3
"""Bounded exhaustive real-code state-machine check for wiki source immutability.

39 ordered traces (3 distinct inputs, lengths 1-3); actual ingest_file calls
are exercised. NOT proof of unbounded concurrency or crash consistency.
A broken overwrite mutant must be detected as a negative control.
"""
from __future__ import annotations

from itertools import product
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.llm_wiki import ingest_file

EVENTS = (("first", "shared.md", b"A"), ("second", "shared.md", b"B"), ("third", "other.md", b"C"))


def broken_overwrite(source: Path, wiki: Path) -> tuple[Path, str]:
    """Deliberately incorrect implementation, never used in production."""
    try:
        return ingest_file(source, wiki)
    except FileExistsError:
        target = wiki / "raw" / "sources" / source.name
        target.write_bytes(source.read_bytes())  # mutation under test
        return target, "mutant"


def explore(ingester) -> int:
    examined = 0
    for length in (1, 2, 3):
        for trace in product(EVENTS, repeat=length):
            examined += 1
            with TemporaryDirectory(prefix="wiki-bound-") as temporary:
                root = Path(temporary)
                wiki = root / ".llm-wiki"
                (wiki / "raw" / "sources").mkdir(parents=True)
                (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
                accepted: dict[str, bytes] = {}
                for index, (identity, name, content) in enumerate(trace):
                    source_dir = root / identity
                    source_dir.mkdir(exist_ok=True)
                    source = source_dir / name
                    source.write_bytes(content)
                    old = accepted.get(name)
                    rejected = False
                    try:
                        ingester(source, wiki)
                    except FileExistsError:
                        rejected = True
                    if old is None:
                        if rejected:
                            raise AssertionError(f"Unexpected first-write rejection at {trace!r}")
                        accepted[name] = content
                    elif content != old and not rejected:
                        raise AssertionError(f"Conflicting source was accepted at step {index}: {trace!r}")
                    elif content == old and rejected:
                        raise AssertionError(f"Exact replay was rejected at step {index}: {trace!r}")
                    for stored_name, expected in accepted.items():
                        observed = (wiki / "raw" / "sources" / stored_name).read_bytes()
                        if observed != expected:
                            raise AssertionError(f"Immutable bytes changed for {stored_name}: {trace!r}")
    return examined


def main() -> int:
    try:
        count = explore(ingest_file)
        print(f"PASS: {count} bounded real-code traces, source immutability + idempotent replay")
    except Exception as exc:
        print(f"FAIL: real-code model check: {exc}", file=sys.stderr)
        return 1
    try:
        explore(broken_overwrite)
    except AssertionError as exc:
        print(f"PASS: deliberate overwrite mutant detected: {exc}")
        return 0
    print("FAIL: overwrite mutant escaped the model checker", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
