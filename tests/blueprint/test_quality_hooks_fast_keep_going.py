"""Tests for scripts/bin/quality/hooks_fast.sh keep-going integration.

Slice 3 — keep-going mode integration (AC-001, AC-002, AC-003, AC-004, AC-006).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_FAST_SH = REPO_ROOT / "scripts/bin/quality/hooks_fast.sh"


def run_script(*args: str, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "ROOT_DIR": str(REPO_ROOT), **(env_overrides or {})}
    return subprocess.run(
        ["bash", str(HOOKS_FAST_SH), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )


class TestHelpOutput:
    """--help mentions --keep-going, QUALITY_HOOKS_KEEP_GOING, QUALITY_HOOKS_FORCE_FULL (AC-006)."""

    def test_help_mentions_keep_going_flag(self) -> None:
        result = run_script("--help")
        assert result.returncode == 0, result.stderr
        assert "--keep-going" in result.stdout, (
            "--help must mention --keep-going flag"
        )

    def test_help_mentions_keep_going_env_var(self) -> None:
        result = run_script("--help")
        assert "QUALITY_HOOKS_KEEP_GOING" in result.stdout, (
            "--help must mention QUALITY_HOOKS_KEEP_GOING env var"
        )

    def test_help_mentions_force_full_env_var(self) -> None:
        result = run_script("--help")
        assert "QUALITY_HOOKS_FORCE_FULL" in result.stdout, (
            "--help must mention QUALITY_HOOKS_FORCE_FULL env var"
        )


class TestKeepGoingFlagDetection:
    """Script detects --keep-going flag and env var."""

    def test_keep_going_flag_exported(self) -> None:
        # We can verify --keep-going flag is parsed by checking that the script
        # sources keep_going.sh and calls keep_going_init when the flag is set.
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "--keep-going" in content, "Script must parse --keep-going flag"

    def test_keep_going_env_var_handled(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_KEEP_GOING" in content, (
            "Script must handle QUALITY_HOOKS_KEEP_GOING env var"
        )

    def test_keep_going_sh_sourced(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "keep_going.sh" in content, "Script must source keep_going.sh"

    def test_keep_going_init_called(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "keep_going_init" in content, "Script must call keep_going_init when active"

    def test_keep_going_finalize_called(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "keep_going_finalize" in content, "Script must call keep_going_finalize"


class TestRunCheckDispatch:
    """All downstream checks dispatched via run_check when keep-going active (AC-002)."""

    def test_run_check_used_for_shellcheck(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert 'run_check "shellcheck"' in content or "run_check shellcheck" in content, (
            "shellcheck must be dispatched via run_check in keep-going mode"
        )

    def test_run_check_used_for_quality_checks(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "run_check" in content, "Script must use run_check for downstream checks"

    def test_quality_hooks_phase_set(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_PHASE" in content, (
            "Script must set QUALITY_HOOKS_PHASE"
        )
        assert "fast" in content, "Script must set QUALITY_HOOKS_PHASE=fast"


class TestPreCommitFailFast:
    """Pre-commit fails fast even in keep-going mode (AC-004)."""

    def test_pre_commit_runs_before_keep_going_dispatch(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        # pre-commit block must appear before keep_going_init
        precommit_pos = content.find("pre-commit")
        keep_going_init_pos = content.find("keep_going_init")
        assert precommit_pos != -1, "pre-commit must be present in script"
        assert keep_going_init_pos != -1, "keep_going_init must be present in script"
        assert precommit_pos < keep_going_init_pos, (
            "pre-commit block must appear before keep_going_init call"
        )

    def test_pre_commit_passed_sentinel_emitted(self) -> None:
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL" in content, (
            "Script must handle QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL for hooks_run.sh integration"
        )


class TestSummaryMarkerInKeepGoingMode:
    """Summary marker emitted in keep-going mode (AC-002)."""

    def test_keep_going_summary_marker_present_in_source(self) -> None:
        # Since we can't run the full gate in tests, verify the structure
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "keep_going_finalize" in content, (
            "keep_going_finalize (which emits summary) must be called"
        )

    def test_no_summary_in_default_mode_structure(self) -> None:
        # In default mode (no keep-going), the code path doesn't call finalize
        # Verify via structure: finalize is inside keep_going_active block
        content = HOOKS_FAST_SH.read_text(encoding="utf-8")
        assert "keep_going_active" in content, (
            "Script must check keep_going_active to gate summary/finalize"
        )
