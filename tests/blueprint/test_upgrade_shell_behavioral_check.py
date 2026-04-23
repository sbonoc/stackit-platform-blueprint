"""Unit tests for upgrade_shell_behavioral_check.py (Slice 1).

Covers:
  AC-001 — syntax error in a merged script → gate fails
  AC-002 — dropped function definition → gate reports unresolved symbol
  AC-003 — all defs present → gate passes (positive-path)
  AC-004 — skip=True → gate skipped, no subprocess calls
  REQ-001 — bash -n used for syntax checking
  REQ-002 — depth-1 source resolution resolves function defs
  REQ-003 — failure output includes file, symbol, line
  REQ-010 — grep-based heuristic, no full parser
  REQ-011 — both positive-path and negative-path fixtures tested
"""

from __future__ import annotations

from pathlib import Path
import unittest

from tests._shared.helpers import REPO_ROOT
from scripts.lib.blueprint.upgrade_shell_behavioral_check import run_behavioral_check


FIXTURE_DIR = REPO_ROOT / "tests/blueprint/fixtures/shell_behavioral_check"


class TestRunBehavioralCheckPositivePath(unittest.TestCase):
    """AC-003, REQ-011: positive-path — all function defs present → pass."""

    def test_clean_script_passes(self) -> None:
        script = FIXTURE_DIR / "clean_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass")
        self.assertFalse(result.skipped)
        self.assertEqual(result.files_checked, 1)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])

    def test_sourced_file_resolves_definition(self) -> None:
        """REQ-002: function defined in depth-1 sourced file → call site resolves."""
        script = FIXTURE_DIR / "calls_sourced_helper.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckSyntaxError(unittest.TestCase):
    """AC-001, REQ-001: syntax error in merged script → gate fails."""

    def test_syntax_error_detected(self) -> None:
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "fail")
        self.assertEqual(result.unresolved_symbols, [], msg="symbol check skipped for syntax errors")
        self.assertEqual(len(result.syntax_errors), 1)
        entry = result.syntax_errors[0]
        # REQ-003: file path is present in finding
        self.assertIn("syntax_error_script.sh", entry["file"])
        self.assertIn("error", entry)
        self.assertIsInstance(entry["error"], str)
        self.assertTrue(entry["error"], "error message must be non-empty")

    def test_syntax_error_skips_symbol_check(self) -> None:
        """Files with syntax errors must not produce unresolved_symbol entries."""
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckUnresolvedSymbol(unittest.TestCase):
    """AC-002, REQ-002, REQ-003, REQ-011: dropped def → gate reports symbol."""

    def test_missing_definition_detected(self) -> None:
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "fail")
        self.assertEqual(result.syntax_errors, [], msg="no syntax errors expected")
        self.assertGreaterEqual(len(result.unresolved_symbols), 1)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertIn("setup_environment", symbols)

    def test_finding_includes_file_symbol_line(self) -> None:
        """REQ-003: each finding must include file, symbol, and line."""
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertGreaterEqual(len(result.unresolved_symbols), 1)
        for entry in result.unresolved_symbols:
            self.assertIn("file", entry)
            self.assertIn("symbol", entry)
            self.assertIn("line", entry)
            self.assertIsInstance(entry["line"], int)
            self.assertGreater(entry["line"], 0)
            self.assertIn("missing_def_script.sh", entry["file"])


class TestRunBehavioralCheckSkip(unittest.TestCase):
    """AC-004, REQ-005: skip=True → status=skipped, no subprocess calls."""

    def test_skip_returns_skipped_status(self) -> None:
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT, skip=True)

        self.assertEqual(result.status, "skipped")
        self.assertTrue(result.skipped)
        self.assertEqual(result.files_checked, 0)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])

    def test_skip_with_syntax_error_file_still_skipped(self) -> None:
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT, skip=True)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.syntax_errors, [])


class TestRunBehavioralCheckEmptyInput(unittest.TestCase):
    """Edge case: empty file list → pass with zero counts."""

    def test_empty_file_list_passes(self) -> None:
        result = run_behavioral_check([], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass")
        self.assertFalse(result.skipped)
        self.assertEqual(result.files_checked, 0)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckAsDict(unittest.TestCase):
    """Result as_dict() must include all required fields for JSON serialisation."""

    def test_as_dict_fields_present(self) -> None:
        script = FIXTURE_DIR / "clean_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)
        d = result.as_dict()

        self.assertIn("skipped", d)
        self.assertIn("files_checked", d)
        self.assertIn("syntax_errors", d)
        self.assertIn("unresolved_symbols", d)
        self.assertIn("status", d)
