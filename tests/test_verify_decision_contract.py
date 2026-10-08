from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-decision-contract.py"
A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40
E = "e" * 40
SPEC = """# Decision specification

## Purpose

Define fixture behavior.

## Requirements

### Requirement: Preserve baseline

The baseline MUST remain available.

#### Scenario: Unknown class

- **WHEN** the class is unknown
- **THEN** the baseline remains selected
"""


def fixture_data() -> tuple[dict, dict, dict]:
    registry = {
        "schema_version": 1,
        "source": {"repository": "cursor/plugins", "path_prefix": "pstack/", "revision": A, "tree": B, "router_blob": C},
        "fallback": "baseline",
        "routes": [
            {"playbook": "feature", "canonical_blob": D, "selection": "semantic_candidate", "class": "feature"},
            {"playbook": "shipping", "canonical_blob": E, "selection": "system_two"},
        ],
    }
    tree = {
        "sha": B,
        "truncated": False,
        "tree": [
            {"path": "pstack/skills/poteto-mode/SKILL.md", "sha": C, "type": "blob"},
            {"path": "pstack/skills/poteto-mode/playbooks/feature.md", "sha": D, "type": "blob"},
            {"path": "pstack/skills/poteto-mode/playbooks/shipping.md", "sha": E, "type": "blob"},
            {"path": "pstack/skills/poteto-mode/playbooks/notes.txt", "sha": A, "type": "blob"},
        ],
    }
    commit = {"sha": A, "tree": {"sha": B}}
    return registry, commit, tree


def make_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, repo / "scripts" / SCRIPT.name)
    (repo / "references").mkdir()
    playbooks = repo / "skills" / "poteto-mode" / "playbooks"
    playbooks.mkdir(parents=True)
    for name in ("feature", "shipping"):
        (playbooks / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    formal = repo / "openspec" / "specs" / "pstack-jev-decisions"
    delta = repo / "openspec" / "changes" / "pstack-jev-decision-plane" / "specs" / "pstack-jev-decisions"
    formal.mkdir(parents=True)
    delta.mkdir(parents=True)
    (formal / "spec.md").write_text(SPEC, encoding="utf-8")
    (delta / "spec.md").write_text(SPEC.replace("## Requirements", "## ADDED Requirements"), encoding="utf-8")
    registry, commit, tree = fixture_data()
    (repo / "references" / "decision-routing.json").write_text(json.dumps(registry), encoding="utf-8")
    commit_path = tmp_path / "commit.json"
    commit_path.write_text(json.dumps(commit), encoding="utf-8")
    tree_path = tmp_path / "tree.json"
    tree_path.write_text(json.dumps(tree), encoding="utf-8")
    return repo, commit_path, tree_path


def run_cli(repo: Path, commit: Path, tree: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / SCRIPT.name),
            "--root",
            str(repo),
            "--upstream-commit",
            str(commit),
            "--upstream-tree",
            str(tree),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result, json.loads(result.stdout)


def run_cli_require_clean(repo: Path, commit: Path, tree: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / SCRIPT.name),
            "--root",
            str(repo),
            "--upstream-commit",
            str(commit),
            "--upstream-tree",
            str(tree),
            "--require-clean",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result, json.loads(result.stdout)


def write_registry(repo: Path, registry: dict) -> None:
    (repo / "references" / "decision-routing.json").write_text(json.dumps(registry), encoding="utf-8")


def write_tree(path: Path, tree: dict) -> None:
    path.write_text(json.dumps(tree), encoding="utf-8")


def write_commit(path: Path, commit: dict) -> None:
    path.write_text(json.dumps(commit), encoding="utf-8")


def assert_failure(result: subprocess.CompletedProcess[str], output: dict, text: str) -> None:
    assert result.returncode == 1
    assert output["verdict"] == "FAIL"
    assert text in output["errors"][0]


def test_positive_fixture_reports_literal_scope_and_route_count(tmp_path: Path) -> None:
    repo, commit, tree = make_repo(tmp_path)
    result, output = run_cli(repo, commit, tree)

    assert result.returncode == 0, result.stdout + result.stderr
    assert output["verdict"] == "PASS"
    assert output["scope"] == "decision-contract-and-canonical-routing"
    assert output["canonical_route_count"] == 2
    assert output["source"] == {"repository": "cursor/plugins", "revision": A, "tree": B}
    assert output["upstream_commit_digest"] == hashlib.sha256(commit.read_bytes()).hexdigest()


def test_wrong_upstream_commit_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    _, commit, _ = fixture_data()
    commit["sha"] = C
    write_commit(commit_path, commit)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "does not match source.revision")


def test_mismatched_upstream_commit_tree_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    _, commit, _ = fixture_data()
    commit["tree"]["sha"] = C
    write_commit(commit_path, commit)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "does not match source.tree")


def test_missing_canonical_row_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry["routes"].pop()
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "missing=['shipping']")


@pytest.mark.parametrize("mutation", ["added", "renamed"])
def test_added_or_renamed_local_route_fails(tmp_path: Path, mutation: str) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    playbooks = repo / "skills" / "poteto-mode" / "playbooks"
    if mutation == "added":
        (playbooks / "extra.md").write_text("# extra\n", encoding="utf-8")
    else:
        (playbooks / "shipping.md").rename(playbooks / "ship.md")
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "local playbook inventory differs")


def test_wrong_source_tree_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    _, _, tree = fixture_data()
    tree["sha"] = A
    write_tree(tree_path, tree)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "does not match source.tree")


@pytest.mark.parametrize("mutation, expected", [("truncated", "truncated=false"), ("duplicate", "duplicate upstream tree path")])
def test_truncated_or_duplicate_source_fails(tmp_path: Path, mutation: str, expected: str) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    _, _, tree = fixture_data()
    if mutation == "truncated":
        tree["truncated"] = True
    else:
        tree["tree"].append(dict(tree["tree"][1]))
    write_tree(tree_path, tree)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, expected)


@pytest.mark.parametrize("mutation, expected", [("mapping", "duplicate playbook"), ("class", "duplicate semantic class")])
def test_duplicated_mapping_or_class_fails(tmp_path: Path, mutation: str, expected: str) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    if mutation == "mapping":
        registry["routes"].append(dict(registry["routes"][0]))
    else:
        registry["routes"][1] = {"playbook": "shipping", "canonical_blob": E, "selection": "semantic_candidate", "class": "feature"}
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, expected)


@pytest.mark.parametrize("field", ["illegal", "provider_policy"])
def test_illegal_field_or_provider_policy_fails(tmp_path: Path, field: str) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry[field] = "forbidden"
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, field)


def test_non_string_selection_returns_structured_failure(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry["routes"][0]["selection"] = ["semantic_candidate"]
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "selection is not allowed")


def test_boolean_schema_version_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry["schema_version"] = True
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "schema_version must equal 1")


def test_require_clean_fails_for_untracked_verifier_input(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Verifier Fixture"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "verifier@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
    (repo / "references" / "untracked-contract-input.json").write_text("{}\n", encoding="utf-8")

    result, output = run_cli_require_clean(repo, commit_path, tree_path)

    assert_failure(result, output, "--require-clean requires")
    assert output["checkout_head"] is not None
    assert output["dirty"] is True


def test_wrong_blob_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry["routes"][0]["canonical_blob"] = A
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "wrong_blob=['feature']")


def test_mapped_other_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    registry, _, _ = fixture_data()
    registry["routes"][0]["class"] = "other"
    write_registry(repo, registry)
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "class cannot be other")


def test_mismatched_spec_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    delta = repo / "openspec" / "changes" / "pstack-jev-decision-plane" / "specs" / "pstack-jev-decisions" / "spec.md"
    delta.write_text(delta.read_text(encoding="utf-8").replace("The baseline MUST remain available", "The baseline MUST change"), encoding="utf-8")
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "formal and delta decision specs differ")


def test_missing_scenario_fails(tmp_path: Path) -> None:
    repo, commit_path, tree_path = make_repo(tmp_path)
    formal = repo / "openspec" / "specs" / "pstack-jev-decisions" / "spec.md"
    formal.write_text(SPEC.split("#### Scenario:", 1)[0], encoding="utf-8")
    result, output = run_cli(repo, commit_path, tree_path)
    assert_failure(result, output, "Requirement has no Scenario")
