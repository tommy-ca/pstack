#!/usr/bin/env python3
"""Host-boundary gate for the portable shared surfaces.

`skills/`, `schemas/`, `agents/` and `droids/` are read by every harness, so a
sentence there may describe a *capability* ("delegate to a worker"), never one
host's concrete name, path, primitive or model. Those live in `profiles/*.json`
and in `skills/*/references/<host>-*.md`. This gate fails when shared prose
leaks one, and it is the only reason the shared skills can stay host-neutral.

Three detectors run over every line of every non-exempt file:

1. Vocabulary. The union of `KNOWN_HOST_PRIMITIVES` below and whatever the
   profiles themselves declare: default models, binding primitives, wire-alias
   targets, `plugins_dir`, and -- when the profile declares a `setup` block --
   its `catalog` and `overlay` paths. The profile is the authority; no host path
   is hardcoded here.
2. Routing directives. A clause that names a host *and* directs work to it
   ("hand to Grok Build's `/create-skill`"). A mere mention or a comparison is
   not a leak.
3. Reviewed prohibitions. The one reviewed sentence in `poteto-mode/SKILL.md`
   that warns readers off the installed copy of the playbooks. It is matched by
   its exact text, never by line number, so moving it changes nothing, and
   rewording it simply makes the exemption inert -- the path then flags. An
   exemption covers only the token occurrences inside the reviewed sentence, so
   a directive elsewhere on the same line still fails.

The gate fails closed: an unparsable profile or an unreadable in-scope file
aborts the scan with `BoundaryInputError` and exit 2, never a silent pass.

Usage:
    python3 scripts/scan-host-boundary.py [--check|--no-check] [--json] [--verbose]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "profiles"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.host_identity import KNOWN_HOSTS, OBSERVER_HOSTS, SCANNED_ONLY_HOST_NAMES  # noqa: E402


@dataclass(frozen=True)
class Exemption:
    """A path scope that owns host specifics on purpose, with the reason it may."""

    pattern: str
    reason: str


class BoundaryInputError(RuntimeError):
    """An input the gate needs to reach a verdict could not be read."""


@dataclass(frozen=True)
class ReviewedProhibition:
    """Host vocabulary a human reviewed and allowed: one exact sentence, one path.

    Keyed by sentence text, never by line number: reflowing the surrounding
    prose or moving the sentence must not change the verdict.
    """

    path: str
    sentence: str
    reason: str


@dataclass
class Violation:
    file_path: str
    line_number: int
    token: str
    category: str
    snippet: str


# Typed, path-scoped exemptions. Each entry is a surface that owns the host
# specifics it names; nothing here is a portable shared surface.
DEFAULT_EXEMPTIONS: Tuple[Exemption, ...] = (
    Exemption("skills/*/references/**", "Per-host adapter tool matrix and reference documentation"),
    Exemption(
        "skills/setup-pstack-grok/**",
        "Grok Build setup adapter: owns the host paths and model keys it writes",
    ),
    Exemption("**/node_modules/**", "External vendor dependencies in scripts"),
    Exemption(
        "profiles/**",
        "Host profile declarations: the authority for host names, primitives and paths",
    ),
    Exemption("tests/**", "Test suites and rejection-testing fixtures"),
    Exemption("scripts/**", "Developer tooling that names host primitives in order to detect them"),
    Exemption(".audit/**", "Historical audit receipts and evidence ledgers"),
    Exemption("openspec/**", "OpenSpec formal change proposals and canonical drifts"),
    Exemption("references/**", "Global harness reference tools documentation"),
    Exemption("*.test.mjs", "JavaScript test fixtures intentionally testing plan markers"),
    Exemption("*.test.py", "Python test fixtures"),
    Exemption("CHANGELOG.md", "Historical change log"),
    Exemption("README.md", "Repository root documentation"),
    Exemption("README.zh-CN.md", "Repository documentation translation"),
    Exemption("todo.md", "Program planning and issue tracking"),
    Exemption(".atl/**", "Agent Teams Lite runtime directory"),
)

# Reviewed, text-keyed exceptions. Adding one is a deliberate review act: quote
# the exact sentence and say why it is not a leak.
REVIEWED_PROHIBITIONS: Tuple[ReviewedProhibition, ...] = (
    ReviewedProhibition(
        path="skills/poteto-mode/SKILL.md",
        sentence="Do not open `~/.grok/installed-plugins/pstack-*/skills/poteto-mode/playbooks/`.",
        reason="Warns readers off the installed copy so the git-tracked playbooks win",
    ),
)

CAPABILITY_NAMES: Set[str] = {
    "agent.spawn",
    "agent.join",
    "agent.message",
    "agent.cancel",
    "agent.resume",
    "workspace.shared",
    "workspace.isolated",
    "workspace.readonly",
    "schedule",
    "monitor",
    "human.gate",
    "human.ask",
    "tool.exec",
    "evidence.capture",
    "plan.update",
    "package.lifecycle",
    "manifest.project",
}

HARNESS_NAMES: Set[str] = set(KNOWN_HOSTS) | set(OBSERVER_HOSTS) | set(SCANNED_ONLY_HOST_NAMES)

# Names that read like host vocabulary but address the portable vocabulary
# itself (capability ids, generic words, this repo's own paths), so
# `profiles/omp.json`'s default model `pi` and `schemas/` enum members stay clean.
GENERIC_WORDS: Set[str] = {
    "inherit",
    "auto",
    "default",
    "none",
    "worktree",
    "cloud",
    "background",
    "scripts/verify-portable.py",
    "task",
    "ask",
    "todo",
    "bash",
    "read",
    "edit",
    "write",
    "terminal",
    "question",
    "webfetch",
}

KNOWN_HOST_PRIMITIVES: Dict[str, str] = {
    "spawn_subagent": "Grok agent.spawn primitive",
    "get_command_or_subagent_output": "Grok agent.join primitive",
    "kill_command_or_subagent": "Grok agent.cancel primitive",
    "scheduler_create": "Grok schedule primitive",
    "MAX_SUBAGENT_DEPTH": "Grok subagent depth limit constant",
    "ask_user_question": "Grok question tool",
    "spawn_agent": "Codex agent.spawn primitive",
    "wait_agent": "Codex agent.join primitive",
    "resume_agent": "Codex agent.resume primitive",
    "pi_spawn": "OMP agent.spawn primitive",
    "pi_wait": "OMP agent.join primitive",
    "pi_resume": "OMP agent.resume primitive",
    "pi_send": "OMP agent.message primitive",
    "pi_prompt": "OMP prompt primitive",
    "task.spawn": "OpenCode agent.spawn primitive",
    "task.wait": "OpenCode agent.join primitive",
    "task.resume": "OpenCode agent.resume primitive",
    "task.cancel": "OpenCode agent.cancel primitive",
    "task.message": "OpenCode agent.message primitive",
    "invoke_subagent": "Antigravity agent.spawn primitive",
    "define_subagent": "Antigravity subagent definition primitive",
    "manage_subagents": "Antigravity agent management primitive",
}

# A host's display name in prose, mapped to the violation category to report.
# Host ids (`grok`, `codex`) are already covered by HARNESS_NAMES filtering, so
# only names that do not read as ids need an entry here.
HOST_DISPLAY_NAMES: Dict[str, str] = {
    "Grok Build": "Grok Build host routing name",
}

# A routing directive sends work or attention to a host: an imperative routing
# verb with the host as its object, or a host as the object of a target
# preposition. `(?!-)` keeps "read-only" from reading as the verb "read", and
# nouns that double as verbs ("an inline mining pass") stay out: a motion verb
# followed by "to <host>" is already caught by the preposition rule below.
ROUTING_VERBS = re.compile(
    r"\b(?:open|read|use|run|invoke|call|route|hand|delegate|dispatch|send|"
    r"escalate|forward|switch|prefer|load|launch|spawn|orchestrate|fall\s+back)\b(?!-)",
    re.IGNORECASE,
)

HOST_TARGET_PREPOSITIONS = re.compile(
    r"\b(?:to|via|through|into|using|over\s+to)\s+(?:the\s+)?",
    re.IGNORECASE,
)

NEGATION = re.compile(
    r"\b(?:not|never|avoid|refuse|cannot|can['\u2019]t|don['\u2019]t|no\s+longer)\b",
    re.IGNORECASE,
)

# Clause separators: sentence punctuation followed by space, and dashes. Commas
# are deliberately not separators, so "Use Grok Build, then review" stays whole.
CLAUSE_BREAK = re.compile(r"(?<=[.!?;:])\s+|\s+[\u2014\u2013]\s+")

# Profile fields that declare a host-owned install location a shared surface
# must never tell a reader to open.
INSTALL_PATH_FIELDS: Tuple[str, ...] = ("plugins_dir",)
SETUP_PATH_FIELDS: Tuple[str, ...] = ("catalog", "overlay")


def load_profiles(profiles_dir: Path) -> List[Dict]:
    """Every host profile, or a named error: a profile the gate cannot read is a gap."""
    if not profiles_dir.is_dir():
        raise BoundaryInputError(f"profile directory is missing: {profiles_dir}")
    profiles = []
    for p in sorted(profiles_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BoundaryInputError(f"unreadable profile {p}: {exc}") from exc
        if not isinstance(data, dict):
            raise BoundaryInputError(f"profile is not an object: {p}")
        profiles.append(data)
    return profiles


def _primitive_name(primitive: object) -> Optional[str]:
    """Bare callable name of a binding primitive, or None when it is prose."""
    if not isinstance(primitive, str):
        return None
    name = primitive.split("(")[0].strip()
    if not name or " " in name or ":" in name or "/" in name:
        return None
    return name


def _is_portable_name(name: str) -> bool:
    """True when a name is portable vocabulary, not a host's private spelling."""
    return name not in CAPABILITY_NAMES and name not in HARNESS_NAMES and name not in GENERIC_WORDS


def _declared_paths(profile: Dict) -> List[Tuple[str, str]]:
    """Host-owned paths a profile declares, with the category to report.

    `setup` is optional: a profile that does not declare it contributes only its
    `plugins_dir`. A `setup` block's `catalog` and `overlay` may be null.
    """
    host = profile.get("host", "unknown")
    declared: List[Tuple[object, str]] = [
        (profile.get(field), f"{host} host install path") for field in INSTALL_PATH_FIELDS
    ]
    setup = profile.get("setup")
    if isinstance(setup, dict):
        declared.extend(
            (setup.get(field), f"{host} setup {field}") for field in SETUP_PATH_FIELDS
        )
    return [(path, category) for path, category in declared if isinstance(path, str) and path]


def extract_forbidden_vocabulary(profiles_dir: Path) -> Dict[str, str]:
    """Token -> category, from the built-in primitive list plus every profile."""
    vocab: Dict[str, str] = dict(KNOWN_HOST_PRIMITIVES)
    for profile in load_profiles(profiles_dir):
        host = profile.get("host", "unknown")
        runtime = profile.get("runtime_conventions", {})

        default_model = runtime.get("default_model")
        if isinstance(default_model, str) and default_model and _is_portable_name(default_model):
            vocab[default_model] = f"{host} concrete default model"

        for binding in profile.get("bindings", []):
            name = _primitive_name(binding.get("primitive"))
            if name and _is_portable_name(name):
                vocab[name] = f"{host} binding primitive for {binding.get('capability', '')}"

        for target in runtime.get("wire_aliases", {}).values():
            name = _primitive_name(target)
            if name and name in KNOWN_HOST_PRIMITIVES:
                vocab[name] = f"{host} wire target"

        for path, category in _declared_paths(profile):
            vocab.setdefault(path, category)

    return vocab


def _token_pattern(token: str) -> Pattern[str]:
    """`token` as a whole word/path, not a substring of a longer name."""
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])")


def _clauses(line: str) -> List[str]:
    return [c for c in CLAUSE_BREAK.split(line) if c.strip()]


def _negated_before(clause: str, pos: int) -> bool:
    """True when a negation precedes `pos` in this clause, so it is not affirmative."""
    return NEGATION.search(clause, 0, pos) is not None


def is_host_routing_directive(line: str) -> Optional[Tuple[str, str]]:
    """Return (token, category) when the line routes work to a host, else None."""
    for display, category in HOST_DISPLAY_NAMES.items():
        mention = re.compile(r"\b" + re.escape(display) + r"\b", re.IGNORECASE)
        target = re.compile(
            HOST_TARGET_PREPOSITIONS.pattern + re.escape(display) + r"\b", re.IGNORECASE
        )
        for clause in _clauses(line):
            if mention.search(clause) is None:
                continue
            for verb in ROUTING_VERBS.finditer(clause):
                host = mention.search(clause, verb.end())
                if host is None or _negated_before(clause, verb.start()):
                    continue
                if NEGATION.search(clause, verb.end(), host.start()) is None:
                    return display, category
            for prep in target.finditer(clause):
                if not _negated_before(clause, prep.start()):
                    return display, category
    return None


def _allowed_occurrences(rel_path: str, line: str, token: str) -> int:
    """Occurrences of `token` that fall inside a reviewed sentence on this line.

    Allowance is per occurrence, not per line: a second actionable path, or a
    routing directive, elsewhere on the sanctioned line still fails.
    """
    allowed = 0
    for prohibition in REVIEWED_PROHIBITIONS:
        if prohibition.path != rel_path or token not in prohibition.sentence:
            continue
        for match in re.finditer(re.escape(prohibition.sentence), line):
            allowed += match.group().count(token)
    return allowed


def _without_reviewed(rel_path: str, line: str) -> str:
    """The line with its reviewed sentences removed, so the remainder is rechecked."""
    for prohibition in REVIEWED_PROHIBITIONS:
        if prohibition.path == rel_path:
            line = line.replace(prohibition.sentence, "")
    return line


def is_exempt(rel_path: str, exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS) -> Optional[str]:
    """Return the exemption reason for a path, or None when it must be scanned."""
    norm_path = rel_path.replace("\\", "/")
    for exemption in exemptions:
        if fnmatch.fnmatch(norm_path, exemption.pattern):
            return exemption.reason
    return None


def scan_file(
    file_path: Path,
    root: Path,
    vocab: Dict[str, str],
    exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS,
) -> List[Violation]:
    """Every forbidden host reference in one file, in line order."""
    rel_path = str(file_path.relative_to(root)).replace("\\", "/")
    if is_exempt(rel_path, exemptions):
        return []

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise BoundaryInputError(f"unreadable in-scope file {rel_path}: {exc}") from exc

    patterns = [
        (token, category, _token_pattern(token)) for token, category in sorted(vocab.items())
    ]

    violations: List[Violation] = []
    for idx, line in enumerate(lines, start=1):
        hits: List[Tuple[str, str]] = [
            (token, category)
            for token, category, pattern in patterns
            if len(pattern.findall(line)) > _allowed_occurrences(rel_path, line, token)
        ]
        routing = is_host_routing_directive(_without_reviewed(rel_path, line))
        if routing is not None:
            hits.append(routing)
        violations.extend(
            Violation(
                file_path=rel_path,
                line_number=idx,
                token=token,
                category=category,
                snippet=line.strip()[:160],
            )
            for token, category in hits
        )
    return violations


def run_scan(
    root: Path,
    profiles_dir: Path,
    target_dirs: Optional[List[Path]] = None,
    exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS,
) -> Tuple[Dict[str, str], List[Violation], int]:
    """Scan the shared surfaces under `root`; return (vocab, violations, files scanned)."""
    vocab = extract_forbidden_vocabulary(profiles_dir)
    violations: List[Violation] = []
    scanned_count = 0

    if target_dirs is None:
        target_dirs = [root / "skills", root / "schemas", root / "agents", root / "droids"]

    for target in target_dirs:
        if target.is_file():
            files = [target]
        elif target.is_dir():
            files = list(target.rglob("*.md")) + list(target.rglob("*.json"))
        else:
            continue

        for f in sorted(files):
            rel = str(f.relative_to(root)).replace("\\", "/")
            if is_exempt(rel, exemptions):
                continue
            scanned_count += 1
            violations.extend(scan_file(f, root, vocab, exemptions))

    return vocab, violations, scanned_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit 1 when a violation is found (default: on; --no-check reports only)",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose scan details")
    args = parser.parse_args()

    try:
        vocab, violations, scanned_count = run_scan(ROOT, PROFILES_DIR)
    except BoundaryInputError as exc:
        print(f"[scan-host-boundary] ERROR: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        payload = {
            "vocabulary_size": len(vocab),
            "scanned_files": scanned_count,
            "violations_count": len(violations),
            "violations": [asdict(v) for v in violations],
        }
        print(json.dumps(payload, indent=2))
        return 1 if (args.check and violations) else 0

    if args.verbose:
        print(f"[scan-host-boundary] Loaded {len(vocab)} forbidden vocabulary items:")
        for tok, cat in sorted(vocab.items()):
            print(f"  - {tok}: {cat}")

    if not violations:
        print(f"[scan-host-boundary] PASS: Scanned {scanned_count} files across portable surfaces. 0 boundary leaks.")
        return 0

    print(f"[scan-host-boundary] FAIL: Found {len(violations)} forbidden host boundary leaks across {scanned_count} files:")
    for v in violations:
        print(f"  {v.file_path}:{v.line_number}: [{v.token}] ({v.category}) -> {v.snippet}")

    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
