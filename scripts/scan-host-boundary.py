#!/usr/bin/env python3
"""Forbidden host vocabulary scanner for portable shared surfaces.

Ensures that shared skills, playbooks, and portability schemas maintain a host-neutral
adapter boundary by detecting host execution primitives, concrete host model slugs,
and host-owned scheduler/question tools that belong behind harness profiles and references.

Usage:
    python3 scripts/scan-host-boundary.py [--check] [--json] [--verbose]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "profiles"


@dataclass(frozen=True)
class Exemption:
    pattern: str
    reason: str


# Typed, path-scoped exemptions
DEFAULT_EXEMPTIONS: Tuple[Exemption, ...] = (
    Exemption("skills/*/references/**", "Host adapter and reference documentation"),
    Exemption("skills/poteto-mode/references/**", "Host adapter tool matrix and references"),
    Exemption("skills/setup-pstack/**", "Host-specific setup skill for Grok CLI configuration"),
    Exemption("**/node_modules/**", "External vendor dependencies in scripts"),
    Exemption("profiles/**", "Host profile declarations and capability bindings"),
    Exemption("tests/**", "Test suites and rejection-testing fixtures"),
    Exemption("scripts/**", "Developer tooling, levers, and verification scripts"),
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


@dataclass
class Violation:
    file_path: str
    line_number: int
    token: str
    category: str
    snippet: str


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

HARNESS_NAMES: Set[str] = {
    "grok",
    "codex",
    "omp",
    "opencode",
    "antigravity",
    "droid",
    "claude",
    "custom",
    "mock",
    "pi",
}

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


def load_profiles(profiles_dir: Path) -> List[Dict]:
    profiles = []
    if not profiles_dir.is_dir():
        return profiles
    for p in sorted(profiles_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            profiles.append(data)
        except Exception:
            continue
    return profiles


def extract_forbidden_vocabulary(profiles_dir: Path) -> Dict[str, str]:
    vocab = dict(KNOWN_HOST_PRIMITIVES)
    profiles = load_profiles(profiles_dir)
    for profile in profiles:
        host = profile.get("host", "unknown")
        rc = profile.get("runtime_conventions", {})
        default_model = rc.get("default_model")
        if (
            default_model
            and default_model not in HARNESS_NAMES
            and default_model not in GENERIC_WORDS
        ):
            vocab[default_model] = f"{host} concrete default model"

        for binding in profile.get("bindings", []):
            prim = binding.get("primitive")
            cap = binding.get("capability", "")
            if prim and isinstance(prim, str):
                clean_prim = prim.split("(")[0].strip()
                if (
                    clean_prim
                    and " " not in clean_prim
                    and ":" not in clean_prim
                    and "/" not in clean_prim
                    and clean_prim not in CAPABILITY_NAMES
                    and clean_prim not in HARNESS_NAMES
                    and clean_prim not in GENERIC_WORDS
                ):
                    vocab[clean_prim] = f"{host} binding primitive for {cap}"

        for alias, target in rc.get("wire_aliases", {}).items():
            if target and isinstance(target, str):
                clean_target = target.split("(")[0].strip()
                if clean_target and clean_target in KNOWN_HOST_PRIMITIVES:
                    vocab[clean_target] = f"{host} wire target"

    return vocab


def is_exempt(rel_path: str, exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS) -> Optional[str]:
    norm_path = rel_path.replace("\\", "/")
    for ex in exemptions:
        if fnmatch.fnmatch(norm_path, ex.pattern):
            return ex.reason
        pattern_parts = ex.pattern.split("/**")
        if len(pattern_parts) == 2:
            prefix = pattern_parts[0]
            if fnmatch.fnmatch(norm_path, prefix) or norm_path.startswith(prefix.rstrip("*") + "/"):
                return ex.reason
    return None


def scan_file(
    file_path: Path,
    root: Path,
    vocab: Dict[str, str],
    exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS,
) -> List[Violation]:
    rel_path = str(file_path.relative_to(root)).replace("\\", "/")
    if is_exempt(rel_path, exemptions):
        return []

    violations: List[Violation] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        for token, category in vocab.items():
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])"
            if re.search(pattern, line):
                violations.append(
                    Violation(
                        file_path=rel_path,
                        line_number=idx,
                        token=token,
                        category=category,
                        snippet=line.strip()[:160],
                    )
                )
    return violations


def run_scan(
    root: Path,
    profiles_dir: Path,
    target_dirs: Optional[List[Path]] = None,
    exemptions: Tuple[Exemption, ...] = DEFAULT_EXEMPTIONS,
) -> Tuple[Dict[str, str], List[Violation], int]:
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
            v = scan_file(f, root, vocab, exemptions)
            violations.extend(v)

    return vocab, violations, scanned_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", default=True, help="Exit 1 on violations (default: True)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose scan details")
    args = parser.parse_args()

    vocab, violations, scanned_count = run_scan(ROOT, PROFILES_DIR)

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
        print(f"[scan-host-boundary] Scanned {scanned_count} files across portable shared surfaces.")

    if not violations:
        print(f"[scan-host-boundary] PASS: Scanned {scanned_count} files across portable surfaces. 0 boundary leaks.")
        return 0

    print(f"[scan-host-boundary] FAIL: Found {len(violations)} forbidden host boundary leaks across {scanned_count} files:")
    for v in violations:
        print(f"  {v.file_path}:{v.line_number}: [{v.token}] ({v.category}) -> {v.snippet}")

    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
