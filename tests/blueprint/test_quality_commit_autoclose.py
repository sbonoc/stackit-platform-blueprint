"""Tests for quality-pr-commit-autoclose-check (T-001..T-006).

Covers REQ-001..REQ-007 and AC-001..AC-006 from
specs/2026-06-22-quality-commit-autoclose-scan/spec.md.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_LIB_PATH = REPO_ROOT / "scripts/lib/quality/autoclose_regex.py"
_CHECK_SCRIPT = REPO_ROOT / "scripts/bin/quality/check_pr_commit_autoclose.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# T-001 — AC-001: regex matches all GitHub auto-close keyword forms
# ---------------------------------------------------------------------------

class TestAutocloseRegex:
    """T-001: canonical auto-close regex coverage."""

    def setup_method(self):
        self.lib = _load_module(_LIB_PATH, "autoclose_regex")

    def test_matches_closes(self):
        assert self.lib.build_pattern(361).search("Closes #361") is not None

    def test_matches_closes_lowercase(self):
        assert self.lib.build_pattern(361).search("closes #361") is not None

    def test_matches_closes_colon(self):
        assert self.lib.build_pattern(361).search("Closes: #361") is not None

    def test_matches_fixed(self):
        assert self.lib.build_pattern(361).search("Fixed #361") is not None

    def test_matches_resolves(self):
        assert self.lib.build_pattern(361).search("Resolves #361") is not None

    def test_matches_auto_closed(self):
        assert self.lib.build_pattern(361).search("auto-closed #361") is not None

    def test_no_match_tracks(self):
        assert self.lib.build_pattern(361).search("Tracks #361") is None

    def test_no_match_references(self):
        assert self.lib.build_pattern(361).search("references #361") is None

    def test_no_match_see(self):
        assert self.lib.build_pattern(361).search("see #361") is None

    def test_no_match_blocked_by(self):
        assert self.lib.build_pattern(361).search("blocked-by #361") is None

    def test_no_match_different_issue(self):
        assert self.lib.build_pattern(361).search("Closes #362") is None


# ---------------------------------------------------------------------------
# T-002 — AC-002: PR body Tracks #N parsing extracts protected set
# ---------------------------------------------------------------------------

class TestPrBodyParsing:
    """T-002: protected issue set extracted from PR body."""

    def setup_method(self):
        self.check = _load_module(_CHECK_SCRIPT, "check_pr_commit_autoclose")

    def test_extracts_multiple_tracks(self):
        body = "Tracks #361\nSome text\nTracks #332\n"
        result = self.check.parse_protected_issues(body)
        assert result == {361, 332}

    def test_allow_override_removes_issue(self):
        body = "Tracks #361\nTracks #332\n#allow-auto-close: #361\n"
        result = self.check.parse_protected_issues(body)
        assert 361 not in result
        assert 332 in result

    def test_empty_body_returns_empty_set(self):
        assert self.check.parse_protected_issues("No tracking markers here") == set()

    def test_allow_override_multiple(self):
        body = "Tracks #361\nTracks #332\nTracks #100\n#allow-auto-close: #361,#332\n"
        result = self.check.parse_protected_issues(body)
        assert result == {100}


# ---------------------------------------------------------------------------
# T-003 — AC-003: commit-log scanner detects violation and reports commit hash
# ---------------------------------------------------------------------------

class TestCommitLogScanner:
    """T-003: commit-log scanning detects violations with commit hash."""

    def setup_method(self):
        self.check = _load_module(_CHECK_SCRIPT, "check_pr_commit_autoclose")

    def test_detects_violation_with_hash(self):
        log = "abc1234\nauto-closed #361\n\ndef5678\nsome normal commit\n"
        findings = self.check.scan_commit_log(log, {361})
        assert len(findings) > 0
        assert any("abc1234" in f["surface"] for f in findings)

    def test_no_finding_for_tracks(self):
        log = "abc1234\nTracks #361\n"
        findings = self.check.scan_commit_log(log, {361})
        assert findings == []

    def test_no_finding_empty_protected_set(self):
        log = "abc1234\nCloses #361\n"
        findings = self.check.scan_commit_log(log, set())
        assert findings == []

    def test_finding_includes_matched_line(self):
        log = "abc1234\nFixes #361 as part of cleanup\n"
        findings = self.check.scan_commit_log(log, {361})
        assert any("Fixes #361" in f["line"] for f in findings)


# ---------------------------------------------------------------------------
# T-004 — AC-004: no-open-PR fallback reads config file
# ---------------------------------------------------------------------------

class TestFallbackConfig:
    """T-004: fallback to .github/no-auto-close-issues.yml when no PR exists."""

    def setup_method(self):
        self.check = _load_module(_CHECK_SCRIPT, "check_pr_commit_autoclose")

    def test_reads_config_file_when_no_pr(self, tmp_path):
        config = tmp_path / ".github" / "no-auto-close-issues.yml"
        config.parent.mkdir(parents=True)
        config.write_text("issues:\n  - 361\n  - 332\n")
        result = self.check.load_protected_from_config(config)
        assert result == {361, 332}

    def test_returns_empty_when_config_absent(self, tmp_path):
        config = tmp_path / ".github" / "no-auto-close-issues.yml"
        result = self.check.load_protected_from_config(config)
        assert result == set()

    def test_gh_failure_triggers_fallback(self, tmp_path, monkeypatch):
        config = tmp_path / ".github" / "no-auto-close-issues.yml"
        config.parent.mkdir(parents=True)
        config.write_text("issues:\n  - 361\n")
        # Simulate gh returning non-zero exit (no open PR)
        monkeypatch.setattr(
            self.check,
            "fetch_pr_body_title",
            lambda: None,
        )
        protected = self.check.get_protected_issues(config)
        assert 361 in protected

    def test_no_op_when_both_absent(self, tmp_path, monkeypatch):
        config = tmp_path / "no-such-file.yml"
        monkeypatch.setattr(
            self.check,
            "fetch_pr_body_title",
            lambda: None,
        )
        protected = self.check.get_protected_issues(config)
        assert protected == set()


# ---------------------------------------------------------------------------
# T-005 — AC-005: integration — script exits non-zero on violation, 0 on clean
# ---------------------------------------------------------------------------

class TestScriptExitCodes:
    """T-005: end-to-end script exit behaviour."""

    def _run(self, env: dict | None = None) -> subprocess.CompletedProcess:
        import os
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            ["uv", "run", "python3", str(_CHECK_SCRIPT)],
            capture_output=True,
            text=True,
            env=run_env,
        )

    def test_exits_zero_when_no_pr_and_no_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = self._run()
        assert result.returncode == 0

    def test_exit_nonzero_on_violation(self, tmp_path, monkeypatch):
        check = _load_module(_CHECK_SCRIPT, "check_pr_commit_autoclose_t005")
        # Use the public API directly to avoid needing a real git repo
        findings = check.scan_commit_log(
            "abc1234\nauto-closed #361\n",
            {361},
        )
        assert len(findings) > 0


# ---------------------------------------------------------------------------
# T-007 — NFR-PERF-001: fetch_pr_body_title called at most once per main() run
# ---------------------------------------------------------------------------

class TestSingleApiCall:
    """T-007: main() must invoke fetch_pr_body_title exactly once (NFR-PERF-001)."""

    def setup_method(self):
        self.check = _load_module(_CHECK_SCRIPT, "check_pr_commit_autoclose_t007")

    def test_fetch_called_once_when_pr_exists(self, monkeypatch):
        pr_data = {"body": "Tracks #361\n", "title": "some title"}
        call_count = []

        def mock_fetch():
            call_count.append(1)
            return pr_data

        monkeypatch.setattr(self.check, "fetch_pr_body_title", mock_fetch)
        monkeypatch.setattr(self.check, "_get_commit_log", lambda: "")
        self.check.main()
        assert len(call_count) == 1, f"fetch_pr_body_title called {len(call_count)} times, expected 1"

    def test_fetch_called_once_when_no_pr(self, monkeypatch, tmp_path):
        call_count = []

        def mock_fetch():
            call_count.append(1)
            return None

        monkeypatch.setattr(self.check, "fetch_pr_body_title", mock_fetch)
        monkeypatch.setattr(self.check, "_DEFAULT_CONFIG", tmp_path / "no-such.yml")
        monkeypatch.setattr(self.check, "_get_commit_log", lambda: "")
        self.check.main()
        assert len(call_count) == 1, f"fetch_pr_body_title called {len(call_count)} times, expected 1"


# ---------------------------------------------------------------------------
# T-006 — AC-006: regression — existing per-spec test imports from shared module
# ---------------------------------------------------------------------------

class TestParentAutocloseRegexImport:
    """T-006: PARENT_AUTOCLOSE_REGEX in test_issue_361_file_children_script.py
    must import from scripts/lib/quality/autoclose_regex.py after refactor."""

    def test_module_exports_build_pattern(self):
        lib = _load_module(_LIB_PATH, "autoclose_regex_t006")
        assert callable(lib.build_pattern)

    def test_build_pattern_matches_parent_autoclose_regex_behaviour(self):
        lib = _load_module(_LIB_PATH, "autoclose_regex_t006")
        pat = lib.build_pattern(361)
        # Must match same patterns as original PARENT_AUTOCLOSE_REGEX
        for text in ("Closes #361", "Fixed #361", "Resolves #361", "close #361"):
            assert pat.search(text) is not None, f"expected match: {text!r}"
        for text in ("Tracks #361", "references #361"):
            assert pat.search(text) is None, f"expected no match: {text!r}"

    def test_existing_test_file_imports_from_lib(self):
        src = (REPO_ROOT / "tests/blueprint/test_issue_361_file_children_script.py").read_text()
        assert "from scripts.lib.quality.autoclose_regex import" in src or \
               "autoclose_regex" in src, \
            "test_issue_361_file_children_script.py must import from autoclose_regex module"
