#!/usr/bin/env python3
"""Rewrite Cursor harness call sites onto grok-build tools.

Principles and playbook steps stay. Only named harness APIs change.

This pass rewrites tool ids and, on a fresh official copy, the models-file
path. It does not rewrite model slugs. Official pstack ships a Cursor panel
as inline defaults. After a refresh, those slugs must not remain as skill
fallbacks: omit task.model when ~/.grok/pstack-models.toml is absent or
inherit-parent/auto.

TEST-PLAN.md, README.md, and docs/ name Cursor ids and ~/.cursor/rules as
negatives (FAIL tokens, "never write this"). Do not rewrite those files.
Once a file already contains ~/.grok/pstack-models.toml, leave any remaining
~/.cursor/rules/pstack-models.mdc mention alone. Otherwise "never create the
Cursor mdc" becomes "never create the grok toml".
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from skill_frontmatter import read_scalar, split_frontmatter, validate_skill_name

ROOT = pathlib.Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "automations", ".superpowers", ".worktrees", "openspec", ".audit"}
SKIP_FILES = {
    "HARNESS.md",
    "grok-tools.md",
    "UPSTREAM",
    "adapt-harness.py",
    "TEST-PLAN.md",
    "README.md",
    "README.zh-CN.md",
    "verify-harness.py",
}
TEXT_SUFFIXES = {".md", ".toml", ".json", ".ts", ".sh", ".mjs"}

CURSOR_MODELS_PATH = "~/.cursor/rules/pstack-models.mdc"
GROK_MODELS_PATH = "~/.grok/pstack-models.toml"

REPLACEMENTS: list[tuple[str, str]] = [
    (CURSOR_MODELS_PATH, GROK_MODELS_PATH),
    ("AskQuestion", "ask_user_question"),
    ("TodoWrite", "todo_write"),
    ('subagent_type: "generalPurpose"', 'subagent_type: "general-purpose"'),
    ("subagent_type: generalPurpose", 'subagent_type: "general-purpose"'),
    ("`generalPurpose`", "`general-purpose`"),
    ("generalPurpose", "general-purpose"),
    ('environment: "cloud"', 'isolation: "worktree"'),
    ('environment: "local"', 'isolation: "none"'),
    ("the Task tool", "the `task` tool"),
    ("The Task tool", "The `task` tool"),
    ("`Task` tool", "`task` tool"),
    ("`Task` calls", "`task` calls"),
    ("`Task` call", "`task` call"),
    ("Task calls", "`task` calls"),
    ("Task call", "`task` call"),
    ("via Task ", "via `task` "),
    ("using the Task ", "using the `task` "),
    ("is_background: true", "background: true"),
    ("Cursor cloud agent", "worktree `task` child"),
    ("Cursor Cloud Agent", "worktree `task` child"),
    ("cursor cloud agent", "worktree `task` child"),
    ("Cursor's built-in babysit skill", "Grok Build's built-in babysit command"),
    ("one Cursor cloud agent per PR", "one worktree `task` child per PR"),
    ("One Cursor cloud agent per PR", "One worktree `task` child per PR"),
    ("each a Cursor cloud agent", "each a worktree `task` child"),
    ('subagent_type: "Comment Sicko"', 'subagent_type: "pstack:comment-sicko"'),
    ('subagent_type: "comment-sicko"', 'subagent_type: "pstack:comment-sicko"'),
    ("`Comment Sicko`", "`pstack:comment-sicko`"),
]


def should_skip(path: pathlib.Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    if set(rel.parts) & SKIP_DIRS:
        return True
    if rel.parts and rel.parts[0] == "docs":
        return True
    if path.name in SKIP_FILES:
        return True
    return path.suffix not in TEXT_SUFFIXES and path.name != "SKILL.md"


def transform(text: str, *, skill_name: str | None = None) -> str:
    if skill_name is not None:
        header, body = split_frontmatter(text)
        name = read_scalar(header, "name")
        if name is None:
            raise ValueError("missing frontmatter 'name'")
        normalized = re.sub(r"\s+", "-", name.lower())
        validate_skill_name(normalized, skill_name)
        read_scalar(header, "mode")
        adapted = []
        for line in header:
            if re.match(r"^mode\s*:", line):
                continue
            if re.match(r"^name\s*:", line) and name != normalized:
                ending = "\r\n" if line.endswith("\r\n") else "\n"
                line = f"name: {normalized}{ending}"
            adapted.append(line)
        text = "".join(adapted) + body
    # Fresh official copy: only the Cursor path is present, so rewrite it.
    # Ported tree: both paths are present on purpose (write grok, never
    # create Cursor). A blind replace inverts that instruction.
    replace_models_path = (
        CURSOR_MODELS_PATH in text and GROK_MODELS_PATH not in text
    )
    for old, new in REPLACEMENTS:
        if old == CURSOR_MODELS_PATH and not replace_models_path:
            continue
        text = text.replace(old, new)
    # Cursor Task `readonly` is not a grok-build task field.
    text = re.sub(
        r"^- `readonly`: `true`.*\n",
        "- read-only: use `subagent_type: \"pstack:how-explorer\"`. Do not send `readonly` or `capability_mode` on `task`; grok-build ignores `capability_mode` on the wire. Builtin `explore` only if that plugin agent is unknown.\n",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^- `readonly`: `false`.*\n",
        "- MCP-backed work: use `subagent_type: \"general-purpose\"` and forbid writes in the prompt. Do not send `readonly` on `task`.\n",
        text,
        flags=re.M,
    )
    text = text.replace("agent mode (readonly strips MCP)", "agent mode (`general-purpose`, MCP inherited)")
    text = text.replace("readonly strips MCP", "`explore` is the read-only type; it is not an MCP sandbox")
    text = text.replace("Readonly/Ask mode strips MCPs", "`explore` is read-oriented; MCP-backed work uses `general-purpose`")
    return text


CURSOR_MODEL_SLUGS = (
    "grok-4.6-fast-xhigh",
    "gpt-5.6-sol-max",
    "claude-fable-5-1-thinking-max",
    "claude-opus-5-thinking-xhigh",
)


def assert_no_cursor_model_slugs() -> None:
    hits: list[str] = []
    skills = ROOT / "skills"
    for path in skills.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for slug in CURSOR_MODEL_SLUGS:
            if slug in text:
                hits.append(f"{path.relative_to(ROOT)}: {slug}")
    if hits:
        raise SystemExit(
            "adapt-harness does not rewrite model slugs; skills/ still names "
            "a Cursor panel fallback. Omit task.model instead.\n  "
            + "\n  ".join(hits)
        )


def files_transform_would_change() -> list[str]:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        with path.open(encoding="utf-8", newline="") as stream:
            original = stream.read()
        if transform(original, skill_name=path.parent.name if path.name == "SKILL.md" else None) != original:
            hits.append(str(path.relative_to(ROOT)))
    return hits


def main() -> None:
    updates = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        with path.open(encoding="utf-8", newline="") as stream:
            original = stream.read()
        updated = transform(original, skill_name=path.parent.name if path.name == "SKILL.md" else None)
        if updated != original:
            updates.append((path, updated))
    for path, updated in updates:
        with path.open("w", encoding="utf-8", newline="") as stream:
            stream.write(updated)
        print(path.relative_to(ROOT))
    print(f"rewrote {len(updates)} files")
    leftover = files_transform_would_change()
    if leftover:
        raise SystemExit(
            "adapt-harness is not idempotent after this pass:\n  "
            + "\n  ".join(leftover)
        )
    assert_no_cursor_model_slugs()


if __name__ == "__main__":
    main()
