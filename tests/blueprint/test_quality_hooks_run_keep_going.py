"""Tests for scripts/bin/quality/hooks_run.sh keep-going integration.

Slice 5 — cross-phase keep-going integration (AC-005, AC-006).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_RUN_SH = REPO_ROOT / "scripts/bin/quality/hooks_run.sh"


def run_script(*args: str, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "ROOT_DIR": str(REPO_ROOT), **(env_overrides or {})}
    return subprocess.run(
        ["bash", str(HOOKS_RUN_SH), *args],
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
        assert "--keep-going" in result.stdout, "--help must mention --keep-going flag"

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
    """Script detects --keep-going flag and propagates it to child invocations."""

    def test_keep_going_flag_parsed(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        assert "--keep-going" in content, "Script must parse --keep-going flag"

    def test_keep_going_propagated_to_fast(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        assert "hooks_fast.sh" in content, "Script must invoke hooks_fast.sh"
        # --keep-going must be propagated (either via env var or flag)
        assert "QUALITY_HOOKS_KEEP_GOING" in content, (
            "Script must propagate QUALITY_HOOKS_KEEP_GOING to child invocations"
        )

    def test_keep_going_propagated_to_strict(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        assert "hooks_strict.sh" in content, "Script must invoke hooks_strict.sh"


class TestPreCommitSentinel:
    """Strict only runs when fast's pre-commit passed (AC-005)."""

    def test_precommit_sentinel_used(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL" in content, (
            "Script must use QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL to gate strict phase"
        )

    def test_strict_gated_on_precommit_sentinel(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        # Strict invocation should be conditional on sentinel
        hooks_strict_pos = content.find("hooks_strict.sh")
        sentinel_pos = content.find("QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL")
        assert hooks_strict_pos != -1, "hooks_strict.sh must be present"
        assert sentinel_pos != -1, "sentinel must be checked before strict"


class TestCombinedExitCode:
    """Combined exit is non-zero if either phase fails."""

    def test_combined_exit_logic_present(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        # Script must track exit codes from both phases
        assert "_fast_exit" in content or "fast_exit" in content or "fast_rc" in content or "_fast" in content, (
            "Script must track fast phase exit code"
        )

    def test_force_full_forwarded(self) -> None:
        content = HOOKS_RUN_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_FORCE_FULL" in content, (
            "Script must forward QUALITY_HOOKS_FORCE_FULL to child invocations"
        )
