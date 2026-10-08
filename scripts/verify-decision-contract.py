#!/usr/bin/env python3
"""Verify the decision contract and canonical routing registry offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HASH_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CLASS_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.MULTILINE)
SCENARIO_RE = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.MULTILINE)
REGISTRY_KEYS = {"schema_version", "source", "fallback", "routes"}
SOURCE_KEYS = {"repository", "path_prefix", "revision", "tree", "router_blob"}
ROUTE_REQUIRED_KEYS = {"playbook", "canonical_blob", "selection"}
SELECTIONS = {"direct", "semantic_candidate", "system_two"}
PLAYBOOK_PREFIX = "pstack/skills/poteto-mode/playbooks/"
ROUTER_PATH = "pstack/skills/poteto-mode/SKILL.md"


class VerificationError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    repository: str
    revision: str
    tree: str
    router_blob: str


@dataclass(frozen=True)
class Route:
    playbook: str
    canonical_blob: str
    selection: str
    decision_class: str | None


@dataclass(frozen=True)
class Registry:
    source: Source
    routes: tuple[Route, ...]


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError, UnicodeError, VerificationError) as exc:
        raise VerificationError(f"{path}: {exc}") from exc


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - value.keys())
    unknown = sorted(value.keys() - expected)
    if missing or unknown:
        raise VerificationError(f"{label} keys mismatch; missing={missing}, unknown={unknown}")


def valid_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise VerificationError(f"{label} must be a lowercase 40-hex Git object ID")
    return value


def parse_registry(raw: Any) -> Registry:
    if not isinstance(raw, dict):
        raise VerificationError("registry must be a JSON object")
    exact_keys(raw, REGISTRY_KEYS, "registry")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise VerificationError("schema_version must equal 1")
    if raw["fallback"] != "baseline":
        raise VerificationError("fallback must equal baseline")

    source_raw = raw["source"]
    if not isinstance(source_raw, dict):
        raise VerificationError("source must be an object")
    exact_keys(source_raw, SOURCE_KEYS, "source")
    if source_raw["repository"] != "cursor/plugins":
        raise VerificationError("source.repository must equal cursor/plugins")
    if source_raw["path_prefix"] != "pstack/":
        raise VerificationError("source.path_prefix must equal pstack/")
    source = Source(
        repository=source_raw["repository"],
        revision=valid_hash(source_raw["revision"], "source.revision"),
        tree=valid_hash(source_raw["tree"], "source.tree"),
        router_blob=valid_hash(source_raw["router_blob"], "source.router_blob"),
    )

    routes_raw = raw["routes"]
    if not isinstance(routes_raw, list) or not routes_raw:
        raise VerificationError("routes must be a non-empty array")
    routes: list[Route] = []
    playbooks: set[str] = set()
    classes: set[str] = set()
    for index, item in enumerate(routes_raw):
        label = f"routes[{index}]"
        if not isinstance(item, dict):
            raise VerificationError(f"{label} must be an object")
        selection = item.get("selection")
        if not isinstance(selection, str) or selection not in SELECTIONS:
            raise VerificationError(f"{label}.selection is not allowed: {selection}")
        expected = ROUTE_REQUIRED_KEYS | ({"class"} if selection == "semantic_candidate" else set())
        exact_keys(item, expected, label)
        playbook = item["playbook"]
        if not isinstance(playbook, str) or not ID_RE.fullmatch(playbook):
            raise VerificationError(f"{label}.playbook must use kebab-case")
        if playbook in playbooks:
            raise VerificationError(f"duplicate playbook: {playbook}")
        playbooks.add(playbook)
        decision_class = item.get("class")
        if selection == "semantic_candidate":
            if not isinstance(decision_class, str) or not CLASS_RE.fullmatch(decision_class):
                raise VerificationError(f"{label}.class must use lowercase underscore syntax")
            if decision_class in {"other", "abstain"}:
                raise VerificationError(f"{label}.class cannot be {decision_class}")
            if decision_class in classes:
                raise VerificationError(f"duplicate semantic class: {decision_class}")
            classes.add(decision_class)
        routes.append(Route(playbook, valid_hash(item["canonical_blob"], f"{label}.canonical_blob"), selection, decision_class))
    return Registry(source, tuple(routes))


def parse_tree(raw: Any, expected_root: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise VerificationError("upstream tree export must be an object")
    if raw.get("sha") != expected_root:
        raise VerificationError(f"upstream tree root {raw.get('sha')!r} does not match source.tree {expected_root}")
    if raw.get("truncated") is not False:
        raise VerificationError("upstream tree export must have truncated=false")
    entries = raw.get("tree")
    if not isinstance(entries, list):
        raise VerificationError("upstream tree export tree must be an array")
    scoped: dict[str, str] = {}
    seen_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise VerificationError(f"upstream tree entry {index} must be an object")
        path = entry.get("path")
        if not isinstance(path, str):
            raise VerificationError(f"upstream tree entry {index} has no string path")
        affects_scope = path == ROUTER_PATH or path.startswith(PLAYBOOK_PREFIX)
        if affects_scope and path in seen_paths:
            raise VerificationError(f"duplicate upstream tree path: {path}")
        if affects_scope:
            seen_paths.add(path)
        if entry.get("type") != "blob":
            continue
        if path == ROUTER_PATH:
            scoped[path] = valid_hash(entry.get("sha"), f"upstream tree {path}")
            continue
        if path.startswith(PLAYBOOK_PREFIX) and path.endswith(".md"):
            scoped[path] = valid_hash(entry.get("sha"), f"upstream tree {path}")
    return scoped


def validate_commit(raw: Any, revision: str, tree: str) -> None:
    if not isinstance(raw, dict):
        raise VerificationError("upstream commit export must be an object")
    commit_sha = raw.get("sha")
    if commit_sha != revision:
        raise VerificationError(f"upstream commit sha {commit_sha!r} does not match source.revision {revision}")
    commit_tree = raw.get("tree")
    if not isinstance(commit_tree, dict):
        raise VerificationError("upstream commit export tree must be an object")
    tree_sha = commit_tree.get("sha")
    if tree_sha != tree:
        raise VerificationError(f"upstream commit tree {tree_sha!r} does not match source.tree {tree}")


def canonical_inventory(scoped: dict[str, str]) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for path, blob in scoped.items():
        if not path.startswith(PLAYBOOK_PREFIX):
            continue
        relative = path.removeprefix(PLAYBOOK_PREFIX)
        if "/" in relative or not relative.endswith(".md"):
            raise VerificationError(f"unsupported official playbook path: {path}")
        playbook = relative[:-3]
        if not ID_RE.fullmatch(playbook):
            raise VerificationError(f"official playbook filename is not kebab-case: {path}")
        inventory[playbook] = blob
    return inventory


def compare_registry_to_source(registry: Registry, scoped: dict[str, str]) -> None:
    router_blob = scoped.get(ROUTER_PATH)
    if router_blob is None:
        raise VerificationError(f"official tree is missing router path: {ROUTER_PATH}")
    if router_blob != registry.source.router_blob:
        raise VerificationError(f"router blob mismatch; registry={registry.source.router_blob}, official={router_blob}")
    official = canonical_inventory(scoped)
    mapped = {route.playbook: route.canonical_blob for route in registry.routes}
    missing = sorted(official.keys() - mapped.keys())
    added = sorted(mapped.keys() - official.keys())
    wrong = sorted(name for name in official.keys() & mapped.keys() if official[name] != mapped[name])
    if missing or added or wrong:
        raise VerificationError(f"canonical mapping differs from official inventory; missing={missing}, added={added}, wrong_blob={wrong}")


def compare_local_inventory(root: Path, registry: Registry) -> None:
    playbook_dir = root / "skills" / "poteto-mode" / "playbooks"
    local = {
        path.relative_to(playbook_dir).as_posix()[:-3]
        for path in playbook_dir.rglob("*.md")
        if path.is_file()
    } if playbook_dir.is_dir() else set()
    expected = {route.playbook for route in registry.routes}
    missing = sorted(expected - local)
    added = sorted(local - expected)
    if missing or added:
        raise VerificationError(f"local playbook inventory differs from registry; missing={missing}, added={added}")


def normalize_spec(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"^## ADDED Requirements[ \t]*$", "## Requirements", text, flags=re.MULTILINE)
    return text.strip() + "\n"


def inspect_requirements(text: str, label: str) -> None:
    matches = list(REQUIREMENT_RE.finditer(text))
    if not matches:
        raise VerificationError(f"{label} has no Requirement headings")
    names: set[str] = set()
    for index, match in enumerate(matches):
        name = match.group(1)
        if name in names:
            raise VerificationError(f"{label} has duplicate Requirement: {name}")
        names.add(name)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if not SCENARIO_RE.search(text[match.end():end]):
            raise VerificationError(f"{label} Requirement has no Scenario: {name}")


def compare_specs(root: Path) -> str:
    formal_path = root / "openspec" / "specs" / "pstack-jev-decisions" / "spec.md"
    delta_path = root / "openspec" / "changes" / "pstack-jev-decision-plane" / "specs" / "pstack-jev-decisions" / "spec.md"
    try:
        formal = formal_path.read_text(encoding="utf-8")
        delta = delta_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise VerificationError(f"cannot read contract specs: {exc}") from exc
    inspect_requirements(formal, str(formal_path))
    inspect_requirements(delta, str(delta_path))
    normalized_formal = normalize_spec(formal)
    normalized_delta = normalize_spec(delta)
    if normalized_formal != normalized_delta:
        raise VerificationError("formal and delta decision specs differ after Requirements heading normalization")
    return hashlib.sha256(normalized_formal.encode()).hexdigest()


def git_state(root: Path) -> tuple[str | None, bool]:
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=normal"],
        capture_output=True, text=True, check=False,
    )
    return (head.stdout.strip() if head.returncode == 0 and HASH_RE.fullmatch(head.stdout.strip()) else None,
            status.returncode != 0 or bool(status.stdout.strip()))


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_evidence(directory: Path, result: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = directory / f"decision-contract-{result['verdict'].lower()}-{stamp}-{os.getpid()}.json"
    with target.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")


def verify(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    registry_path = root / "references" / "decision-routing.json"
    commit_path = args.upstream_commit.resolve()
    tree_path = args.upstream_tree.resolve()
    head, dirty = git_state(root)
    result: dict[str, Any] = {
        "verdict": "FAIL",
        "scope": "decision-contract-and-canonical-routing",
        "mapping_digest": None,
        "content_digest": None,
        "upstream_commit_digest": None,
        "upstream_tree_digest": None,
        "source": {"repository": None, "revision": None, "tree": None},
        "canonical_route_count": 0,
        "checkout_head": head,
        "dirty": dirty,
        "errors": [],
    }
    try:
        registry = parse_registry(load_json(registry_path))
        result["canonical_route_count"] = len(registry.routes)
        result["mapping_digest"] = digest_file(registry_path)
        result["source"] = {
            "repository": registry.source.repository,
            "revision": registry.source.revision,
            "tree": registry.source.tree,
        }
        validate_commit(load_json(commit_path), registry.source.revision, registry.source.tree)
        result["upstream_commit_digest"] = digest_file(commit_path)
        tree = parse_tree(load_json(tree_path), registry.source.tree)
        result["upstream_tree_digest"] = digest_file(tree_path)
        compare_registry_to_source(registry, tree)
        compare_local_inventory(root, registry)
        result["content_digest"] = compare_specs(root)
        if args.require_clean and (head is None or dirty):
            raise VerificationError("--require-clean requires a Git checkout with a clean tracked worktree and an exact HEAD")
        result["verdict"] = "PASS"
    except (OSError, VerificationError) as exc:
        result["errors"].append(str(exc))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--upstream-commit", type=Path, required=True)
    parser.add_argument("--upstream-tree", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    result = verify(args)
    if args.evidence_dir:
        try:
            write_evidence(args.evidence_dir.resolve(), result)
        except OSError as exc:
            result["verdict"] = "FAIL"
            result["errors"].append(f"cannot write evidence: {exc}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
