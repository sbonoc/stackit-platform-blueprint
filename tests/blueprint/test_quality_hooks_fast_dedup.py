"""Tests for dedup in scripts/bin/quality/hooks_fast.sh.

Slice 8 — quality-docs-lint and quality-test-pyramid dedup (AC-014, FR-013).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_FAST_SH = REPO_ROOT / "scripts/bin/quality/hooks_fast.sh"


def _read() -> str:
    return HOOKS_FAST_SH.read_text(encoding="utf-8")


class TestQualityDocsLintDedup:
    """No separate run_cmd line for quality-docs-lint (AC-014)."""

    def test_no_run_cmd_quality_docs_lint(self) -> None:
        content = _read()
        # Check for the explicit run_cmd call pattern (not inside run_check)
        # We allow quality-docs-lint to appear as a run_check argument but not as a standalone run_cmd
        run_cmd_docs_lint = re.search(r'run_cmd\s+make\s+-C\s+["\$\w/]+\s+quality-docs-lint', content)
        assert run_cmd_docs_lint is None, (
            "hooks_fast.sh must NOT have a standalone run_cmd for quality-docs-lint "
            "(it is now handled by pre-commit). "
            f"Found: {run_cmd_docs_lint.group() if run_cmd_docs_lint else None!r}"
        )

    def test_quality_docs_lint_not_standalone_runnable(self) -> None:
        content = _read()
        # Ensure quality-docs-lint does NOT appear as a direct make invocation outside of run_check
        lines_with_docs_lint = [
            line.strip()
            for line in content.splitlines()
            if "quality-docs-lint" in line and not line.strip().startswith("#")
        ]
        for line in lines_with_docs_lint:
            # Line should not be a run_cmd call
            assert not re.match(r'run_cmd\s+make.*quality-docs-lint', line), (
                f"quality-docs-lint must not be invoked via run_cmd: {line!r}"
            )


class TestQualityTestPyramidDedup:
    """No separate run_cmd line for quality-test-pyramid (AC-014)."""

    def test_no_run_cmd_quality_test_pyramid(self) -> None:
        content = _read()
        run_cmd_test_pyramid = re.search(r'run_cmd\s+make\s+-C\s+["\$\w/]+\s+quality-test-pyramid', content)
        assert run_cmd_test_pyramid is None, (
            "hooks_fast.sh must NOT have a standalone run_cmd for quality-test-pyramid "
            "(it is now handled by pre-commit). "
            f"Found: {run_cmd_test_pyramid.group() if run_cmd_test_pyramid else None!r}"
        )


class TestPreCommitMissingWarn:
    """When pre-commit is missing, a log_warn directs user to install it (FR-013)."""

    def test_log_warn_when_precommit_missing(self) -> None:
        content = _read()
        # The pre-commit not-installed branch must emit log_warn
        assert "log_warn" in content, "Script must emit log_warn when pre-commit is not installed"

    def test_warn_mentions_precommit_install(self) -> None:
        content = _read()
        # The warning should mention installing pre-commit
        assert "pre-commit" in content
        # Check for the install URL or directive
        assert "install pre-commit" in content or "https://pre-commit.com" in content, (
            "log_warn when pre-commit missing must direct user to install pre-commit"
        )

    def test_warn_mentions_what_is_skipped(self) -> None:
        content = _read()
        # The warn message should mention what hooks are skipped
        assert "quality-docs-lint" in content or "quality-test-pyramid" in content, (
            "log_warn must mention what is skipped when pre-commit is not installed"
        )
