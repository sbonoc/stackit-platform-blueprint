"""Unit tests for upgrade_semantic_annotator.py (Slice 1 — issue-165).

Covers:
  AC-001 — function-added: kind, description names the function, hint confirms presence
  AC-002 — variable-changed: kind, description names var+value, hint confirms value
  AC-003 — no-match: kind=structural-change, hint directs manual review
  AC-004 — annotation generation error: structural-change fallback, no exception raised
  FR-001 — annotation object has kind, description, verification_hints (non-empty)
  FR-002 — kind from closed set; first matching kind returned
  FR-003 — detects function-added, function-removed, variable-changed, source-directive-added
"""

from __future__ import annotations

from pathlib import Path
import unittest

from tests._shared.helpers import REPO_ROOT
from scripts.lib.blueprint.upgrade_semantic_annotator import (
    annotate,
    KIND_FUNCTION_ADDED,
    KIND_FUNCTION_REMOVED,
    KIND_VARIABLE_CHANGED,
    KIND_SOURCE_DIRECTIVE_ADDED,
    KIND_STRUCTURAL_CHANGE,
    SemanticAnnotation,
)


FIXTURE_DIR = REPO_ROOT / "tests/blueprint/fixtures/semantic_annotator"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestAnnotateFunctionAdded(unittest.TestCase):
    """AC-001, FR-003: function-added detected when source has a new function."""

    def test_function_added_kind(self) -> None:
        baseline = _read(FIXTURE_DIR / "function_added_baseline.sh")
        source = _read(FIXTURE_DIR / "function_added_source.sh")
        result = annotate(baseline, source)
        self.assertEqual(result.kind, KIND_FUNCTION_ADDED)

    def test_function_added_description_names_function(self) -> None:
        baseline = _read(FIXTURE_DIR / "function_added_baseline.sh")
        source = _read(FIXTURE_DIR / "function_added_source.sh")
        result = annotate(baseline, source)
        self.assertIn("foo", result.description)

    def test_function_added_hints_non_empty(self) -> None:
        """FR-001: verification_hints must be non-empty."""
        baseline = _read(FIXTURE_DIR / "function_added_baseline.sh")
        source = _read(FIXTURE_DIR / "function_added_source.sh")
        result = annotate(baseline, source)
        self.assertTrue(len(result.verification_hints) > 0)
        self.assertTrue(any("foo" in h for h in result.verification_hints))


class TestAnnotateFunctionRemoved(unittest.TestCase):
    """FR-002, FR-003: function-removed detected when baseline has function absent from source."""

    def test_function_removed_kind(self) -> None:
        baseline = _read(FIXTURE_DIR / "function_removed_baseline.sh")
        source = _read(FIXTURE_DIR / "function_removed_source.sh")
        result = annotate(baseline, source)
        self.assertEqual(result.kind, KIND_FUNCTION_REMOVED)

    def test_function_removed_description_names_function(self) -> None:
        baseline = _read(FIXTURE_DIR / "function_removed_baseline.sh")
        source = _read(FIXTURE_DIR / "function_removed_source.sh")
        result = annotate(baseline, source)
        self.assertIn("baz", result.description)

    def test_function_removed_hint_warns_call_sites(self) -> None:
        baseline = _read(FIXTURE_DIR / "function_removed_baseline.sh")
        source = _read(FIXTURE_DIR / "function_removed_source.sh")
        result = annotate(baseline, source)
        self.assertTrue(any("call site" in h for h in result.verification_hints))


class TestAnnotateVariableChanged(unittest.TestCase):
    """AC-002, FR-003: variable-changed detected when an assignment value differs."""

    def test_variable_changed_kind(self) -> None:
        baseline = _read(FIXTURE_DIR / "variable_changed_baseline.sh")
        source = _read(FIXTURE_DIR / "variable_changed_source.sh")
        result = annotate(baseline, source)
        self.assertEqual(result.kind, KIND_VARIABLE_CHANGED)

    def test_variable_changed_description_names_variable_and_value(self) -> None:
        baseline = _read(FIXTURE_DIR / "variable_changed_baseline.sh")
        source = _read(FIXTURE_DIR / "variable_changed_source.sh")
        result = annotate(baseline, source)
        self.assertIn("FOO_VERSION", result.description)
        self.assertIn("2.0", result.description)

    def test_variable_changed_hint_confirms_value(self) -> None:
        baseline = _read(FIXTURE_DIR / "variable_changed_baseline.sh")
        source = _read(FIXTURE_DIR / "variable_changed_source.sh")
        result = annotate(baseline, source)
        self.assertTrue(any("2.0" in h for h in result.verification_hints))


class TestAnnotateSourceDirectiveAdded(unittest.TestCase):
    """FR-003: source-directive-added detected when source has a new source directive."""

    def test_source_directive_added_kind(self) -> None:
        baseline = _read(FIXTURE_DIR / "source_directive_baseline.sh")
        source = _read(FIXTURE_DIR / "source_directive_source.sh")
        result = annotate(baseline, source)
        self.assertEqual(result.kind, KIND_SOURCE_DIRECTIVE_ADDED)

    def test_source_directive_description_names_target(self) -> None:
        baseline = _read(FIXTURE_DIR / "source_directive_baseline.sh")
        source = _read(FIXTURE_DIR / "source_directive_source.sh")
        result = annotate(baseline, source)
        self.assertIn("helpers.sh", result.description)

    def test_source_directive_hints_non_empty(self) -> None:
        baseline = _read(FIXTURE_DIR / "source_directive_baseline.sh")
        source = _read(FIXTURE_DIR / "source_directive_source.sh")
        result = annotate(baseline, source)
        self.assertTrue(len(result.verification_hints) > 0)


class TestAnnotateNoMatch(unittest.TestCase):
    """AC-003: no specific pattern → structural-change fallback with manual review hint."""

    def test_no_match_returns_structural_change(self) -> None:
        baseline = _read(FIXTURE_DIR / "no_match_baseline.sh")
        source = _read(FIXTURE_DIR / "no_match_source.sh")
        result = annotate(baseline, source)
        self.assertEqual(result.kind, KIND_STRUCTURAL_CHANGE)

    def test_no_match_hints_direct_manual_review(self) -> None:
        baseline = _read(FIXTURE_DIR / "no_match_baseline.sh")
        source = _read(FIXTURE_DIR / "no_match_source.sh")
        result = annotate(baseline, source)
        self.assertTrue(len(result.verification_hints) > 0)
        combined = " ".join(result.verification_hints).lower()
        self.assertIn("review", combined)


class TestAnnotateAdditiveFile(unittest.TestCase):
    """FR-003 additive path: empty baseline → structural-change with additive description."""

    def test_empty_baseline_returns_structural_change(self) -> None:
        result = annotate("", "#!/usr/bin/env bash\nfunction foo() { echo 1; }\n")
        self.assertEqual(result.kind, KIND_STRUCTURAL_CHANGE)

    def test_empty_baseline_description_mentions_additive(self) -> None:
        result = annotate("", "#!/usr/bin/env bash\n")
        self.assertIn("Additive", result.description)

    def test_empty_baseline_hints_non_empty(self) -> None:
        result = annotate("", "#!/usr/bin/env bash\n")
        self.assertTrue(len(result.verification_hints) > 0)


class TestAnnotateErrorFallback(unittest.TestCase):
    """AC-004: verify structural-change returned on bad input without raising."""

    def test_none_baseline_treated_as_empty(self) -> None:
        """None baseline is falsy — same as empty-string additive path; returns structural-change."""
        result = annotate(None, "#!/usr/bin/env bash\n")  # type: ignore[arg-type]
        self.assertEqual(result.kind, KIND_STRUCTURAL_CHANGE)

    def test_as_dict_round_trips(self) -> None:
        """FR-001: as_dict() serialises all required fields."""
        ann = annotate("", "#!/usr/bin/env bash\n")
        d = ann.as_dict()
        self.assertIn("kind", d)
        self.assertIn("description", d)
        self.assertIn("verification_hints", d)
        self.assertIsInstance(d["verification_hints"], list)
        self.assertTrue(len(d["verification_hints"]) > 0)
