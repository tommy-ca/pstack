"""Negative witnesses for Agnix static policy and bounded verdict acceptance."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts import agnix_guard as guard


def receipt(*, version: str = guard.VERSION, files: int = guard.MIN_FILES,
            errors: int = 0, warnings: int = 0) -> dict:
    return {
        "version": version,
        "files_checked": files,
        "summary": {"errors": errors, "warnings": warnings, "info": 0},
        "diagnostics": ([{"level": "error", "rule": "AS-001"}] if errors else []),
    }


class AgnixGuardTest(unittest.TestCase):
    def test_reviewed_policy_and_mise_pin(self) -> None:
        self.assertEqual(guard.policy_errors(guard.ROOT), [])

    def test_missing_or_malformed_receipts_never_pass(self) -> None:
        for bad in ([], {}, {"version": guard.VERSION}, {"summary": {}, "diagnostics": []},
                    {"version": guard.VERSION, "files_checked": False,
                     "summary": {"errors": 0, "warnings": 0, "info": 0}, "diagnostics": []}):
            with self.subTest(bad=bad):
                self.assertTrue(guard.receipt_errors(bad, 0))

    def test_bad_version_and_vacuous_coverage_rejected(self) -> None:
        self.assertTrue(guard.receipt_errors(receipt(version="0.0.0"), 0))
        self.assertTrue(guard.receipt_errors(receipt(files=0), 0))
        self.assertTrue(guard.receipt_errors(receipt(files=guard.MIN_FILES-1), 0))

    def test_error_and_failing_exit_are_rejected(self) -> None:
        self.assertTrue(guard.receipt_errors(receipt(errors=1), 0))
        self.assertTrue(guard.receipt_errors(receipt(), 1))
        self.assertTrue(guard.receipt_errors(receipt(warnings=2), 0, 1))

    def test_warnings_are_visible_but_not_yet_zero_budgeted(self) -> None:
        self.assertEqual(guard.receipt_errors(receipt(warnings=2), 0), [])
        self.assertEqual(guard.receipt_errors(receipt(warnings=1), 0, 1), [])

    def test_bounded_real_code_verdict_and_failing_mutant(self) -> None:
        states, failures = guard.bounded_model()
        self.assertEqual(states, 216)
        self.assertEqual(failures, [])

    def test_policy_rejects_blanket_exclusion_and_disabled_rules(self) -> None:
        source = (guard.ROOT / ".agnix.toml").read_text(encoding="utf-8")
        mise = (guard.ROOT / "mise.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "mise.toml").write_text(mise, encoding="utf-8")
            for mutated in (
                source.replace('".git/**",', '"**",'),
                source.replace("disabled_rules = []", 'disabled_rules = ["AS-001"]'),
                source.replace('severity = "Warning"', 'severity = "Info"'),
                source + '\n[[overrides]]\npaths = ["skills/**"]\ndisabled_rules = ["AS-001"]\n',
                source.replace('include_as_generic = ["droids/*.md"]',
                               'include_as_generic = []'),
            ):
                with self.subTest(mutated=mutated[-120:]):
                    (root / ".agnix.toml").write_text(mutated, encoding="utf-8")
                    self.assertTrue(guard.policy_errors(root))

    def test_binary_never_falls_back_to_node_modules(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch) / "node_modules" / ".bin"
            folder.mkdir(parents=True)
            candidate = folder / "agnix"
            candidate.write_text("stub", encoding="utf-8")
            self.assertIsNone(guard.resolve_binary(candidate))


if __name__ == "__main__":
    unittest.main()
