from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "interrogate" / "scripts" / "pack.py"


def load_pack():
    spec = importlib.util.spec_from_file_location("interrogate_pack", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_assemble_prompt_fills_placeholders() -> None:
    mod = load_pack()
    template = (
        "I:{INTENT}\nD:{DIFF_OR_FILES}\nR:{RUBRIC_CONTENTS}\n"
        "Q:{CODE_QUALITY_CONTENTS}\n"
    )
    prompt = mod.assemble_prompt(template, "intent-body", "diff-body", "rubric-body", "lens-body")
    assert "intent-body" in prompt
    assert "diff-body" in prompt
    assert "rubric-body" in prompt
    assert "lens-body" in prompt
    assert "{INTENT}" not in prompt


def test_pack_out_overwrites_named_files_only(tmp_path: Path) -> None:
    mod = load_pack()
    keep = tmp_path / "unrelated.txt"
    keep.write_text("keep\n", encoding="utf-8")
    request = mod.PackRequest(
        intent_text="intent-body",
        diff_text="diff-body\n",
        rubric_text="rubric-body\n",
        code_quality_text="lens-body\n",
        template_text="I:{INTENT}\nD:{DIFF_OR_FILES}\nR:{RUBRIC_CONTENTS}\nQ:{CODE_QUALITY_CONTENTS}\n",
        out_dir=tmp_path,
    )
    prompt = mod.pack_review(request)
    assert (tmp_path / "prompt.md").read_text(encoding="utf-8") == prompt
    assert (tmp_path / "intent.md").read_text(encoding="utf-8") == "intent-body\n"
    assert (tmp_path / "diff.patch").read_text(encoding="utf-8") == "diff-body\n"
    assert keep.read_text(encoding="utf-8") == "keep\n"
    request2 = request._replace(intent_text="second")
    mod.pack_review(request2)
    assert (tmp_path / "intent.md").read_text(encoding="utf-8") == "second\n"
    assert keep.read_text(encoding="utf-8") == "keep\n"


def test_pack_cli_ignores_lead_judgment(tmp_path: Path, capsys) -> None:
    mod = load_pack()
    refs = tmp_path / "references"
    refs.mkdir()
    template = refs / "reviewer-prompt.md"
    template.write_text(
        "{INTENT}\n{DIFF_OR_FILES}\n{RUBRIC_CONTENTS}\n{CODE_QUALITY_CONTENTS}\n",
        encoding="utf-8",
    )
    rubric = refs / "rubric.md"
    rubric.write_text("RUBRIC\n", encoding="utf-8")
    lens = refs / "code-quality-review.md"
    lens.write_text("LENS\n", encoding="utf-8")
    (refs / "lead-judgment.md").write_text("MUST-NOT-APPEAR\n", encoding="utf-8")
    intent = tmp_path / "intent.md"
    intent.write_text("do the refresh\n", encoding="utf-8")
    diff = tmp_path / "d.patch"
    diff.write_text("difftext\n", encoding="utf-8")
    mod.pack_main(
        [
            "--intent",
            str(intent),
            "--diff-file",
            str(diff),
            "--template",
            str(template),
            "--rubric",
            str(rubric),
            "--code-quality",
            str(lens),
        ]
    )
    out = capsys.readouterr().out
    assert "MUST-NOT-APPEAR" not in out
    assert "lead-judgment" not in out
    assert "do the refresh" in out
    assert "RUBRIC" in out
