#!/usr/bin/env python3
"""Fill the interrogate reviewer prompt from intent, diff, and rubric files.

Does not spawn. Does not read lead-judgment.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

PACK_NAMES: tuple[str, ...] = (
    "intent.md",
    "diff.patch",
    "rubric.md",
    "code-quality-review.md",
    "prompt.md",
)
PLACEHOLDERS = (
    "{INTENT}",
    "{DIFF_OR_FILES}",
    "{RUBRIC_CONTENTS}",
    "{CODE_QUALITY_CONTENTS}",
)


class PackRequest(NamedTuple):
    intent_text: str
    diff_text: str
    rubric_text: str
    code_quality_text: str
    template_text: str
    out_dir: Path | None


def interrogate_skill_root(script_file: Path) -> Path:
    return script_file.resolve().parents[1]


def repo_root_from_script(script_file: Path) -> Path:
    return script_file.resolve().parents[3]


def read_intent(path: Path) -> str:
    text = sys.stdin.read() if str(path) == "-" else path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        raise SystemExit("intent is empty")
    return stripped


def read_diff(
    repo: Path,
    range_spec: str | None,
    diff_file: Path | None,
    paths: Sequence[str],
) -> str:
    if (range_spec is None) == (diff_file is None):
        raise SystemExit("exactly one of --range or --diff-file is required")
    if diff_file is not None:
        return diff_file.read_text(encoding="utf-8")
    cmd = ["git", "-C", str(repo), "diff", range_spec, "--"]
    cmd.extend(paths)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or "git diff failed")
    return proc.stdout


def read_reference(skill_root: Path, name: str) -> str:
    path = skill_root / "references" / name
    if not path.is_file():
        raise SystemExit(f"missing reference: {path}")
    return path.read_text(encoding="utf-8")


def assemble_prompt(
    template: str,
    intent: str,
    diff: str,
    rubric: str,
    code_quality: str,
) -> str:
    for placeholder in PLACEHOLDERS:
        if placeholder not in template:
            raise SystemExit(f"missing placeholder {placeholder}")
    return (
        template.replace("{INTENT}", intent)
        .replace("{DIFF_OR_FILES}", diff)
        .replace("{RUBRIC_CONTENTS}", rubric)
        .replace("{CODE_QUALITY_CONTENTS}", code_quality)
    )


def write_pack_dir(out_dir: Path, request: PackRequest, prompt: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "intent.md").write_text(request.intent_text + "\n", encoding="utf-8")
    (out_dir / "diff.patch").write_text(request.diff_text, encoding="utf-8")
    (out_dir / "rubric.md").write_text(request.rubric_text, encoding="utf-8")
    (out_dir / "code-quality-review.md").write_text(
        request.code_quality_text, encoding="utf-8"
    )
    (out_dir / "prompt.md").write_text(prompt, encoding="utf-8")


def pack_review(request: PackRequest) -> str:
    prompt = assemble_prompt(
        request.template_text,
        request.intent_text,
        request.diff_text,
        request.rubric_text,
        request.code_quality_text,
    )
    if request.out_dir is not None:
        write_pack_dir(request.out_dir, request, prompt)
    return prompt


def pack_main(argv: Sequence[str] | None = None) -> None:
    skill_root = interrogate_skill_root(Path(__file__))
    repo = repo_root_from_script(Path(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--range")
    parser.add_argument("--diff-file", type=Path)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--rubric", type=Path)
    parser.add_argument("--code-quality", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    template = (
        args.template.read_text(encoding="utf-8")
        if args.template
        else read_reference(skill_root, "reviewer-prompt.md")
    )
    rubric = (
        args.rubric.read_text(encoding="utf-8")
        if args.rubric
        else read_reference(skill_root, "rubric.md")
    )
    code_quality = (
        args.code_quality.read_text(encoding="utf-8")
        if args.code_quality
        else read_reference(skill_root, "code-quality-review.md")
    )
    request = PackRequest(
        intent_text=read_intent(args.intent),
        diff_text=read_diff(
            args.repo or repo, args.range, args.diff_file, args.path
        ),
        rubric_text=rubric,
        code_quality_text=code_quality,
        template_text=template,
        out_dir=args.out,
    )
    prompt = pack_review(request)
    if args.out is None:
        sys.stdout.write(prompt)


if __name__ == "__main__":
    try:
        pack_main()
    except SystemExit as exc:
        if isinstance(exc.code, str):
            sys.stderr.write(exc.code + "\n")
            raise SystemExit(2) from None
        raise
