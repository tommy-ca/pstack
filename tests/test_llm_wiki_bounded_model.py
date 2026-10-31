"""Evidence that bounded source-mutation verification checks production ingest."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.llm_wiki import ingest_file
from scripts.verify_llm_wiki_model import broken_overwrite, explore, main


def test_bounded_actual_code_traces() -> None:
    assert explore(ingest_file) == 39


def test_bounded_negative_mutant_is_caught() -> None:
    with pytest.raises(AssertionError, match="Conflicting source was accepted"):
        explore(broken_overwrite)


def test_standalone_model_verifier_exit_status() -> None:
    assert main() == 0
