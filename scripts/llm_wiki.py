#!/usr/bin/env python3
"""LLM Wiki compiler, validator, and ingestion manager for PStack.

Adheres strictly to SOLID, KISS, DRY, and YAGNI:
- Pure Python 3.10+ standard library (zero external dependencies).
- Single responsibility: validate knowledge schema, compile index, and ingest raw sources.
- Deterministic, headless verification for CI and local agent workflows.

Usage:
    python3 scripts/llm_wiki.py check [--wiki-dir <dir>]
    python3 scripts/llm_wiki.py index [--wiki-dir <dir>] [--write]
    python3 scripts/llm_wiki.py ingest <file> [--wiki-dir <dir>] [--label <label>]
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
import sys

DEFAULT_WIKI_DIR = Path(__file__).resolve().parents[1] / ".llm-wiki"

REQUIRED_TOP_LEVEL_FILES = ("config.json", "WIKI_SCHEMA.md", "index.md", "log.md")
REQUIRED_DIRECTORIES = ("raw", "raw/sources", "wiki")
WIKI_CATEGORIES = ("sources", "entities", "concepts", "requirements", "analyses", "syntheses")


def compute_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_wiki(wiki_dir: Path) -> list[str]:
    """Validate wiki structure, configuration, links, and completeness.
    
    Returns a list of error descriptions (empty on valid pass).
    """
    errors: list[str] = []
    if not wiki_dir.is_dir():
        return [f"Wiki root directory not found: {wiki_dir}"]

    # 1. Required files
    for fname in REQUIRED_TOP_LEVEL_FILES:
        target = wiki_dir / fname
        if not target.is_file():
            errors.append(f"Missing required top-level file: {fname}")

    # 2. Required directories
    for dname in REQUIRED_DIRECTORIES:
        target = wiki_dir / dname
        if not target.is_dir():
            errors.append(f"Missing required directory: {dname}")

    # 3. Config JSON validation
    config_file = wiki_dir / "config.json"
    if config_file.is_file():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            for req_key in ("name", "mode", "topic", "version"):
                if req_key not in cfg:
                    errors.append(f"config.json missing required key '{req_key}'")
        except Exception as e:
            errors.append(f"config.json is invalid JSON: {e}")

    # 4. Check index links and unindexed pages
    index_file = wiki_dir / "index.md"
    indexed_targets: set[Path] = set()
    if index_file.is_file():
        text = index_file.read_text(encoding="utf-8")
        # Extract markdown links: [Title](relative/path.md)
        for link_match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            target_rel = link_match.group(2).strip()
            # Ignore external or absolute links
            if target_rel.startswith(("http://", "https://", "#")):
                continue
            resolved = (wiki_dir / target_rel).resolve()
            if not resolved.is_file():
                errors.append(f"index.md contains broken link: {target_rel} (resolved to {resolved})")
            else:
                indexed_targets.add(resolved)

    # 5. Check every file in wiki/ is indexed
    wiki_content_dir = wiki_dir / "wiki"
    if wiki_content_dir.is_dir():
        for page in wiki_content_dir.rglob("*.md"):
            if page.resolve() not in indexed_targets:
                rel_path = page.relative_to(wiki_dir)
                errors.append(f"Wiki page not listed in index.md: {rel_path}")

            # Check relative links inside the wiki page
            page_text = page.read_text(encoding="utf-8")
            for page_link in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", page_text):
                link_target = page_link.group(2).strip()
                if link_target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                # Split off anchor if present
                file_target = link_target.split("#")[0]
                if not file_target:
                    continue
                link_resolved = (page.parent / file_target).resolve()
                if not link_resolved.exists():
                    errors.append(
                        f"Page {page.name} contains broken relative link to: {link_target}"
                    )

    return errors


def generate_index_markdown(wiki_dir: Path) -> str:
    """Generate index markdown content from categorized wiki pages."""
    wiki_content_dir = wiki_dir / "wiki"
    config_file = wiki_dir / "config.json"
    topic = "PStack Knowledge Base"
    if config_file.is_file():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            topic = cfg.get("topic", topic)
        except Exception:
            pass

    lines = [f"# Knowledge Base Index: {topic}\n"]

    for category in WIKI_CATEGORIES:
        cat_dir = wiki_content_dir / category
        if not cat_dir.is_dir():
            continue
        pages = sorted(cat_dir.glob("*.md"))
        if not pages:
            continue
        lines.append(f"## {category.capitalize()}")
        for page in pages:
            rel_path = page.relative_to(wiki_dir)
            title = page.stem.replace("-", " ").title()
            summary = ""
            for line in page.read_text(encoding="utf-8").splitlines():
                line_str = line.strip()
                if line_str.startswith("# "):
                    title = line_str[2:].strip()
                elif line_str and not line_str.startswith(("#", "```", "---", "|")):
                    summary = line_str
                    break
            if summary:
                lines.append(f"- [{title}]({rel_path}): {summary}")
            else:
                lines.append(f"- [{title}]({rel_path})")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def ingest_file(source: Path, wiki_dir: Path, label: str | None = None) -> tuple[Path, str]:
    """Ingest a source file into raw/sources/ and record provenance in log.md."""
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    raw_sources_dir = wiki_dir / "raw" / "sources"
    raw_sources_dir.mkdir(parents=True, exist_ok=True)

    dest = raw_sources_dir / source.name
    content = source.read_bytes()
    dest.write_bytes(content)

    digest = hashlib.sha256(content).hexdigest()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    log_file = wiki_dir / "log.md"
    log_entry = (
        f"- **{now_str}**: Ingested `{source.name}` (SHA256: `{digest[:12]}...`)"
        + (f" - {label}" if label else "")
        + "\n"
    )
    if log_file.is_file():
        existing = log_file.read_text(encoding="utf-8")
        log_file.write_text(existing + log_entry, encoding="utf-8")
    else:
        log_file.write_text(f"# Wiki Activity Log\n\n{log_entry}", encoding="utf-8")

    return dest, digest


def main(argv: list[str] | None = None) -> int:
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--wiki-dir",
        type=Path,
        default=DEFAULT_WIKI_DIR,
        help="Path to .llm-wiki directory",
    )

    parser = argparse.ArgumentParser(
        parents=[parent_parser],
        description="PStack LLM Wiki management tool.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # check
    subparsers.add_parser(
        "check",
        parents=[parent_parser],
        help="Verify wiki structure, schema, and link integrity.",
    )

    # index
    index_parser = subparsers.add_parser(
        "index",
        parents=[parent_parser],
        help="Rebuild or verify index.md.",
    )
    index_parser.add_argument("--write", action="store_true", help="Write generated index to index.md.")

    # ingest
    ingest_parser = subparsers.add_parser(
        "ingest",
        parents=[parent_parser],
        help="Ingest a source file into raw/sources/.",
    )
    ingest_parser.add_argument("source", type=Path, help="File to ingest")
    ingest_parser.add_argument("--label", type=str, default=None, help="Descriptive provenance note")

    args = parser.parse_args(argv)
    wiki_dir: Path = args.wiki_dir.resolve()

    if args.subcommand == "check":
        errors = check_wiki(wiki_dir)
        if errors:
            print(f"FAIL: {len(errors)} wiki validation error(s) found in {wiki_dir}:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: LLM Wiki at {wiki_dir} is structurally valid and fully indexed.")
        return 0

    elif args.subcommand == "index":
        generated = generate_index_markdown(wiki_dir)
        if args.write:
            index_path = wiki_dir / "index.md"
            index_path.write_text(generated, encoding="utf-8")
            print(f"Wrote generated index to {index_path}")
            return 0
        else:
            print(generated)
            return 0

    elif args.subcommand == "ingest":
        try:
            dest, digest = ingest_file(args.source, wiki_dir, label=args.label)
            print(f"Ingested {args.source} -> {dest}")
            print(f"SHA-256: {digest}")
            return 0
        except Exception as e:
            print(f"FAIL: Ingestion failed: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
