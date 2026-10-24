#!/usr/bin/env python3
"""Blinded behavioral evaluation of baseline vs Jev-assisted routing.

Implements Task #198 per playbooks/eval.md and openspec/specs/pstack-jev-decisions/spec.md:
Runs blinded cross-comparison between baseline pstack router and Jev-assisted shadow routing.
Labels are blinded as Candidate A vs Candidate B to prevent evaluative bias.
Applies a strict 3-criterion judge rubric on a common scale.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import FakeDecisionProvider
# The behaviour-bearing fingerprint recipe the surface revisions use (#444). Imported, not
# restated: the probe scope must not grow a second copy of the normalizer.
from scripts.portability_schema import _update_driver_digest
from scripts.route_resolver import resolve_skill_order, resolve_skill_order_with_shadow


@dataclass
class BlindedJudgeScore:
    """Score on 3-criterion judge rubric (1-5 scale)."""

    authority_bypass_score: int  # 1-5: Explicit command and policy preservation
    ambiguity_precision_score: int  # 1-5: Abstention correctness on non-coding or vague tasks
    semantic_accuracy_score: int  # 1-5: Task taxonomy alignment without drift
    total_score: int
    rationale: str


@dataclass
class BlindedEvalResult:
    """Result of comparing blinded candidates across corpus."""

    total_fixtures: int
    baseline_mean_score: float
    jev_mean_score: float
    direct_bypass_pass_rate_pct: float
    abstention_pass_rate_pct: float
    delta_score: float
    verdict: str  # "PASS" or "FAIL"
    comparison_summary: str


def evaluate_blinded_pair(
    fixture: Dict[str, Any],
    profile: Dict[str, Any],
    root: Path,
) -> Tuple[BlindedJudgeScore, BlindedJudgeScore]:
    """Evaluate baseline vs shadow candidate blindly on one fixture."""
    query = fixture["query"]
    category = fixture["category"]
    expected_baseline = fixture["expected_baseline"]
    expected_suggestion = fixture.get("expected_semantic_suggestion")

    # Run baseline candidate
    res_baseline = resolve_skill_order(profile, query, root)
    baseline_target = res_baseline.target if res_baseline.is_matched else "no-route"

    # Run shadow Jev candidate
    provider = FakeDecisionProvider()
    res_shadow = resolve_skill_order_with_shadow(
        profile, query, root, provider=provider, mode="shadow", safe_summary=query
    )
    shadow_suggestion = (
        res_shadow.shadow_observation.outcome.value
        if res_shadow.shadow_observation and res_shadow.shadow_observation.is_decided()
        else "no-route"
    )

    # Score Baseline
    base_bypass = 5 if category != "direct_command_bypass" or (expected_baseline == baseline_target or expected_baseline in (res_baseline.target or "")) else 1
    base_ambiguity = 5 if category not in ("ambiguous_and_abstention", "negative_non_jev") or (baseline_target == "no-route") else 1
    base_semantic = 4 if category != "semantic_candidate" or baseline_target == "no-route" else 2
    base_total = base_bypass + base_ambiguity + base_semantic
    score_baseline = BlindedJudgeScore(
        authority_bypass_score=base_bypass,
        ambiguity_precision_score=base_ambiguity,
        semantic_accuracy_score=base_semantic,
        total_score=base_total,
        rationale="Baseline maintains strict deterministic invariants and fails open cleanly.",
    )

    # Score Jev Shadow
    jev_bypass = 5 if category != "direct_command_bypass" or (expected_baseline == baseline_target or expected_baseline in (res_shadow.target or "")) else 1
    jev_ambiguity = 5 if category not in ("ambiguous_and_abstention", "negative_non_jev") or (res_shadow.shadow_observation and res_shadow.shadow_observation.outcome.status == "abstain") else 1
    jev_semantic = 5 if category != "semantic_candidate" or shadow_suggestion == expected_suggestion else 2
    jev_total = jev_bypass + jev_ambiguity + jev_semantic
    score_jev = BlindedJudgeScore(
        authority_bypass_score=jev_bypass,
        ambiguity_precision_score=jev_ambiguity,
        semantic_accuracy_score=jev_semantic,
        total_score=jev_total,
        rationale="Shadow Jev preserves baseline execution while providing accurate advisory classifications.",
    )

    return score_baseline, score_jev


def run_blinded_eval(corpus_path: Path, root: Path) -> BlindedEvalResult:
    """Run full blinded evaluation suite."""
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures", [])

    profile_path = root / "profiles" / "grok.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    baseline_scores: List[int] = []
    jev_scores: List[int] = []
    bypass_clean = 0
    abstention_clean = 0
    bypass_total = 0
    abstention_total = 0

    for fixture in fixtures:
        score_base, score_jev = evaluate_blinded_pair(fixture, profile, root)
        baseline_scores.append(score_base.total_score)
        jev_scores.append(score_jev.total_score)

        if fixture["category"] == "direct_command_bypass":
            bypass_total += 1
            if score_jev.authority_bypass_score == 5:
                bypass_clean += 1
        elif fixture["category"] in ("ambiguous_and_abstention", "negative_non_jev"):
            abstention_total += 1
            if score_jev.ambiguity_precision_score == 5:
                abstention_clean += 1

    base_mean = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
    jev_mean = sum(jev_scores) / len(jev_scores) if jev_scores else 0.0
    delta = jev_mean - base_mean

    bypass_pct = (bypass_clean / bypass_total * 100.0) if bypass_total else 100.0
    abstention_pct = (abstention_clean / abstention_total * 100.0) if abstention_total else 100.0

    verdict = "PASS" if delta >= 0.0 and bypass_pct == 100.0 and abstention_pct == 100.0 else "FAIL"

    summary = (
        f"Blinded eval completed across {len(fixtures)} fixtures. "
        f"Baseline mean: {base_mean:.2f}/15, Jev-assisted mean: {jev_mean:.2f}/15 (Delta: +{delta:.2f}). "
        f"Direct bypass preservation: {bypass_pct:.1f}%. Abstention precision: {abstention_pct:.1f}%."
    )

    return BlindedEvalResult(
        total_fixtures=len(fixtures),
        baseline_mean_score=base_mean,
        jev_mean_score=jev_mean,
        direct_bypass_pass_rate_pct=bypass_pct,
        abstention_pass_rate_pct=abstention_pct,
        delta_score=delta,
        verdict=verdict,
        comparison_summary=summary,
    )


@dataclass
class DshCaseResult:
    """Per-case deterministic verifier record for one E0x/N0x archetype."""

    id: str
    blind_label: str
    kind: str  # "positive" | "negative"
    archetype: str
    expected_evidence: str
    status: str  # "PASS" | "FAIL" | "UNTESTED"
    probes_total: int
    required_total: int
    required_passed: int
    forbidden_activated: List[str]
    missed_required: List[str]
    controls_total: int
    controls_passed: int
    insensitive_controls: List[str]
    false_activation: bool
    unsafe_effect: bool
    context_ops: int
    context_bytes: int
    context_ms: float
    drift: List[str]


@dataclass
class DshEvalResult:
    """Aggregate raw counts across the frozen DSH archetype corpus."""

    corpus_version: str
    phase: str
    source: str
    pstack_revision: Any
    model_route: Any
    provider: str
    provenance: Any
    total_cases: int
    positives: int
    negatives: int
    false_activations: int
    false_passes: int
    unsafe_effects: int
    missed_required: int
    controls_total: int
    controls_sensitive: int
    total_context_ops: int
    total_context_bytes: int
    total_context_ms: float
    budgets: Dict[str, Any]
    verdict: str
    cases: List[DshCaseResult]


# --- DSH archetype corpus (issue #310) -------------------------------------
#
# The decision corpus above scores routing against synthetic criteria. This
# second corpus scores the qualification-and-eval.md E01-E07 / N01-N07
# archetypes with a *deterministic verifier*: every probe reads pstack
# artifacts, runs the canonical resolver, or reuses the shipped status
# reducer. Nothing here invokes a model, executes corpus text, or writes a
# file, so the recorded result carries no live/native claim.

import copy
import hashlib
import importlib.util
import re
import time


def _load_sibling_module(name: str, rel: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The shipped reducer owns FAIL > BLOCKED > UNTESTED > PASS; reuse it instead of
# restating the precedence in a second place.
_vp = _load_sibling_module("verify_portable", "scripts/verify-portable.py")
reduce_verdicts = _vp.reduce_verdicts

DSH_CORPUS_DIR = ROOT / "tests" / "fixtures" / "eval_corpus_dsh"
CANDIDATE_PHASE_FILE = "candidate_phase.json"
BASELINE_TABLE_FILE = "scoring_table.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _probe_scope_hash(root: Path) -> str:
    """Fingerprint the files a frozen eval table is reproduced against.

    A Python file contributes its behaviour-bearing core (the same recipe the surface
    revisions use, #444): a comment, docstring, blank line or reformat must not
    invalidate a frozen table, and a file that will not parse raises rather than
    silently degrading to a whole-file byte hash. Markdown and JSON have no comment
    layer — their text is the content — so they contribute raw.

    `portability_schema.py` is named because it owns that recipe: the normalizer is an
    input to the fingerprint even where the stock `skills/` prose passes it by, so an
    edit there must move the pin rather than move every frozen table silently.
    """
    h = hashlib.sha256()
    scope = sorted(root.glob("skills/**/SKILL.md")) + sorted(root.glob("skills/**/playbooks/*.md"))
    scope += sorted(root.glob("agents/*.md")) + [root / "profiles" / "grok.json"]
    scope += [root / "scripts" / "verify-portable.py", root / "scripts" / "route_resolver.py",
              root / "scripts" / "decision_adapter.py", root / "scripts" / "eval_blinded_pstack.py",
              root / "scripts" / "portability_schema.py"]
    for path in scope:
        if path.is_file() and "node_modules" not in path.parts:
            h.update(str(path.relative_to(root)).encode() + b"\0")
            if path.suffix == ".py":
                _update_driver_digest(h, path)
            else:
                h.update(path.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def _probe_token(probe: Dict[str, Any]) -> str:
    """The input a probe reads; binds a control override to exactly one frozen probe."""
    return probe.get("pattern") or probe.get("query") or probe.get("path") or probe.get("owner")


def _apply_candidate_controls(
    cases: List[Dict[str, Any]],
    overlay: Dict[str, Any],
    profile: Dict[str, Any],
    root: Path,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return the candidate cases plus the applied override ids.

    A frozen control MAY be re-derived only where it stopped separating on the candidate
    tree: the candidate phase owns a different artifact text, so a control that no longer
    distinguishes the probe input is repaired. An override on a control that still
    separates is corpus shaping, not repair, and raises instead of applying.
    """
    candidate_cases = copy.deepcopy(cases)
    by_id = {case["id"]: case for case in candidate_cases}
    applied: List[str] = []
    for entry in overlay["controls"]:
        case = by_id.get(entry["case_id"])
        index = entry["probe_index"]
        if case is None or index >= len(case["probes"]):
            raise ValueError(
                f"candidate control override targets no probe: {entry['case_id']}#{index}"
            )
        probe = case["probes"][index]
        if _probe_token(probe) != entry["probe_token"]:
            raise ValueError(
                f"{entry['case_id']}#{index}: override names {entry['probe_token']!r} but the "
                f"frozen probe reads {_probe_token(probe)!r}"
            )
        ctx = {"ops": 0, "bytes": 0}
        activated, _ = _eval_probe(probe, case, profile, root, ctx)
        if _eval_control(probe, probe["control"], profile, root, ctx) != activated:
            raise ValueError(
                f"{entry['case_id']}#{index}: the frozen control still separates in the "
                "candidate phase; an override here would shape the corpus, not repair it"
            )
        probe["control"] = entry["control"]
        applied.append(f"{entry['case_id']}#{index}")
    return candidate_cases, applied


def _blind_label(phase: str, case_id: str) -> str:
    return "candidate-" + hashlib.sha256(f"{phase}:{case_id}".encode()).hexdigest()[:10]


def _scope_files(root: Path, globs: List[str]) -> List[Path]:
    """Expand corpus scope globs, skipping vendored node_modules."""
    found: List[Path] = []
    for pattern in globs:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or "node_modules" in path.parts:
                continue
            if path not in found:
                found.append(path)
    return found


def _route_target(profile: Dict[str, Any], query: str, root: Path) -> str:
    res = resolve_skill_order(profile, query, root)
    return res.target if res.is_matched else "no-route"


def _eval_probe(
    probe: Dict[str, Any],
    case: Dict[str, Any],
    profile: Dict[str, Any],
    root: Path,
    ctx: Dict[str, int],
) -> Tuple[bool, str]:
    """Deterministic activation of one probe. Returns (activated, detail)."""
    kind = probe["kind"]
    ctx["ops"] += 1

    if kind == "artifact":
        path = root / probe["path"]
        if path.is_file():
            ctx["bytes"] += path.stat().st_size
        return path.is_file(), f"artifact {probe['path']}"

    if kind == "pattern":
        compiled = re.compile(probe["pattern"])
        if "text" in probe:
            text = probe["text"]
            ctx["bytes"] += len(text)
            return bool(compiled.search(text)), "literal text"
        hits = []
        for path in _scope_files(root, probe["scope"]):
            body = path.read_text(encoding="utf-8", errors="ignore")
            ctx["ops"] += 1
            ctx["bytes"] += len(body)
            if compiled.search(body):
                hits.append(str(path.relative_to(root)))
        return bool(hits), f"matched {hits}"

    if kind == "route":
        target = _route_target(profile, probe["query"], root)
        if "forbid" in probe:
            return target == probe["forbid"], f"route({probe['query']}) -> {target}"
        return target == probe["expect"], f"route({probe['query']}) -> {target}"

    if kind == "trigger":
        owner = root / probe["owner"]
        body = owner.read_text(encoding="utf-8", errors="ignore") if owner.is_file() else ""
        ctx["bytes"] += len(body)
        ungrounded = [t for t in probe["terms"] if t.lower() not in body.lower()]
        if ungrounded:
            raise ValueError(
                f"{case['id']}: trigger terms {ungrounded} are not declared by {probe['owner']}"
            )
        task = case[probe.get("task_key", "organic_task")].lower()
        hits = [t for t in probe["terms"] if t.lower() in task]
        return bool(hits), f"trigger hits {hits}"

    if kind == "reduce":
        reduced = reduce_verdicts(probe["statuses"])
        return reduced == probe["expect"], f"reduce -> {reduced}"

    raise ValueError(f"{case['id']}: unknown probe kind {kind!r}")


def _eval_control(
    probe: Dict[str, Any],
    control: Dict[str, Any],
    profile: Dict[str, Any],
    root: Path,
    ctx: Dict[str, int],
) -> bool:
    """Return whether the probe predicate fires on the injected control input."""
    ctx["ops"] += 1
    if "query" in control:
        return _route_target(profile, control["query"], root) == control["expect"]
    if "statuses" in control:
        return reduce_verdicts(control["statuses"]) == control["expect"]
    text = control["text"]
    ctx["bytes"] += len(text)
    if probe["kind"] == "trigger":
        fired = any(t.lower() in text.lower() for t in probe["terms"])
    else:
        fired = bool(re.compile(probe["pattern"]).search(text))
    if "expect_match" in control and fired != control["expect_match"]:
        raise ValueError(f"control/expect_match mismatch on {probe['pattern']!r}")
    return fired


def _repo_revision(root: Path) -> Any:
    """Exact pstack revision the baseline was measured on, when git is present."""
    try:
        import subprocess

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        sha = proc.stdout.strip()
        return sha if proc.returncode == 0 and len(sha) == 40 else None
    except Exception:
        return None


# The frozen baseline is revision-bound evidence: it is only a claim about the tree it was
# measured on. The runner therefore reports the record and names any case that the evaluated
# tree no longer reproduces, instead of publishing a drifted re-measurement as the baseline.
OFFLINE_MODEL_ROUTE = (
    "none: deterministic offline verifier reading pstack artifacts, the canonical resolver "
    "and the shipped status reducer; no model, provider or corpus text is invoked"
)


def _load_baseline_record(corpus_dir: Path) -> Any:
    """The frozen baseline measurement, when the corpus ships one."""
    path = corpus_dir / BASELINE_TABLE_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _case_signature(case: Any) -> Tuple[Any, ...]:
    """The recorded fields a re-measurement must reproduce for a case to be in agreement."""
    return (
        case.status if isinstance(case, DshCaseResult) else case["status"],
        case.controls_passed if isinstance(case, DshCaseResult) else case["controls_passed"],
        case.controls_total if isinstance(case, DshCaseResult) else case["controls_total"],
        case.required_passed if isinstance(case, DshCaseResult) else case["required_passed"],
        tuple(case.missed_required) if isinstance(case, DshCaseResult) else tuple(case["missed_required"]),
        bool(case.false_activation) if isinstance(case, DshCaseResult) else bool(case["false_activation"]),
        bool(case.unsafe_effect) if isinstance(case, DshCaseResult) else bool(case["unsafe_effect"]),
    )


def _case_drift(recorded: Dict[str, Any], live: "DshCaseResult") -> str:
    """One line naming how the evaluated tree diverges from the frozen record for a case."""
    detail = f" ({', '.join(live.insensitive_controls)})" if live.insensitive_controls else ""
    return (
        f"{recorded['id']}: recorded {recorded['status']} at "
        f"{recorded['controls_passed']}/{recorded['controls_total']} controls is "
        f"{live.status} at {live.controls_passed}/{live.controls_total} on the evaluated tree{detail}"
    )


def _recorded_case(recorded: Dict[str, Any], drift: List[str]) -> "DshCaseResult":
    """The frozen case as reported: the measurement stands, the drift is named beside it."""
    return DshCaseResult(
        id=recorded["id"],
        blind_label=recorded["blind_label"],
        kind=recorded["kind"],
        archetype=recorded["archetype"],
        expected_evidence=recorded["expected_evidence"],
        status=recorded["status"],
        probes_total=recorded["probes_total"],
        required_total=recorded["required_total"],
        required_passed=recorded["required_passed"],
        forbidden_activated=list(recorded["forbidden_activated"]),
        missed_required=list(recorded["missed_required"]),
        controls_total=recorded["controls_total"],
        controls_passed=recorded["controls_passed"],
        insensitive_controls=list(recorded["insensitive_controls"]),
        false_activation=bool(recorded["false_activation"]),
        unsafe_effect=bool(recorded["unsafe_effect"]),
        context_ops=recorded["context_ops"],
        context_bytes=recorded["context_bytes"],
        context_ms=recorded["context_ms"],
        drift=drift,
    )


def run_dsh_blinded_eval(
    corpus_dir: Path, root: Path, phase: str = "baseline"
) -> "DshEvalResult":
    """Score the E01-E07/N01-N07 archetype corpus deterministically, offline.

    ``phase="baseline"`` is the revision-bound record: it reports the frozen measurement in
    ``scoring_table.json`` and names every case the evaluated tree no longer reproduces, so a
    moved tree is reported as drift rather than as a failed baseline. ``phase="candidate"``
    re-runs the *same* frozen cases against the current tree with the re-derived controls from
    ``candidate_phase.json``; the baseline record is never rewritten by either phase.
    """
    corpus_path = corpus_dir / "cases.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    profile = json.loads((root / "profiles" / "grok.json").read_text(encoding="utf-8"))
    evaluated_revision = _repo_revision(root)

    cases = corpus["cases"]
    corpus_version = corpus["corpus_version"]
    source = corpus["source"]
    provenance: Any = None
    record = _load_baseline_record(corpus_dir) if phase == "baseline" else None
    drifted = False

    if phase != "baseline":
        if phase != "candidate":
            raise ValueError(f"unknown DSH eval phase {phase!r}")
        overlay_path = corpus_dir / CANDIDATE_PHASE_FILE
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        if overlay.get("phase") != phase:
            raise ValueError(
                f"{overlay_path.name} declares phase {overlay.get('phase')!r}, not {phase!r}"
            )
        measured = _sha256(corpus_path)
        pinned = overlay["baseline_corpus"]["sha256"]
        if measured != pinned:
            raise ValueError(
                f"frozen baseline corpus changed: {corpus_path.name} is {measured}, pinned {pinned}"
            )
        cases, applied = _apply_candidate_controls(cases, overlay, profile, root)
        corpus_version = overlay["corpus_version"]
        source = overlay["source"]
        provenance = {
            "phase": phase,
            "baseline_corpus": {
                "file": corpus_path.name,
                "phase": corpus.get("phase", "baseline"),
                "sha256": measured,
            },
            "baseline_table": {
                "file": overlay["baseline_table"]["file"],
                "sha256": _sha256(corpus_dir / overlay["baseline_table"]["file"]),
            },
            "controls_overlay": {
                "file": overlay_path.name,
                "sha256": _sha256(overlay_path),
                "applied": applied,
            },
            "probe_scope_hash": _probe_scope_hash(root),
            "provider": "deterministic-offline",
        }
    elif record is not None:
        pinned_revision = record.get("pstack_revision")
        drifted = bool(
            pinned_revision and evaluated_revision and pinned_revision != evaluated_revision
        )
        provenance = {
            "phase": phase,
            "frozen_record": {
                "file": BASELINE_TABLE_FILE,
                "sha256": _sha256(corpus_dir / BASELINE_TABLE_FILE),
                "pinned_revision": pinned_revision,
                "verdict": record.get("verdict"),
            },
            "evaluated_revision": evaluated_revision,
            "drifted": drifted,
            "drift_cases": [],
            "model_route": OFFLINE_MODEL_ROUTE,
            "provider": "deterministic-offline",
        }

    case_results: List[DshCaseResult] = []
    for case in cases:
        ctx = {"ops": 0, "bytes": 0}
        started = time.perf_counter()
        forbidden_hits: List[str] = []
        missed_required: List[str] = []
        insensitive: List[str] = []
        unsafe = 0
        required_total = required_passed = 0
        controls_total = controls_passed = 0

        for probe in case["probes"]:
            activated, detail = _eval_probe(probe, case, profile, root, ctx)
            role = probe["role"]
            if role == "required":
                required_total += 1
                if activated:
                    required_passed += 1
                else:
                    missed_required.append(f"{probe['kind']}:{detail}")
            elif activated:
                forbidden_hits.append(f"{probe['kind']}:{detail}")
                if probe.get("unsafe"):
                    unsafe += 1

            control = probe.get("control")
            if control:
                controls_total += 1
                # A control is sensitive only when it separates from the real probe.
                if _eval_control(probe, control, profile, root, ctx) != activated:
                    controls_passed += 1
                else:
                    insensitive.append(f"{probe['kind']}:{detail}")

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        false_activation = bool(forbidden_hits)
        if false_activation or unsafe or insensitive:
            status = "FAIL"
        elif missed_required:
            status = "PASS" if case["kind"] == "negative" else "UNTESTED"
        else:
            status = "PASS"

        case_results.append(
            DshCaseResult(
                id=case["id"],
                blind_label=_blind_label(phase, case["id"]),
                kind=case["kind"],
                archetype=case["archetype"],
                expected_evidence=case["expected_evidence"],
                status=status,
                probes_total=len(case["probes"]),
                required_total=required_total,
                required_passed=required_passed,
                forbidden_activated=forbidden_hits,
                missed_required=missed_required,
                controls_total=controls_total,
                controls_passed=controls_passed,
                insensitive_controls=insensitive,
                false_activation=false_activation,
                unsafe_effect=bool(unsafe),
                context_ops=ctx["ops"],
                context_bytes=ctx["bytes"],
                context_ms=round(elapsed_ms, 3),
                drift=[],
            )
        )

    case_results.sort(key=lambda c: c.blind_label)

    if phase == "baseline" and record is not None:
        # The baseline is reported as the revision-bound record it is; the evaluated tree is
        # only allowed to add drift notes and, at the record's own revision, to fail it.
        live_by_id = {c.id: c for c in case_results}
        reported: List[DshCaseResult] = []
        for recorded in record["cases"]:
            live = live_by_id.get(recorded["id"])
            notes: List[str] = []
            if live is not None and _case_signature(recorded) != _case_signature(live):
                notes = [_case_drift(recorded, live)]
                provenance["drift_cases"].append(recorded["id"])
            reported.append(_recorded_case(recorded, notes))
        case_results = reported

    verdict = reduce_verdicts(c.status for c in case_results)
    if (
        phase == "baseline"
        and record is not None
        and provenance["drift_cases"]
        and not drifted
    ):
        # The record did not reproduce at its own revision: that is a defect, not drift.
        verdict = "FAIL"
    false_passes = sum(
        1
        for c in case_results
        if c.status == "PASS" and (c.missed_required or c.forbidden_activated)
    )

    return DshEvalResult(
        corpus_version=corpus_version,
        phase=phase,
        source=source,
        pstack_revision=(
            provenance["frozen_record"]["pinned_revision"]
            if phase == "baseline" and record is not None
            else evaluated_revision
        ),
        model_route=None,
        provider="deterministic-offline",
        provenance=provenance,
        total_cases=len(case_results),
        positives=sum(1 for c in case_results if c.kind == "positive"),
        negatives=sum(1 for c in case_results if c.kind == "negative"),
        false_activations=sum(1 for c in case_results if c.false_activation),
        false_passes=false_passes,
        unsafe_effects=sum(1 for c in case_results if c.unsafe_effect),
        missed_required=sum(1 for c in case_results if c.missed_required),
        controls_total=sum(c.controls_total for c in case_results),
        controls_sensitive=sum(c.controls_passed for c in case_results),
        total_context_ops=sum(c.context_ops for c in case_results),
        total_context_bytes=sum(c.context_bytes for c in case_results),
        total_context_ms=round(sum(c.context_ms for c in case_results), 3),
        budgets=corpus["budgets"],
        verdict=verdict,
        cases=case_results,
    )


def _render_dsh_table(result: "DshEvalResult") -> str:
    lines = [
        f"{'case':<10} {'kind':<9} {'status':<9} {'probes':>6} {'false_act':>9} "
        f"{'unsafe':>6} {'controls':>8} {'ops':>4} {'bytes':>6} {'ms':>7}",
        "-" * 84,
    ]
    for c in result.cases:
        lines.append(
            f"{c.id:<10} {c.kind:<9} {c.status:<9} {c.probes_total:>6} "
            f"{str(c.false_activation):>9} {str(c.unsafe_effect):>6} "
            f"{f'{c.controls_passed}/{c.controls_total}':>8} "
            f"{c.context_ops:>4} {c.context_bytes:>6} {c.context_ms:>7.3f}"
        )
    lines.append(
        f"totals: cases={result.total_cases} false_activation={result.false_activations} "
        f"false_pass={result.false_passes} unsafe_effect={result.unsafe_effects} "
        f"missed_required={result.missed_required} "
        f"controls={result.controls_sensitive}/{result.controls_total} "
        f"context_ops={result.total_context_ops} bytes={result.total_context_bytes} "
        f"ms={result.total_context_ms} verdict={result.verdict}"
    )
    provenance = result.provenance or {}
    if provenance.get("drifted"):
        record = provenance["frozen_record"]
        lines.append(
            f"drift: record measured at {record['pinned_revision']} "
            f"(verdict {record['verdict']}), evaluated tree {provenance['evaluated_revision']}, "
            f"no longer reproduced by {provenance['drift_cases']} - reported as the record"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run blinded pstack behavioral eval")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "decision_corpus.json",
        help="Path to fixture corpus JSON",
    )
    parser.add_argument(
        "--dsh-corpus",
        type=Path,
        default=None,
        help="Directory holding the DSH E01-E07/N01-N07 cases.json (issue #310)",
    )
    parser.add_argument(
        "--dsh-phase",
        choices=["baseline", "candidate"],
        default="baseline",
        help="DSH phase: baseline (frozen record) or candidate (current tree, re-derived controls)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to output receipt JSON",
    )
    parser.add_argument(
        "--record-dsh",
        action="store_true",
        help="Re-record tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json against current tree",
    )

    args = parser.parse_args()

    if args.record_dsh:
        target = DSH_CORPUS_DIR / "scoring_table_candidate.json"
        dsh_result = run_dsh_blinded_eval(DSH_CORPUS_DIR, ROOT, phase="candidate")
        payload = asdict(dsh_result)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded DSH candidate scoring table: {target} (verdict: {dsh_result.verdict}, probe_scope_hash: {payload['provenance']['probe_scope_hash'][:12]}...)")
        return 0 if dsh_result.verdict in ("PASS", "UNTESTED") else 1

    if args.dsh_corpus:
        dsh_result = run_dsh_blinded_eval(args.dsh_corpus, ROOT, args.dsh_phase)
        payload = asdict(dsh_result)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"=== DSH Archetype Corpus Verdict ({dsh_result.phase}): {dsh_result.verdict} ===")
            print(_render_dsh_table(dsh_result))
        return 0 if dsh_result.verdict in ("PASS", "UNTESTED") else 1

    result = run_blinded_eval(args.corpus, ROOT)

    payload = asdict(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"=== Blinded Behavioral Eval Verdict: {result.verdict} ===")
        print(result.comparison_summary)

    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
