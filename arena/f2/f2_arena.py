#!/usr/bin/env python3
"""F2 arena harness: driver-revision recipes measured against the real tree.

Defect under test (#444 / lane-B row F2): `compute_surface_revisions`
(`scripts/portability_schema.py:601-735`) hashes the *bytes* of the verifier and
its sibling drivers, so a comment edit stales the `adapter` + `runtime` planes
for every host whose claim is `verified`/`supported`.

Three candidate recipes are compared:

  A  whole-file byte hash            (trunk status quo)
  B  behavior-bearing core only      (ast.unparse with docstrings stripped)
  B+ B plus the declared docstring/byte complement
  C  explicit dependency list        (declared public top-level surfaces only)

Two quantities are measured per recipe, on the real files:

  comment-edit cost   neutral edits that still move the revision (= forced
                      multi-host re-proof)
  missed-change risk  behavior-bearing edits that no longer move the revision
                      (= the gate fails open)

Modes
  compare   mutation battery + per-host plane-flip cost           -> results.json
  pins      run the pinned suites against patched disposable copies
  demo      self-check: assert the headline numbers in this file still hold

Run from the repo root:  python3 arena/f2/f2_arena.py demo
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "scripts" / "portability_schema.py").is_file(), ROOT

sys.path.insert(0, str(ROOT))
from scripts.portability_schema import (  # noqa: E402
    VerificationReceipt,
    compute_surface_revisions,
)

HARNESS_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = HARNESS_DIR / "c_registry.json"
RESULTS_FILE = HARNESS_DIR / "results.json"
PINS_FILE = HARNESS_DIR / "pins.json"

# --------------------------------------------------------------------------
# Input sets, copied verbatim from the trunk recipe so a harness drift cannot
# silently measure a different surface.
# --------------------------------------------------------------------------
NAMED_DRIVERS = (
    "canonical-index.py",
    "verify-portable.py",
    "verify-harness.py",
    "adapt-harness.py",
    "scaffold-verification-skill.py",
    "skill_frontmatter.py",
    "portability_schema.py",
    "route_resolver.py",
)
PACKAGE_FILES = ("project-package.py", "package-lifecycle.py", "sync-antigravity-plugin.py")
BOUNDARY_FILE = "scan-host-boundary.py"

# Modules that consume their own module docstring as observable behaviour
# (`argparse.ArgumentParser(description=__doc__)`) out of the driver set above.
DOCSTRING_CONSUMED = ("canonical-index.py", "verify-portable.py")

HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid")


class RecipeError(Exception):
    """Recipe refused to produce a revision (fail closed)."""


def driver_scope(root: Path) -> List[str]:
    rels = [f"scripts/{n}" for n in NAMED_DRIVERS]
    rels += sorted(
        p.relative_to(root).as_posix() for p in (root / "scripts" / "drivers").rglob("*.py")
    )
    return rels


def package_scope(root: Path) -> List[str]:
    return [f"scripts/{n}" for n in PACKAGE_FILES]


# --------------------------------------------------------------------------
# Normalizer
# --------------------------------------------------------------------------
def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return tree


def core_bytes(src: bytes, *, keep_docstrings: bool = False) -> bytes:
    """Behavior-bearing core: canonical AST, comments and formatting dropped."""
    try:
        tree = ast.parse(src.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError) as err:
        raise RecipeError(f"unparseable: {err}") from err
    if not keep_docstrings:
        tree = _strip_docstrings(tree)
    return ast.unparse(tree).encode("utf-8")


def _sha(parts: Sequence[bytes]) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Recipes
# --------------------------------------------------------------------------
def rev_a(root: Path) -> Dict[str, str]:
    """A: trunk. Whole-file bytes, filename folded in."""
    def digest(rels: Sequence[str]) -> str:
        parts: List[bytes] = []
        for rel in rels:
            parts += [rel.encode(), (root / rel).read_bytes()]
        return _sha(parts)

    return {
        "driver_revision": digest(driver_scope(root)),
        "package_driver_revision": digest(package_scope(root)),
        "boundary_driver_revision": digest([f"scripts/{BOUNDARY_FILE}"]),
    }


def rev_b(root: Path, *, complement: bool = False) -> Dict[str, str]:
    """B: hash the behavior-bearing core. B+ adds the declared byte complement."""
    def digest(rels: Sequence[str]) -> str:
        parts: List[bytes] = []
        for rel in rels:
            if not (root / rel).is_file():
                continue  # trunk semantics: a synthetic root may hold a subset
            parts += [rel.encode(), core_bytes((root / rel).read_bytes())]
            if complement and Path(rel).name in DOCSTRING_CONSUMED:
                # `__doc__` is read at runtime by argparse; keep it raw.
                parts.append(_raw_module_docstring((root / rel).read_bytes()))
        return _sha(parts)

    return {
        "driver_revision": digest(driver_scope(root)),
        "package_driver_revision": digest(package_scope(root)),
        "boundary_driver_revision": digest([f"scripts/{BOUNDARY_FILE}"]),
    }


def rev_bplus(root: Path) -> Dict[str, str]:
    return rev_b(root, complement=True)


def _raw_module_docstring(src: bytes) -> bytes:
    tree = ast.parse(src.decode("utf-8"))
    body = tree.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[0].value.value.encode("utf-8")
    return b""


def _public_surfaces(root: Path, rel: str) -> Tuple[str, ...]:
    tree = ast.parse((root / rel).read_text(encoding="utf-8"))
    names: List[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    names.append(tgt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith("_"):
                names.append(node.target.id)
    return tuple(sorted(set(names)))


def build_registry(root: Path) -> Dict[str, List[str]]:
    rels = driver_scope(root) + package_scope(root) + [f"scripts/{BOUNDARY_FILE}"]
    return {rel: sorted(set(_public_surfaces(root, rel))) for rel in rels}


def rev_c(root: Path) -> Dict[str, str]:
    """C: hash only the declared public surfaces, fail closed on drift."""
    if not REGISTRY_FILE.is_file():
        REGISTRY_FILE.write_text(json.dumps(build_registry(root), indent=2, sort_keys=True))
    declared: Dict[str, List[str]] = json.loads(REGISTRY_FILE.read_text())

    def digest(rels: Sequence[str]) -> str:
        parts: List[bytes] = []
        for rel in rels:
            if not (root / rel).is_file():
                continue  # trunk semantics: a synthetic root may hold a subset
            live = sorted(set(_public_surfaces(root, rel)))
            want = declared.get(rel)
            if want is None:
                raise RecipeError(f"undeclared file in scope: {rel}")
            if live != want:
                added = sorted(set(live) - set(want))
                gone = sorted(set(want) - set(live))
                raise RecipeError(f"{rel}: undeclared surface added={added} removed={gone}")
            tree = ast.parse((root / rel).read_text(encoding="utf-8"))
            for node in tree.body:
                names = []
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names = [node.name]
                elif isinstance(node, ast.Assign):
                    names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    names = [node.target.id]
                if names and names[0] in want:
                    seg = ast.get_source_segment(
                        (root / rel).read_text(encoding="utf-8"), node
                    )
                    parts += [f"{rel}:{names[0]}".encode(), core_bytes(seg.encode())]
        return _sha(parts)

    return {
        "driver_revision": digest(driver_scope(root)),
        "package_driver_revision": digest(package_scope(root)),
        "boundary_driver_revision": digest([f"scripts/{BOUNDARY_FILE}"]),
    }


RECIPES = {"A": rev_a, "B": rev_b, "B+": rev_bplus, "C": rev_c}


# --------------------------------------------------------------------------
# Mutation battery
# --------------------------------------------------------------------------
# (id, kind, rel, anchor, replacement). anchor must occur exactly once.
MUTATIONS: List[Tuple[str, str, str, str, str]] = [
    ("n1-comment-eof", "neutral", "scripts/verify-portable.py",
     'if __name__ == "__main__":',
     'if __name__ == "__main__":\n    # F2 comment probe: a comment that cannot move a verdict.'),
    ("n2-comment-body", "neutral", "scripts/portability_schema.py",
     "    # 8. driver revision",
     "    # F2 comment probe inside a function body.\n    # 8. driver revision"),
    ("n3-docstring-module", "observable", "scripts/verify-portable.py",
     '"""Portable lever verification engine for pstack across agent harnesses.',
     '"""Portable lever verification engine for pstack across agent harnesses.\nF2 docstring probe: one added sentence.'),
    ("o1-docstring-module-consumed", "observable", "scripts/canonical-index.py",
     'Reads the immutable UPSTREAM pin, discovers canonical principles, playbooks,',
     'F2 docstring probe: one added sentence.\nReads the immutable UPSTREAM pin, discovers canonical principles, playbooks,'),
    ("n7-docstring-func", "neutral", "scripts/portability_schema.py",
     '"""Receipt this binding points at, whether pinned to a scenario or receipt-only."""',
     '"""Receipt this binding points at, whether pinned to a scenario or receipt-only. F2 probe."""'),
    ("n4-comment-two", "neutral", "scripts/portability_schema.py",
     "        reasons: Dict[str, List[str]] = {p: [] for p in CONFORMANCE_PLANES}",
     "        # F2 comment probe, second site\n        reasons: Dict[str, List[str]] = {p: [] for p in CONFORMANCE_PLANES}"),
    ("n5-whitespace", "neutral", "scripts/verify-portable.py",
     "def reduce_verdicts(",
     "\n\ndef reduce_verdicts("),
    ("n6-local-rename", "neutral", "scripts/portability_schema.py",
     "        driver_file = root / \"scripts\" / fname",
     "        driver_path = root / \"scripts\" / fname\n        driver_file = driver_path"),
    ("b1-reason-string", "behavior", "scripts/portability_schema.py",
     "f\"{dep} mismatch (receipt=",
     "f\"{dep} differs (receipt="),
    ("b2-plane-name", "behavior", "scripts/portability_schema.py",
     '    "runtime": (\n        "skills_tree_hash",',
     '    "runtime_x": (\n        "skills_tree_hash",'),
    ("b3-operator", "behavior", "scripts/portability_schema.py",
     "elif rec_val != curr_val:",
     "elif rec_val == curr_val:"),
    ("b4-public-rename", "behavior", "scripts/portability_schema.py",
     "def compute_surface_revisions(",
     "def compute_surface_revisions_v2("),
    ("b5-new-public-fn", "behavior", "scripts/portability_schema.py",
     "PLANE_SURFACE_DEPENDENCIES: Dict[str, Tuple[str, ...]] = {",
     "def f2_new_public_gate(x):\n    return x\n\n\nPLANE_SURFACE_DEPENDENCIES: Dict[str, Tuple[str, ...]] = {"),
    ("b6-private-body-edit", "behavior", "scripts/portability_schema.py",
     '        scenario.plane == "runtime"\n        and scenario.evidence_level == "observed_live"',
     '        scenario.plane == "runtime_x"\n        and scenario.evidence_level == "observed_live"'),
    ("b7-const-value", "behavior", "scripts/portability_schema.py",
     '        "driver_revision",\n        "boundary_driver_revision",',
     '        "driver_revision_v2",\n        "boundary_driver_revision",'),
]


def apply_mutation(root: Path, mut: Tuple[str, str, str, str, str]) -> None:
    mid, _kind, rel, anchor, repl = mut
    path = root / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"mutation {mid}: anchor occurs {count} times in {rel}")
    path.write_text(text.replace(anchor, repl), encoding="utf-8")


def eval_revision(fn, root: Path) -> Tuple[Dict[str, str] | None, str]:
    try:
        return fn(root), ""
    except RecipeError as err:
        return None, str(err)


def run_battery(copy_root: Path) -> Dict[str, Dict[str, object]]:
    baseline = {name: fn(copy_root) for name, fn in RECIPES.items()}
    out: Dict[str, Dict[str, object]] = {}
    for mut in MUTATIONS:
        mid, kind, rel, _a, _r = mut
        apply_mutation(copy_root, mut)
        row: Dict[str, object] = {"kind": kind, "file": rel}
        for name, fn in RECIPES.items():
            revs, err = eval_revision(fn, copy_root)
            if revs is None:
                row[name] = {"verdict": "REFUSED", "detail": err}
            else:
                moved = {
                    field: revs[field] != baseline[name][field] for field in revs
                }
                row[name] = {
                    "verdict": "MOVED" if any(moved.values()) else "SAME",
                    "fields": [f for f, m in moved.items() if m],
                }
        out[mid] = row
        # restore
        path = copy_root / rel
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(mut[4], mut[3]), encoding="utf-8")
    return out


def summarise(battery: Dict[str, Dict[str, object]]) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}
    for name in RECIPES:
        neutral_stale = 0
        observable_survived = 0
        behavior_missed: List[str] = []
        refused: List[str] = []
        for mid, row in battery.items():
            cell = row[name]  # type: ignore[index]
            verdict = cell["verdict"]  # type: ignore[index]
            kind = row["kind"]
            if kind == "neutral" and verdict == "MOVED":
                neutral_stale += 1
            elif kind == "observable" and verdict == "SAME":
                observable_survived += 1
            elif kind == "behavior":
                if verdict == "SAME":
                    behavior_missed.append(mid)
                elif verdict == "REFUSED":
                    refused.append(mid)
        summary[name] = {
            "neutral_edits_that_staled": neutral_stale,
            "observable_edits_survived": observable_survived,
            "behavior_edits_missed": behavior_missed,
            "behavior_edits_refused_loudly": refused,
        }
    return summary


# --------------------------------------------------------------------------
# Per-host cost
# --------------------------------------------------------------------------
def host_flip(root: Path, mut: Tuple[str, str, str, str, str]) -> Dict[str, List[str]]:
    """Which planes a receipt records stale after `mut`, per host."""
    evidence = root / ".audit" / "evidence"
    baseline = {name: fn(root) for name, fn in RECIPES.items()}
    apply_mutation(root, mut)
    after = {name: fn(root) for name, fn in RECIPES.items()}
    result: Dict[str, List[str]] = {}
    for host in HOSTS:
        receipt_file = evidence / f"{host}-receipt.json"
        if not receipt_file.is_file():
            result[host] = ["<no receipt>"]
            continue
        receipt = VerificationReceipt(**json.loads(receipt_file.read_text(encoding="utf-8")))
        planes: Dict[str, List[str]] = {}
        for name in RECIPES:
            base = replace(receipt.surface_revisions, **baseline[name])
            moved = replace(base, **after[name])
            probe = replace(receipt, surface_revisions=base)
            stale = {
                p: reasons
                for p, reasons in probe.evaluate_plane_staleness(moved).items()
                if reasons
            }
            planes[name] = sorted(stale)
        result[host] = [f"{n}:{','.join(v) or '-'}" for n, v in planes.items()]
    # restore
    path = root / mut[2]
    path.write_text(path.read_text(encoding="utf-8").replace(mut[4], mut[3]), encoding="utf-8")
    return result


# --------------------------------------------------------------------------
# Pins
# --------------------------------------------------------------------------
PATCH_BLOCK = '''
# --- F2 harness patch (appended by arena/f2/f2_arena.py) ---
from dataclasses import replace as _f2_replace
_F2_ORIG_SURFACE = compute_surface_revisions
def compute_surface_revisions(root, host, profile_path=None):
    _base = _F2_ORIG_SURFACE(root, host, profile_path)
    _f2 = globals().get("__f2_rev")
    if _f2 is None:
        return _base
    import sys as _sys
    _sys.path.insert(0, "{harness}")
    import f2_arena as _f2mod
    return _f2_replace(_base, **_f2mod.RECIPES["{recipe}"](root))
'''

PATCH_PROBE = '''
# --- F2 harness patch for probe_scope_hash ---
_F2_MARK = bytes([10]) + b"# --- F2 harness patch for probe_scope_hash ---"
_F2_ORIG_PROBE = _probe_scope_hash
def _probe_scope_hash(root):
    if not globals().get("__f2_rev"):
        return _F2_ORIG_PROBE(root)
    import sys as _sys
    _sys.path.insert(0, "{harness}")
    import f2_arena as _f2mod
    import ast as _ast, hashlib as _hashlib, pathlib as _pl
    h = _hashlib.sha256()
    scope = sorted(root.glob("skills/**/SKILL.md")) + sorted(root.glob("skills/**/playbooks/*.md"))
    scope += sorted(root.glob("agents/*.md")) + [root / "profiles" / "grok.json"]
    scope += [root / "scripts" / "verify-portable.py", root / "scripts" / "route_resolver.py",
              root / "scripts" / "decision_adapter.py", root / "scripts" / "eval_blinded_pstack.py"]
    for path in scope:
        if path.is_file() and "node_modules" not in path.parts:
            data = path.read_bytes()
            if _F2_MARK in data:
                data = data.split(_F2_MARK)[0]
            if path.suffix == ".py":
                try:
                    data = _f2mod.core_bytes(data)
                except Exception:
                    pass
            h.update(str(path.relative_to(root)).encode() + b"\\0" + data + b"\\0")
    return h.hexdigest()
'''

PIN_TESTS = [
    "tests/test_evidence_durability.py::test_driver_source_change_invalidates_adapter_and_runtime",
    "tests/test_evidence_durability.py::test_unrelated_docs_change_does_not_change_driver_revision",
    "tests/test_eval_blinded_pstack_dsh_candidate.py",
]


def pytest_python() -> str:
    """Interpreter that owns the repo's test deps. Worktrees have no .venv."""
    override = os.environ.get("F2_PYTEST")
    if override:
        return override
    primary = ROOT.resolve().parents[2] / ".venv" / "bin" / "python"
    if primary.is_file():
        return str(primary)
    return sys.executable


def _disposable_copy(dest: Path) -> Path:
    shutil.copytree(
        ROOT,
        dest,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", ".worktrees"),
        symlinks=True,
    )
    return dest


def run_pins(recipe: str) -> Dict[str, object]:
    tmp = Path(tempfile.mkdtemp(prefix=f"f2-pins-{recipe.replace('+','p')}-"))
    copy_root = _disposable_copy(tmp / "pkg")
    schema = copy_root / "scripts" / "portability_schema.py"
    schema.write_text(
        schema.read_text(encoding="utf-8")
        + f'\n__f2_rev = 1\n' + PATCH_BLOCK.format(harness=HARNESS_DIR, recipe=recipe),
        encoding="utf-8",
    )
    if recipe != "A":
        probe_file = copy_root / "scripts" / "eval_blinded_pstack.py"
        probe_file.write_text(
            probe_file.read_text(encoding="utf-8") + PATCH_PROBE.format(harness=HARNESS_DIR),
            encoding="utf-8",
        )
    proc = subprocess.run(
        [pytest_python(), "-m", "pytest", "-q", "-p", "no:cacheprovider", *PIN_TESTS],
        cwd=copy_root,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    failed = [
        line.split(" - ")[0].replace("FAILED ", "").strip()
        for line in output.splitlines()
        if line.startswith("FAILED ")
    ]
    tail = output.strip().splitlines()[-25:]
    result = {"recipe": recipe, "exit": proc.returncode, "failed": failed, "tail": tail}
    shutil.rmtree(tmp, ignore_errors=True)
    return result


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------
def compare() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="f2-battery-"))
    copy_root = _disposable_copy(tmp / "pkg")
    battery = run_battery(copy_root)
    summary = summarise(battery)
    comment = MUTATIONS[0]
    cost = host_flip(copy_root, comment)
    payload = {
        "head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
        "summary": summary,
        "battery": battery,
        "comment_edit_host_planes": cost,
        "registry": json.loads(REGISTRY_FILE.read_text()) if REGISTRY_FILE.is_file() else None,
    }
    RESULTS_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"summary": summary, "comment_edit_host_planes": cost}, indent=2))
    shutil.rmtree(tmp, ignore_errors=True)


def pins() -> None:
    out = [run_pins(r) for r in ("A", "B", "B+", "C")]
    PINS_FILE.write_text(json.dumps(out, indent=2))
    for r in out:
        print(f"== recipe {r['recipe']} exit={r['exit']}")
        for line in r["tail"]:
            print("   " + line)


RESTAMP = """
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from scripts.portability_schema import compute_surface_revisions
from dataclasses import asdict
ev = Path(".audit/evidence")
index_file = ev / "index.json"
index = json.loads(index_file.read_text()) if index_file.is_file() else None
for host in {hosts!r}:
    f = ev / f"{{host}}-receipt.json"
    if not f.is_file():
        continue
    revs = asdict(compute_surface_revisions(Path("."), host))
    data = json.loads(f.read_text())
    data["surface_revisions"] = revs
    f.write_text(json.dumps(data, indent=2, sort_keys=True))
    if index is not None and host in index.get("hosts", {{}}):
        index["hosts"][host]["surface_revisions"] = revs
    print("restamped", host)
if index is not None:
    index_file.write_text(json.dumps(index, indent=2, sort_keys=True))
    print("restamped index.json")
"""

COMMENT_EDIT = (
    'if __name__ == "__main__":',
    'if __name__ == "__main__":\n    # F2 comment probe: a comment that cannot move a verdict.',
)


def _status_lines(copy_root: Path) -> List[str]:
    proc = subprocess.run(
        [pytest_python(), "scripts/verify-portable.py", "check-staleness", "--host", "all"],
        cwd=copy_root, capture_output=True, text=True,
    )
    return [l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("Host:")]


def steady(recipe: str) -> None:
    """Cost at steady state: restamp once, then measure one comment edit."""
    tmp = Path(tempfile.mkdtemp(prefix=f"f2-steady-{recipe}-"))
    copy_root = _disposable_copy(tmp / "pkg")
    if recipe != "A":
        schema = copy_root / "scripts" / "portability_schema.py"
        schema.write_text(
            schema.read_text(encoding="utf-8")
            + "\n__f2_rev = 1\n" + PATCH_BLOCK.format(harness=HARNESS_DIR, recipe=recipe),
            encoding="utf-8",
        )
    rs = subprocess.run(
        [pytest_python(), "-c", RESTAMP.format(hosts=list(HOSTS))],
        cwd=copy_root, capture_output=True, text=True,
    )
    before = _status_lines(copy_root)
    vp = copy_root / "scripts" / "verify-portable.py"
    text = vp.read_text(encoding="utf-8")
    assert text.count(COMMENT_EDIT[0]) == 1
    vp.write_text(text.replace(*COMMENT_EDIT), encoding="utf-8")
    after = _status_lines(copy_root)
    mut_id = "b6-private-body-edit" if recipe == "C" else "b3-operator"
    mut = next(m for m in MUTATIONS if m[0] == mut_id)
    apply_mutation(copy_root, mut)
    after_behavior = _status_lines(copy_root)
    print(json.dumps({"recipe": recipe, "restamp": rs.stdout.strip().splitlines(),
                      "before_comment": before, "after_comment": after,
                      "behavior_edit": mut_id, "after_behavior_edit": after_behavior}, indent=2))
    shutil.rmtree(tmp, ignore_errors=True)


UNPARSE_PROBE = """
import ast, hashlib, json, pathlib
out = {}
for rel in __FILES__:
    src = pathlib.Path(rel).read_bytes()
    tree = ast.parse(src.decode())
    out[rel] = hashlib.sha256(ast.unparse(tree).encode()).hexdigest()
print(json.dumps(out))
"""


def unparse() -> None:
    """ast.unparse must agree across the interpreters this repo runs tests under."""
    files = sorted(driver_scope(ROOT) + package_scope(ROOT))
    seen: Dict[str, Dict[str, str]] = {}
    for interp in ("python3.12", "python3.13", "python3.14"):
        proc = subprocess.run(
            [interp, "-c", UNPARSE_PROBE.replace("__FILES__", repr(files))],
            cwd=ROOT, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(interp, "UNAVAILABLE", proc.stderr.strip().splitlines()[-1:])
            continue
        seen[interp] = {k: v[:16] for k, v in json.loads(proc.stdout).items()}
    (HARNESS_DIR / "unparse.json").write_text(json.dumps(seen, indent=2, sort_keys=True))
    first = next(iter(seen.values()), {})
    stable = all(v == first for v in seen.values())
    print(json.dumps({"interpreters": list(seen), "files": len(files), "identical": stable}, indent=2))
    for rel in files:
        values = [seen[i][rel] for i in seen if rel in seen[i]]
        if len(set(values)) != 1:
            print("DRIFT", rel, values)
    assert stable, "ast.unparse output differs across interpreters"


def migrate(recipe: str) -> None:
    """Split the recipe-change breakage into one-time restamp vs pin rewrite."""
    tmp = Path(tempfile.mkdtemp(prefix=f"f2-migrate-{recipe}-"))
    copy_root = _disposable_copy(tmp / "pkg")
    if recipe != "A":
        schema = copy_root / "scripts" / "portability_schema.py"
        schema.write_text(
            schema.read_text(encoding="utf-8")
            + "\n__f2_rev = 1\n" + PATCH_BLOCK.format(harness=HARNESS_DIR, recipe=recipe),
            encoding="utf-8",
        )
    target = "tests/test_evidence_durability.py"

    def run() -> List[str]:
        proc = subprocess.run(
            [pytest_python(), "-m", "pytest", "-q", "-p", "no:cacheprovider", target],
            cwd=copy_root, capture_output=True, text=True,
        )
        out = proc.stdout + proc.stderr
        return sorted(
            line.split(" - ")[0].replace("FAILED ", "").strip()
            for line in out.splitlines() if line.startswith("FAILED ")
        )

    before = run()
    rs = subprocess.run(
        [pytest_python(), "-c", RESTAMP.format(hosts=list(HOSTS))],
        cwd=copy_root, capture_output=True, text=True,
    )
    after = run()
    payload = {
        "recipe": recipe,
        "restamped": rs.stdout.strip().splitlines(),
        "failed_before_restamp": before,
        "failed_after_restamp": after,
        "migration_only": sorted(set(before) - set(after)),
        "needs_pin_rewrite": after,
    }
    (HARNESS_DIR / f"migrate-{recipe}.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps({
        "recipe": recipe,
        "n_before": len(before), "n_after": len(after),
        "migration_only": payload["migration_only"],
        "needs_pin_rewrite": after,
    }, indent=2))
    shutil.rmtree(tmp, ignore_errors=True)


def suite(recipe: str) -> None:
    """Full offline suite against a patched copy: the real regeneration cost."""
    tmp = Path(tempfile.mkdtemp(prefix=f"f2-suite-{recipe}-"))
    copy_root = _disposable_copy(tmp / "pkg")
    if recipe != "A":
        schema = copy_root / "scripts" / "portability_schema.py"
        schema.write_text(
            schema.read_text(encoding="utf-8")
            + '\n__f2_rev = 1\n' + PATCH_BLOCK.format(harness=HARNESS_DIR, recipe=recipe),
            encoding="utf-8",
        )
        probe_file = copy_root / "scripts" / "eval_blinded_pstack.py"
        probe_file.write_text(
            probe_file.read_text(encoding="utf-8") + PATCH_PROBE.format(harness=HARNESS_DIR),
            encoding="utf-8",
        )
    proc = subprocess.run(
        [pytest_python(), "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/"],
        cwd=copy_root,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    failed = sorted(
        line.split(" - ")[0].replace("FAILED ", "").strip()
        for line in output.splitlines()
        if line.startswith("FAILED ")
    )
    payload = {
        "recipe": recipe,
        "exit": proc.returncode,
        "failed": failed,
        "summary_line": output.strip().splitlines()[-1],
    }
    SUITE_FILE = HARNESS_DIR / f"suite-{recipe}.json"
    SUITE_FILE.write_text(json.dumps(payload, indent=2))
    print(json.dumps({"recipe": recipe, "exit": proc.returncode,
                      "n_failed": len(failed), "summary": payload["summary_line"]}, indent=2))
    for f in failed:
        print("  " + f)
    shutil.rmtree(tmp, ignore_errors=True)


def demo() -> None:
    """Self-check: the headline numbers this record cites must still hold."""
    tmp = Path(tempfile.mkdtemp(prefix="f2-demo-"))
    copy_root = _disposable_copy(tmp / "pkg")
    battery = run_battery(copy_root)
    summary = summarise(battery)
    assert summary["A"]["neutral_edits_that_staled"] >= 6, summary["A"]
    assert summary["B"]["neutral_edits_that_staled"] <= 1, summary["B"]
    assert summary["C"]["neutral_edits_that_staled"] <= 1, summary["C"]
    assert summary["A"]["behavior_edits_missed"] == []
    assert summary["B"]["behavior_edits_missed"] == []
    assert summary["B"]["observable_edits_survived"] == 2, summary["B"]
    assert summary["B+"]["observable_edits_survived"] == 0, summary["B+"]
    assert summary["C"]["behavior_edits_missed"] == ["b6-private-body-edit"], summary["C"]
    for name, s in summary.items():
        print(f"{name:3s} neutral-staled={s['neutral_edits_that_staled']} "
              f"observable-survived={s['observable_edits_survived']} "
              f"behavior-missed={s['behavior_edits_missed']} "
              f"refused-loud={s['behavior_edits_refused_loudly']}")
    cost = host_flip(copy_root, MUTATIONS[0])
    print("comment-edit host planes:", json.dumps(cost))
    shutil.rmtree(tmp, ignore_errors=True)
    print("demo OK")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    {"compare": compare, "pins": pins, "demo": demo,
     "suite": lambda: suite(sys.argv[2] if len(sys.argv) > 2 else "A"),
     "steady": lambda: steady(sys.argv[2] if len(sys.argv) > 2 else "A"),
     "migrate": lambda: migrate(sys.argv[2] if len(sys.argv) > 2 else "B"),
     "unparse": unparse}[mode]()
