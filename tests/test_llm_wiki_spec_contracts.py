"""Offline proposed CandidateEnvelope contract tests: not runtime wiki admission.

A Draft202012Validator PASS says a synthetic object has valid JSON shape.
It cannot prove matching source bytes, rights or authenticated review.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT / "openspec/changes/2026-10-31-llm-wiki-reference-contracts"
SCHEMA = CHANGE / "schemas/candidate-envelope.v1.schema.json"


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


@pytest.fixture
def valid_candidate() -> dict:
    """Hex values are synthetic placeholders, not actual computed evidence."""
    return {
        "schema_version": 1,
        "candidate_id": "synthesis.alpha-001",
        "kind": "synthesis",
        "state": "proposed",
        "target_path": "wiki/syntheses/alpha.md",
        "content_sha256": "a" * 64,
        "source_revisions": [{
            "source_id": "fixture:primary",
            "uri": "repo:docs/research/llm-wiki-architecture.md",
            "sha256": "b" * 64,
            "rights": "repository",
            "captured_at": "2026-10-31T15:00:00Z",
        }],
        "target_precondition": {"not_exists": True},
        "review": {"hold_reasons": ["rights-unverified"]},
        "citations": [{"source_id": "fixture:primary", "start_line": 2, "end_line": 4}],
        "derived_from": {"engine": "atomicstrata", "version": "1.5.0"},
    }


def test_candidate_schema_is_valid_draft2020(validator: Draft202012Validator) -> None:
    assert validator.schema["$schema"].endswith("/draft/2020-12/schema")


def test_synthetic_candidate_shape_passes(validator: Draft202012Validator, valid_candidate: dict) -> None:
    validator.validate(valid_candidate)


def test_existing_target_cas_alternative(validator: Draft202012Validator, valid_candidate: dict) -> None:
    valid_candidate["target_precondition"] = {"sha256": "c" * 64}
    validator.validate(valid_candidate)


@pytest.mark.parametrize("change", [
    {"schema_version": 99},
    {"state": "published"},
    {"kind": "totally-unknown"},
    {"content_sha256": "not-a-digest"},
    {"source_revisions": []},
    {"target_path": "../private/file.md"},
    {"target_path": "wiki/concepts/../outside.md"},
    {"target_precondition": {}},
    {"target_precondition": {"not_exists": True, "sha256": "c" * 64}},
    {"review": {"hold_reasons": ["grant-authority"]}},
    {"citations": [{"source_id": "fixture:primary", "start_line": 0, "end_line": 1}]},
    {"citations": [{"source_id": "fixture:primary", "start_line": 1}]},
    {"source_revisions": [{"source_id": "test", "uri": "file", "sha256": "b" * 64}]},
    {"unknown_publisher_override": True},
])
def test_invalid_contracts_fail_closed(
    validator: Draft202012Validator, valid_candidate: dict, change: dict,
) -> None:
    specimen = copy.deepcopy(valid_candidate)
    specimen.update(change)
    with pytest.raises(ValidationError):
        validator.validate(specimen)


def test_required_formal_specs_present_with_source_refs() -> None:
    spec = (CHANGE / "specs/llm-wiki/spec.md").read_text(encoding="utf-8")
    design = (CHANGE / "design.md").read_text(encoding="utf-8")
    for n in range(1, 11):
        assert f"R-WIKI-{n:03d}" in spec
    assert "0f8ff86ef0a28f4c15627a2ea5e94a96cadd834e" in design
    assert "9d974c9e4d9d6c21638a5f520e6d89f79647724e" in design
    assert "CitationNonEntailment" in design
    assert "CandidateIsolation" in design


def test_valid_schema_is_not_publisher_authorization(
    validator: Draft202012Validator, valid_candidate: dict,
) -> None:
    # A syntactically valid envelope has no signing key, authenticated
    # reviewer or source content check. Its correctness is structural only.
    validator.validate(valid_candidate)
    assert "reviewer_attestation" not in valid_candidate
    assert valid_candidate["review"]["hold_reasons"] == ["rights-unverified"]
