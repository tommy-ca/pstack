#!/usr/bin/env python3
"""Print, cover, seed, and check the upstream refresh classification TSV.

Does not copy files. Does not fetch. Canonical table is
skills/swarm/references/classification.tsv.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, NamedTuple

Change = Literal["A", "M", "D"]
Bucket = Literal[
    "port",
    "skip",
    "host-owned",
    "audit",
    "new-skill-lever",
    "unclassified",
]
PartitionBy = Literal["group", "path"]
WriteAction = Literal["copy", "skip", "refuse"]
WriteReason = Literal[
    "permitted-copy",
    "idempotent-equal",
    "fence",
    "not-copy-bucket",
    "unclassified",
    "already-remapped",
    "host-keep",
    "delete",
    "missing-source-blob",
    "dest-is-cache",
]

CHANGES: frozenset[str] = frozenset({"A", "M", "D"})
BUCKETS: frozenset[str] = frozenset(
    {
        "port",
        "skip",
        "host-owned",
        "audit",
        "new-skill-lever",
        "unclassified",
    }
)
FENCE_BUCKETS: frozenset[str] = frozenset({"skip", "host-owned", "audit"})
COPY_BUCKETS: frozenset[str] = frozenset({"port", "new-skill-lever"})
SLICE_BUCKETS: frozenset[str] = BUCKETS - FENCE_BUCKETS
HEADER: tuple[str, str, str, str] = ("path", "change", "bucket", "note")
WORKER_PATHS_RE = re.compile(r"^worker-[0-9]+\.paths$")
PIN_RE = re.compile(r"^tree ([0-9a-f]{40})$", re.M)

assert COPY_BUCKETS.isdisjoint(FENCE_BUCKETS)
assert "unclassified" not in COPY_BUCKETS
assert "unclassified" in SLICE_BUCKETS

LEFTOVER_TOKENS: tuple[str, ...] = (
    "AskQuestion",
    "TodoWrite",
    "generalPurpose",
    'environment: "cloud"',
    "/deslop",
    "cursor-team-kit",
    "Transcripts live at ~/.cursor/projects",
    "Transcripts live at `~/.cursor/projects",
)

HOST_MARKERS: tuple[str, ...] = (
    "spawn_subagent",
    "pstack:",
    "~/.grok/",
    "scheduler_create",
    "ask_user_question",
    "todo_write",
)

APPLY_CHECK_SKIP_DIRS: frozenset[str] = frozenset(
    {".git", "automations", "scripts", ".superpowers", ".worktrees", "openspec", ".audit"}
)
APPLY_CHECK_SKIP_FILES: frozenset[str] = frozenset(
    {
        "HARNESS.md",
        "UPSTREAM",
        "TEST-PLAN.md",
        "README.md",
        "README.zh-CN.md",
        "codex-tools.md",
        "provider-dispatch.md",
        "classification.tsv",
    }
)
LEFTOVER_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".toml", ".json", ".mjs", ".txt"}
)


class Row(NamedTuple):
    path: str
    change: str
    bucket: str
    note: str


class Table(NamedTuple):
    comments: Mapping[str, str]
    rows: tuple[Row, ...]

    @property
    def pin(self) -> str | None:
        return self.comments.get("pin")

    @property
    def tip(self) -> str | None:
        return self.comments.get("tip")


class WriteDecision(NamedTuple):
    row: Row
    action: WriteAction
    reason: WriteReason


class LeftoverHit(NamedTuple):
    relpath: str
    token: str


class ApplyCheckReport(NamedTuple):
    leftover: tuple[LeftoverHit, ...]
    fence_copied: tuple[str, ...]
    missing_dest: tuple[str, ...]
    ok: bool


class ApplyReport(NamedTuple):
    copied: tuple[str, ...]
    skipped: tuple[str, ...]
    refused: tuple[WriteDecision, ...]
    dry_run: bool


def repo_root_from_script(script_file: Path) -> Path:
    return script_file.resolve().parents[3]


def default_table_path(root: Path) -> Path:
    return root / "skills" / "swarm" / "references" / "classification.tsv"


def primary_checkout_root(root: Path) -> Path:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return root
    common = Path(proc.stdout.strip())
    if not common.is_absolute():
        common = (root / common).resolve()
    else:
        common = common.resolve()
    if common.name == ".git":
        return common.parent
    return common


def default_cache_path(root: Path) -> Path:
    return primary_checkout_root(root) / ".worktrees" / "upstream-cursor-plugins"


def resolve_cache(root: Path, cache: Path | None) -> Path:
    path = Path(cache) if cache is not None else default_cache_path(root)
    if not path.exists():
        raise SystemExit(f"missing cache: {path}")
    return path


def read_upstream_pin(root: Path) -> str:
    text = (root / "UPSTREAM").read_text(encoding="utf-8")
    m = PIN_RE.search(text)
    if not m:
        raise SystemExit("UPSTREAM missing `tree <40-hex>` line")
    return m.group(1)


def sanitize_cell(value: str) -> str:
    cleaned = value.replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()
    if cleaned[:1] in {"=", "+", "-", "@"}:
        return "'" + cleaned
    return cleaned


def parse_row(cells: Sequence[str]) -> Row:
    if len(cells) != 4:
        raise SystemExit(f"expected 4 columns, got {len(cells)}")
    path, change, bucket, note = (c.strip() for c in cells)
    if path.startswith("pstack/"):
        path = path[len("pstack/") :]
    if not path or path.startswith("/") or ".." in path.split("/"):
        raise SystemExit(f"invalid path: {path!r}")
    if change not in CHANGES:
        raise SystemExit(f"invalid change: {change!r}")
    if bucket not in BUCKETS:
        raise SystemExit(f"invalid bucket: {bucket!r}")
    return Row(path, change, bucket, sanitize_cell(note))


def read_table(path: Path) -> Table:
    text = path.read_text(encoding="utf-8")
    comments: dict[str, str] = {}
    header_seen = False
    rows: list[Row] = []
    seen: set[str] = set()
    reader = csv.reader(io.StringIO(text), dialect="excel-tab")
    for raw in reader:
        if not raw or all(not c.strip() for c in raw):
            continue
        first = raw[0]
        if not header_seen and first.lstrip().startswith("#"):
            body = first.lstrip()[1:].strip()
            if "=" in body:
                key, _, val = body.partition("=")
                comments[key.strip()] = val.strip()
            continue
        if not header_seen:
            got = tuple(c.strip() for c in raw)
            if got != HEADER:
                raise SystemExit(f"bad header: {got!r}")
            header_seen = True
            continue
        row = parse_row(raw)
        if row.path in seen:
            raise SystemExit(f"duplicate path: {row.path}")
        seen.add(row.path)
        rows.append(row)
    if not header_seen:
        raise SystemExit("missing TSV header")
    return Table(comments, tuple(rows))


def merge_tables(tables: Sequence[Table]) -> Table:
    if not tables:
        raise SystemExit("merge requires at least one table")
    pin: str | None = None
    tip: str | None = None
    comments: dict[str, str] = {}
    rows: list[Row] = []
    seen: set[str] = set()
    for table in tables:
        comments.update(table.comments)
        if table.pin:
            if pin is not None and table.pin != pin:
                raise SystemExit("pin mismatch across tables")
            pin = table.pin
        if table.tip:
            if tip is not None and table.tip != tip:
                raise SystemExit("tip mismatch across tables")
            tip = table.tip
        for row in table.rows:
            if row.path in seen:
                raise SystemExit(f"duplicate path: {row.path}")
            seen.add(row.path)
            rows.append(row)
    if pin:
        comments["pin"] = pin
    if tip:
        comments["tip"] = tip
    return Table(comments, tuple(rows))


def format_table(table: Table) -> str:
    lines: list[str] = []
    for key in ("pin", "tip"):
        if key in table.comments:
            lines.append(f"# {key}={table.comments[key]}")
    for key, val in table.comments.items():
        if key in {"pin", "tip"}:
            continue
        lines.append(f"# {key}={val}")
    buf = io.StringIO()
    writer = csv.writer(buf, dialect="excel-tab", lineterminator="\n")
    writer.writerow(HEADER)
    for row in table.rows:
        writer.writerow([row.path, row.change, row.bucket, row.note])
    return "\n".join(lines + [buf.getvalue().rstrip("\n")]) + "\n"


def format_paths(rows: Sequence[Row]) -> str:
    if not rows:
        return ""
    return "".join(f"{row.path}\n" for row in rows)


def format_stats(rows: Sequence[Row]) -> str:
    order = (
        "port",
        "skip",
        "host-owned",
        "audit",
        "new-skill-lever",
        "unclassified",
    )
    counts = {bucket: 0 for bucket in order}
    for row in rows:
        counts[row.bucket] += 1
    lines = [f"{bucket}\t{counts[bucket]}" for bucket in counts]
    lines.append(f"total\t{len(rows)}")
    return "\n".join(lines) + "\n"


def filter_rows(rows: Sequence[Row], bucket: str | None) -> tuple[Row, ...]:
    if bucket is None:
        return tuple(rows)
    if bucket not in BUCKETS:
        raise SystemExit(f"invalid bucket: {bucket!r}")
    return tuple(row for row in rows if row.bucket == bucket)


def git_name_status(cache: Path, pin: str, tip: str) -> tuple[tuple[str, str], ...]:
    if not cache.exists():
        raise SystemExit(f"missing cache: {cache}")
    proc = subprocess.run(
        ["git", "-C", str(cache), "diff", "--name-status", f"{pin}..{tip}", "--", "pstack"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or "git diff failed")
    pairs: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        change = parts[0]
        if change[0] in {"R", "C"}:
            raise SystemExit(f"rename/copy status is not classified: {line}")
        if change not in CHANGES:
            raise SystemExit(f"invalid change: {change!r}")
        if len(parts) != 2:
            raise SystemExit(f"bad name-status line: {line!r}")
        path = parts[1]
        if path.startswith("pstack/"):
            path = path[len("pstack/") :]
        pairs.append((change, path))
    return tuple(pairs)


def skeleton_table(
    pin: str, tip: str, name_status: Sequence[tuple[str, str]]
) -> Table:
    rows = tuple(Row(path, change, "unclassified", "") for change, path in name_status)
    return Table({"pin": pin, "tip": tip}, rows)


def overlay_seed(
    prior: Table,
    name_status: Sequence[tuple[str, str]],
    pin: str,
    tip: str,
) -> Table:
    prior_map = {row.path: row for row in prior.rows}
    rows: list[Row] = []
    for change, path in name_status:
        prev = prior_map.get(path)
        if prev is None:
            rows.append(Row(path, change, "unclassified", ""))
            continue
        if prev.bucket != "unclassified":
            rows.append(Row(path, change, prev.bucket, prev.note))
            continue
        if prev.change == change:
            rows.append(Row(path, change, prev.bucket, prev.note))
            continue
        rows.append(Row(path, change, "unclassified", prev.note))
    comments = dict(prior.comments)
    comments["pin"] = pin
    comments["tip"] = tip
    return Table(comments, tuple(rows))


def coverage_errors(
    table: Table,
    name_status: Sequence[tuple[str, str]],
) -> tuple[str, ...]:
    errors: list[str] = []
    diff_map = {path: change for change, path in name_status}
    table_map = {row.path: row for row in table.rows}
    for path, change in diff_map.items():
        row = table_map.get(path)
        if row is None:
            errors.append(f"missing diff path: {path}")
        elif row.change != change:
            errors.append(f"change mismatch: {path} table={row.change} git={change}")
    for path in table_map:
        if path not in diff_map:
            errors.append(f"extra table path: {path}")
    for row in table.rows:
        if row.bucket == "unclassified":
            errors.append(f"unclassified: {row.path}")
    return tuple(errors)


def group_key(path: str, by: PartitionBy) -> str:
    if by == "path":
        return path
    parts = path.split("/")
    if parts[0] == "skills" and len(parts) >= 2:
        return f"skills/{parts[1]}"
    if parts[0] == "docs":
        return "docs"
    return parts[0]


def partition_rows(
    rows: Sequence[Row],
    n_workers: int,
    by: PartitionBy = "group",
) -> tuple[tuple[Row, ...], ...]:
    if n_workers < 1:
        raise SystemExit("workers must be >= 1")
    if not rows:
        raise SystemExit("empty partition")
    groups: dict[str, list[Row]] = {}
    for row in rows:
        groups.setdefault(group_key(row.path, by), []).append(row)
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    slices: list[list[Row]] = [[] for _ in range(n_workers)]
    sizes = [0] * n_workers
    for _, group_rows in ordered:
        idx = min(range(n_workers), key=lambda i: (sizes[i], i))
        slices[idx].extend(group_rows)
        sizes[idx] += len(group_rows)
    packed = tuple(tuple(slice_rows) for slice_rows in slices)
    assert_disjoint(packed)
    return packed


def assert_disjoint(slices: Sequence[Sequence[Row]]) -> None:
    seen: set[str] = set()
    for slice_rows in slices:
        for row in slice_rows:
            if row.path in seen:
                raise SystemExit(f"path in two slices: {row.path}")
            seen.add(row.path)


def write_worker_paths(out_dir: Path, slices: Sequence[Sequence[Row]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.iterdir():
        if existing.is_file() and WORKER_PATHS_RE.match(existing.name):
            existing.unlink()
    for i, slice_rows in enumerate(slices):
        (out_dir / f"worker-{i}.paths").write_text(format_paths(slice_rows), encoding="utf-8")


def _load_tables(paths: Sequence[Path]) -> Table:
    return merge_tables([read_table(path) for path in paths])


def _resolve_range(
    table: Table | None, root: Path, cache: Path, pin: str | None, tip: str | None
) -> tuple[str, str]:
    resolved_pin = pin or (table.pin if table else None) or read_upstream_pin(root)
    if tip:
        resolved_tip = tip
    elif table and table.tip:
        resolved_tip = table.tip
    else:
        proc = subprocess.run(
            ["git", "-C", str(cache), "rev-parse", "origin/main"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise SystemExit(proc.stderr.strip() or "git rev-parse failed")
        resolved_tip = proc.stdout.strip()
    return resolved_pin, resolved_tip


def read_upstream_blob(cache: Path, tip: str, relpath: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(cache), "show", f"{tip}:pstack/{relpath}"],
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout
    path = cache / "pstack" / relpath
    if path.is_file():
        return path.read_bytes()
    return None


def read_dest_bytes(dest_root: Path, relpath: str) -> bytes | None:
    path = dest_root / relpath
    if not path.is_file():
        return None
    return path.read_bytes()


def read_dest_text(dest_root: Path, relpath: str) -> str | None:
    data = read_dest_bytes(dest_root, relpath)
    if data is None:
        return None
    return data.decode("utf-8", errors="replace")


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def dest_is_cache_tree(dest_root: Path, cache: Path) -> bool:
    dest = dest_root.resolve()
    cached = cache.resolve()
    return dest == cached or dest == (cached / "pstack")


def looks_remapped(source_text: str, dest_text: str) -> bool:
    return any(marker in dest_text and marker not in source_text for marker in HOST_MARKERS)


def dest_looks_raw_cursor(text: str) -> bool:
    return any(token in text for token in LEFTOVER_TOKENS)


def leftover_mention_allowed(text: str, token: str, index: int) -> bool:
    line_start = text.rfind("\n", 0, index) + 1
    line_end = text.find("\n", index)
    line = text[line_start : len(text) if line_end < 0 else line_end]
    if token == "/deslop" and ("no `/deslop`" in line or "no /deslop" in line):
        return True
    if token == "cursor-team-kit" and (
        "There is no cursor-team-kit" in line
        or "There is no `cursor-team-kit`" in line
        or "no cursor-team-kit" in line
    ):
        return True
    return False


def leftover_hits(dest_root: Path) -> tuple[LeftoverHit, ...]:
    skills = dest_root / "skills"
    if not skills.is_dir():
        return ()
    hits: list[LeftoverHit] = []
    for path in skills.rglob("*"):
        if not path.is_file() or path.suffix not in LEFTOVER_TEXT_SUFFIXES:
            continue
        rel = path.relative_to(dest_root)
        if set(rel.parts) & APPLY_CHECK_SKIP_DIRS:
            continue
        if path.name in APPLY_CHECK_SKIP_FILES:
            continue
        if rel.parts[:1] == ("docs",):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel_s = rel.as_posix()
        for token in LEFTOVER_TOKENS:
            start = 0
            while True:
                idx = text.find(token, start)
                if idx < 0:
                    break
                if leftover_mention_allowed(text, token, idx):
                    start = idx + len(token)
                    continue
                hits.append(LeftoverHit(rel_s, token))
                break
    return tuple(hits)


def fence_copied_paths(
    table: Table,
    cache: Path,
    dest_root: Path,
    tip: str,
) -> tuple[str, ...]:
    copied: list[str] = []
    for row in table.rows:
        if row.bucket not in FENCE_BUCKETS:
            continue
        source = read_upstream_blob(cache, tip, row.path)
        dest = read_dest_bytes(dest_root, row.path)
        if source is None or dest is None:
            continue
        if dest == source:
            copied.append(row.path)
    return tuple(copied)


def missing_copy_dests(table: Table, dest_root: Path) -> tuple[str, ...]:
    missing: list[str] = []
    for row in table.rows:
        if row.bucket not in COPY_BUCKETS:
            continue
        if row.change not in {"A", "M"}:
            continue
        if read_dest_bytes(dest_root, row.path) is None:
            missing.append(row.path)
    return tuple(missing)


def apply_check(
    table: Table,
    cache: Path,
    dest_root: Path,
    tip: str,
) -> ApplyCheckReport:
    leftover = leftover_hits(dest_root)
    fence = fence_copied_paths(table, cache, dest_root, tip)
    missing = missing_copy_dests(table, dest_root)
    ok = not leftover and not fence and not missing
    return ApplyCheckReport(leftover, fence, missing, ok)


def decide_write(
    row: Row,
    source_bytes: bytes | None,
    dest_bytes: bytes | None,
    *,
    dest_is_cache: bool,
) -> WriteDecision:
    if dest_is_cache:
        return WriteDecision(row, "refuse", "dest-is-cache")
    if row.change == "D":
        return WriteDecision(row, "refuse", "delete")
    if row.bucket in FENCE_BUCKETS:
        return WriteDecision(row, "refuse", "fence")
    if row.bucket == "unclassified":
        return WriteDecision(row, "refuse", "unclassified")
    if row.bucket not in COPY_BUCKETS:
        return WriteDecision(row, "refuse", "not-copy-bucket")
    if source_bytes is None:
        return WriteDecision(row, "refuse", "missing-source-blob")
    if dest_bytes is None:
        return WriteDecision(row, "copy", "permitted-copy")
    if dest_bytes == source_bytes:
        return WriteDecision(row, "skip", "idempotent-equal")
    dest_text = _decode(dest_bytes)
    source_text = _decode(source_bytes)
    if looks_remapped(source_text, dest_text):
        return WriteDecision(row, "refuse", "already-remapped")
    if not dest_looks_raw_cursor(dest_text):
        return WriteDecision(row, "refuse", "host-keep")
    return WriteDecision(row, "copy", "permitted-copy")


def write_decisions(
    table: Table,
    dest_root: Path,
    cache: Path,
    tip: str | None = None,
) -> tuple[WriteDecision, ...]:
    resolved_tip = tip or table.tip
    if not resolved_tip:
        raise SystemExit("missing tip for write decisions")
    dest_is_cache = dest_is_cache_tree(dest_root, cache)
    decisions: list[WriteDecision] = []
    for row in table.rows:
        source = (
            None
            if row.change == "D"
            else read_upstream_blob(cache, resolved_tip, row.path)
        )
        dest = read_dest_bytes(dest_root, row.path)
        decisions.append(
            decide_write(row, source, dest, dest_is_cache=dest_is_cache)
        )
    return tuple(decisions)


def format_apply_check_errors(report: ApplyCheckReport) -> str:
    lines: list[str] = []
    for hit in report.leftover:
        lines.append(f"leftover {hit.token}: {hit.relpath}")
    for path in report.fence_copied:
        lines.append(f"fence copied: {path}")
    for path in report.missing_dest:
        lines.append(f"missing dest: {path}")
    return "\n".join(lines) + ("\n" if lines else "")


def seed_main(args: argparse.Namespace, root: Path) -> None:
    cache = resolve_cache(root, args.cache)
    table = read_table(args.table or default_table_path(root))
    pin, tip = _resolve_range(table, root, cache, args.pin, args.tip)
    overlay = overlay_seed(table, git_name_status(cache, pin, tip), pin, tip)
    text = format_table(overlay)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)


def apply_check_main(args: argparse.Namespace, root: Path) -> None:
    cache = resolve_cache(root, args.cache)
    dest_root = Path(args.dest) if args.dest is not None else root
    table = read_table(args.table or default_table_path(root))
    _pin, tip = _resolve_range(table, root, cache, args.pin, args.tip)
    report = apply_check(table, cache, dest_root, tip)
    if not report.ok:
        sys.stderr.write(format_apply_check_errors(report))
        raise SystemExit(2)
    sys.stdout.write("apply-check ok\n")


def partition_main(argv: Sequence[str] | None = None) -> None:
    root = repo_root_from_script(Path(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    print_p = sub.add_parser("print")
    print_p.add_argument("--table", action="append", type=Path)
    print_p.add_argument("--bucket")
    print_p.add_argument("--paths", action="store_true")
    print_p.add_argument("--stats", action="store_true")
    print_p.add_argument("--coverage", action="store_true")
    print_p.add_argument("--diff", action="store_true")
    print_p.add_argument("--cache", type=Path)
    print_p.add_argument("--pin")
    print_p.add_argument("--tip")

    part_p = sub.add_parser("partition")
    part_p.add_argument("--workers", type=int, required=True)
    part_p.add_argument("--out", type=Path, required=True)
    part_p.add_argument("--table", type=Path)
    part_p.add_argument("--bucket")
    part_p.add_argument("--by", choices=("group", "path"), default="group")

    seed_p = sub.add_parser("seed")
    seed_p.add_argument("--cache", type=Path)
    seed_p.add_argument("--table", type=Path)
    seed_p.add_argument("--out", type=Path)
    seed_p.add_argument("--pin")
    seed_p.add_argument("--tip")

    check_p = sub.add_parser("apply-check")
    check_p.add_argument("--cache", type=Path)
    check_p.add_argument("--table", type=Path)
    check_p.add_argument("--dest", type=Path)
    check_p.add_argument("--pin")
    check_p.add_argument("--tip")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.cmd == "print":
        cache = args.cache or default_cache_path(root)
        if args.diff:
            pin, tip = _resolve_range(None, root, cache, args.pin, args.tip)
            table = skeleton_table(pin, tip, git_name_status(cache, pin, tip))
            sys.stdout.write(format_table(table))
            return
        tables = args.table or [default_table_path(root)]
        table = _load_tables(tables)
        rows = filter_rows(table.rows, args.bucket)
        if args.coverage:
            pin, tip = _resolve_range(table, root, cache, args.pin, args.tip)
            errors = coverage_errors(table, git_name_status(cache, pin, tip))
            if errors:
                sys.stderr.write("\n".join(errors) + "\n")
                raise SystemExit(2)
            sys.stdout.write("coverage ok\n")
            return
        if args.stats:
            sys.stdout.write(format_stats(rows))
            return
        if args.paths:
            sys.stdout.write(format_paths(rows))
            return
        sys.stdout.write(format_table(Table(table.comments, rows)))
        return

    if args.cmd == "seed":
        seed_main(args, root)
        return

    if args.cmd == "apply-check":
        apply_check_main(args, root)
        return

    table = read_table(args.table or default_table_path(root))
    if args.bucket in FENCE_BUCKETS:
        raise SystemExit("skip, host-owned, and audit are fences, not worker slices")
    rows = filter_rows(table.rows, args.bucket)
    rows = tuple(row for row in rows if row.bucket in SLICE_BUCKETS)
    slices = partition_rows(rows, args.workers, args.by)
    for slice_rows in slices:
        if any(row.bucket in FENCE_BUCKETS for row in slice_rows):
            raise SystemExit("port slices must not contain skip or host-owned")
    write_worker_paths(args.out, slices)


if __name__ == "__main__":
    try:
        partition_main()
    except SystemExit as exc:
        if isinstance(exc.code, str):
            sys.stderr.write(exc.code + "\n")
            raise SystemExit(2) from None
        raise
