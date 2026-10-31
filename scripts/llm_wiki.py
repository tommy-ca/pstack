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
import os
import re
from pathlib import Path
import sys
import tempfile
from typing import Any

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


def verify_sources(wiki_dir: Path) -> list[str]:
    """Verify raw source files against recorded digests in log.md.
    
    Returns a list of error descriptions (empty on valid pass).
    """
    errors: list[str] = []
    log_file = wiki_dir / "log.md"
    raw_sources_dir = wiki_dir / "raw" / "sources"

    if not log_file.is_file():
        return ["Activity log missing: log.md"]
    if not raw_sources_dir.is_dir():
        return ["Raw sources directory missing: raw/sources"]

    # Parse log entries for Ingested <name> (SHA256: <digest>...)
    pattern = re.compile(
        r"- \*\*[^*]+\*\*: Ingested `([^`]+)` \(SHA256: `([a-f0-9]+)\.\.\.`\)"
    )
    logged_sources: dict[str, str] = {}
    for line in log_file.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match:
            fname, digest_prefix = match.group(1), match.group(2)
            logged_sources[fname] = digest_prefix

    # Verify each logged source on disk
    for fname, prefix in logged_sources.items():
        target = raw_sources_dir / fname
        if not target.is_file():
            errors.append(f"Missing raw source: {fname} (recorded SHA256 prefix: {prefix})")
            continue
        actual_hash = compute_sha256(target)
        if not actual_hash.startswith(prefix):
            errors.append(
                f"Source hash mismatch for {fname}: expected prefix {prefix}, got {actual_hash[:len(prefix)]}"
            )

    # Check for unlogged raw sources on disk
    for disk_source in raw_sources_dir.iterdir():
        if disk_source.name.startswith(".") or disk_source.is_dir():
            continue
        if disk_source.name not in logged_sources:
            errors.append(f"Unlogged raw source file on disk: {disk_source.name}")

    return errors


def build_knowledge_graph(wiki_dir: Path) -> dict[str, Any]:
    """Extract directed cross-references between wiki articles and identify orphans."""
    pages_root = (wiki_dir / "wiki").resolve()
    if not pages_root.is_dir():
        return {"nodes": [], "edges": [], "orphans": [], "metrics": {}}

    nodes: list[str] = []
    inbound: dict[str, list[str]] = {}
    outbound: dict[str, list[str]] = {}
    edges: list[dict[str, str]] = []

    pages = sorted(pages_root.rglob("*.md"))
    for page in pages:
        if page.is_symlink():
            continue
        rel = str(page.relative_to(pages_root))
        nodes.append(rel)
        inbound[rel] = []
        outbound[rel] = []

    for page in pages:
        if page.is_symlink():
            continue
        src_rel = str(page.relative_to(pages_root))
        text = page.read_text(encoding="utf-8")
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            label = match.group(1).strip()
            target = match.group(2).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            file_target = target.split("#")[0]
            if not file_target:
                continue
            resolved = (page.parent / file_target).resolve()
            if resolved.is_relative_to(pages_root) and resolved.is_file():
                dest_rel = str(resolved.relative_to(pages_root))
                if dest_rel in outbound[src_rel]:
                    continue
                outbound[src_rel].append(dest_rel)
                inbound[dest_rel].append(src_rel)
                edges.append({"source": src_rel, "target": dest_rel, "label": label})

    orphans = [node for node in nodes if len(inbound[node]) == 0]
    total_nodes = len(nodes)
    total_edges = len(edges)
    density = round(total_edges / (total_nodes * (total_nodes - 1)), 4) if total_nodes > 1 else 0.0

    return {
        "nodes": nodes,
        "edges": edges,
        "inbound": inbound,
        "outbound": outbound,
        "orphans": orphans,
        "metrics": {
            "total_pages": total_nodes,
            "total_links": total_edges,
            "orphan_count": len(orphans),
            "graph_density": density,
        },
    }


def search_wiki(wiki_dir: Path, query: str) -> list[dict[str, Any]]:
    """Perform fast keyword and heading search across wiki pages."""
    pages_root = (wiki_dir / "wiki").resolve()
    terms = [t.lower() for t in query.strip().split() if t.strip()]
    if not terms or not pages_root.is_dir():
        return []

    results: list[dict[str, Any]] = []

    for page in sorted(pages_root.rglob("*.md")):
        if page.is_symlink():
            continue
        rel = str(page.relative_to(wiki_dir))
        content = page.read_text(encoding="utf-8")
        lines = content.splitlines()

        title = page.stem.replace("-", " ").title()
        headings: list[str] = []
        body_snippets: list[str] = []
        score = 0

        # Extract title and headings
        for line in lines:
            line_s = line.strip()
            if line_s.startswith("# "):
                title = line_s[2:].strip()
            elif line_s.startswith(("## ", "### ")):
                headings.append(line_s.lstrip("#").strip())

        title_lower = title.lower()
        headings_lower = " ".join(headings).lower()
        content_lower = content.lower()

        # Score matching
        all_terms_present = all(term in content_lower for term in terms)
        if not all_terms_present:
            continue

        for term in terms:
            if term in title_lower:
                score += 15
            if term in headings_lower:
                score += 8
            score += min(content_lower.count(term), 10)

        # Extract snippet
        for line in lines:
            line_s = line.strip()
            if not line_s or line_s.startswith(("#", "```", "---", "|")):
                continue
            if any(term in line_s.lower() for term in terms):
                body_snippets.append(line_s)
                if len(body_snippets) >= 2:
                    break

        snippet = " ... ".join(body_snippets) if body_snippets else ""
        results.append({
            "path": rel,
            "title": title,
            "score": score,
            "snippet": snippet[:200] + ("..." if len(snippet) > 200 else ""),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def check_wiki(wiki_dir: Path) -> list[str]:
    """Validate wiki structure, configuration, links, and completeness.
    
    Returns a list of error descriptions (empty on valid pass).
    """
    errors: list[str] = []
    if not wiki_dir.is_dir():
        return [f"Wiki root directory not found: {wiki_dir}"]
    wiki_root = wiki_dir.resolve()
    pages_root = (wiki_dir / "wiki").resolve()

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
        if target.is_symlink():
            errors.append(f"Symlink directory forbidden in wiki: {dname}")

    # 3. Config JSON validation
    config_file = wiki_dir / "config.json"
    if config_file.is_file():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            for req_key in ("name", "mode", "topic", "version"):
                if req_key not in cfg:
                    errors.append(f"config.json missing required key '{req_key}'")
                elif not isinstance(cfg[req_key], str) or not cfg[req_key].strip():
                    errors.append(f"config.json key '{req_key}' must be a nonempty string")
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
            if target_rel.startswith(("http://", "https://", "#", "mailto:")):
                continue
            resolved = (wiki_dir / target_rel.split("#", 1)[0]).resolve()
            if not resolved.is_relative_to(pages_root):
                errors.append(f"index.md contains out-of-root link: {target_rel}")
                continue
            if not resolved.is_file():
                errors.append(f"index.md contains broken link: {target_rel} (resolved to {resolved})")
            else:
                indexed_targets.add(resolved)

    # 5. Check every file in wiki/ is indexed
    wiki_content_dir = wiki_dir / "wiki"
    if wiki_content_dir.is_dir():
        for page in wiki_content_dir.rglob("*.md"):
            if page.is_symlink() or not page.resolve().is_relative_to(pages_root):
                errors.append(f"Wiki page escapes content root: {page}")
                continue
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
                if not link_resolved.is_relative_to(wiki_root):
                    errors.append(f"Page {page.name} contains out-of-root link to: {link_target}")
                    continue
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
        pages = sorted(cat_dir.rglob("*.md"))
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

    # A source revision is write-once. Reject known symlink aliases before writes;
    # this check is not an OS sandbox against hostile concurrent directory swaps.
    wiki_dir = wiki_dir.resolve()
    raw_dir = wiki_dir / "raw"
    raw_sources_dir = raw_dir / "sources"
    for directory in (raw_dir, raw_sources_dir):
        if directory.is_symlink():
            raise ValueError(f"Symlink wiki source directory forbidden: {directory}")
    raw_sources_dir.mkdir(parents=True, exist_ok=True)
    log_file = wiki_dir / "log.md"
    if log_file.is_symlink():
        raise ValueError(f"Symlink wiki log forbidden: {log_file}")

    dest = raw_sources_dir / source.name
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    try:
        # Exclusive create is atomic on the destination filesystem; no overwrite.
        with dest.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != content:
            raise FileExistsError(f"Immutable raw source collision: {dest}") from None
        # Exact replays have no additional log event (idempotent ingest).
        return dest, digest
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    log_entry = (
        f"- **{now_str}**: Ingested `{source.name}` (SHA256: `{digest[:12]}...`)"
        + (f" - {label}" if label else "")
        + "\n"
    )
    # A failed append can leave an unlogged source; reconcile with a later audit.
    # This is intentionally not represented as an atomic source+ledger transaction.
    prefix = "" if log_file.is_file() else "# Wiki Activity Log\n\n"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(prefix + log_entry)

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
    check_parser = subparsers.add_parser(
        "check",
        parents=[parent_parser],
        help="Verify wiki structure, config shape, and local links (not semantic schema).",
    )
    check_parser.add_argument(
        "--sources",
        action="store_true",
        help="Also verify raw source file hashes against log.md digests.",
    )

    # verify-sources
    subparsers.add_parser(
        "verify-sources",
        parents=[parent_parser],
        help="Verify raw source file integrity and hashes against log.md digests.",
    )

    # graph
    graph_parser = subparsers.add_parser(
        "graph",
        parents=[parent_parser],
        help="Analyze directed cross-references between wiki articles and detect orphan pages.",
    )
    graph_parser.add_argument("--json", action="store_true", help="Output graph structure as JSON.")
    graph_parser.add_argument("--orphans-only", action="store_true", help="Display only orphan pages.")

    # search
    search_parser = subparsers.add_parser(
        "search",
        parents=[parent_parser],
        help="Perform fast keyword search across wiki titles, headings, and content.",
    )
    search_parser.add_argument("query", type=str, help="Search terms.")
    search_parser.add_argument("--json", action="store_true", help="Output search results as JSON.")

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
        if args.sources:
            source_errors = verify_sources(wiki_dir)
            errors.extend(source_errors)
        if errors:
            print(f"FAIL: {len(errors)} wiki validation error(s) found in {wiki_dir}:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: LLM Wiki at {wiki_dir} is structurally valid and fully indexed.")
        return 0

    elif args.subcommand == "verify-sources":
        errors = verify_sources(wiki_dir)
        if errors:
            print(f"FAIL: {len(errors)} source verification error(s) found in {wiki_dir}:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"PASS: All raw sources in {wiki_dir} match recorded cryptographic digests.")
        return 0

    elif args.subcommand == "graph":
        graph_data = build_knowledge_graph(wiki_dir)
        if args.json:
            print(json.dumps(graph_data, indent=2))
            return 0
        metrics = graph_data["metrics"]
        print(f"Knowledge Graph Analysis for {wiki_dir}:")
        print(f"  Total pages: {metrics.get('total_pages', 0)}")
        print(f"  Total links: {metrics.get('total_links', 0)}")
        print(f"  Graph density: {metrics.get('graph_density', 0.0)}")
        print(f"  Orphan pages ({metrics.get('orphan_count', 0)}):")
        for orphan in graph_data.get("orphans", []):
            print(f"    - {orphan}")
        if not args.orphans_only and graph_data.get("nodes"):
            print("\nPage Cross-References:")
            for node in graph_data["nodes"]:
                out = graph_data["outbound"].get(node, [])
                inb = graph_data["inbound"].get(node, [])
                print(f"  - {node}: {len(inb)} inbound, {len(out)} outbound")
        return 0

    elif args.subcommand == "search":
        results = search_wiki(wiki_dir, args.query)
        if args.json:
            print(json.dumps(results, indent=2))
            return 0
        if not results:
            print(f"No matching wiki pages found for query: '{args.query}'")
            return 0
        print(f"Search results for '{args.query}' ({len(results)} matches):")
        for res in results:
            print(f"  [{res['score']}] {res['title']} ({res['path']})")
            if res["snippet"]:
                print(f"      {res['snippet']}")
        return 0

    elif args.subcommand == "index":
        generated = generate_index_markdown(wiki_dir)
        if args.write:
            index_path = wiki_dir / "index.md"
            # Atomic replace avoids exposing a partially-written navigation index.
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=wiki_dir,
                prefix=".index-", suffix=".tmp", delete=False,
            ) as handle:
                handle.write(generated)
                temporary = Path(handle.name)
            try:
                os.replace(temporary, index_path)
            finally:
                temporary.unlink(missing_ok=True)
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
