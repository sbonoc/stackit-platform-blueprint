"""Tests for scripts/lib/shell/keep_going.sh

Slice 1 — keep-going aggregation helper unit contract (AC-007).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KEEP_GOING_SH = REPO_ROOT / "scripts/lib/shell/keep_going.sh"

PREAMBLE = f"""
set -euo pipefail
ROOT_DIR="{REPO_ROOT}"
SCRIPT_DIR="{REPO_ROOT}/scripts/bin/quality"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{KEEP_GOING_SH}"
"""


def bash(script: str, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "ROOT_DIR": str(REPO_ROOT), **(env_overrides or {})}
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )


class TestKeepGoingActive:
    """keep_going_active returns 0 when QUALITY_HOOKS_KEEP_GOING=true, non-zero otherwise."""

    def test_active_when_env_true(self) -> None:
        result = bash(
            PREAMBLE + "keep_going_active",
            {"QUALITY_HOOKS_KEEP_GOING": "true"},
        )
        assert result.returncode == 0, result.stderr

    def test_inactive_when_env_unset(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "QUALITY_HOOKS_KEEP_GOING"}
        env["ROOT_DIR"] = str(REPO_ROOT)
        result = subprocess.run(
            ["bash", "-c", PREAMBLE + "keep_going_active"],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0

    def test_inactive_when_env_false(self) -> None:
        result = bash(
            PREAMBLE + "keep_going_active",
            {"QUALITY_HOOKS_KEEP_GOING": "false"},
        )
        assert result.returncode != 0

    def test_inactive_when_env_empty(self) -> None:
        result = bash(
            PREAMBLE + "keep_going_active",
            {"QUALITY_HOOKS_KEEP_GOING": ""},
        )
        assert result.returncode != 0


class TestRunCheck:
    """run_check records pass/fail/duration; multiple checks aggregate correctly."""

    def test_passing_check_recorded(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "my-check" -- true
echo "failed_count=${_KG_FAILED_COUNT}"
echo "names_count=${#_KG_NAMES[@]}"
echo "status=${_KG_STATUSES[0]}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        assert "failed_count=0" in result.stdout
        assert "names_count=1" in result.stdout
        assert "status=0" in result.stdout

    def test_failing_check_recorded(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "bad-check" -- false
echo "failed_count=${_KG_FAILED_COUNT}"
echo "status=${_KG_STATUSES[0]}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        assert "failed_count=1" in result.stdout
        assert "status=1" in result.stdout

    def test_multiple_checks_aggregate(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "check-pass" -- true
run_check "check-fail-1" -- false
run_check "check-fail-2" -- false
echo "failed_count=${_KG_FAILED_COUNT}"
echo "names_count=${#_KG_NAMES[@]}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        assert "failed_count=2" in result.stdout
        assert "names_count=3" in result.stdout

    def test_duration_recorded(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "timed-check" -- true
echo "duration=${_KG_DURATIONS[0]}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        assert "duration=" in result.stdout


class TestFailedCheckTailReemitted:
    """Failed check tail re-emitted to stderr immediately."""

    def test_failed_check_emits_output_to_stderr(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "failing-echo" -- bash -c 'echo "unique-failure-output"; exit 1'
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert "unique-failure-output" in result.stderr, (
            f"Expected captured output in stderr. stderr={result.stderr!r}"
        )

    def test_passing_check_output_not_in_stderr(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "passing-echo" -- bash -c 'echo "only-on-pass"; exit 0'
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert "only-on-pass" not in result.stderr


class TestTailLinesEnvVar:
    """QUALITY_HOOKS_KEEP_GOING_TAIL_LINES controls tail length."""

    def test_tail_lines_limits_output(self) -> None:
        # Generate 100-line output from failing check; with TAIL_LINES=5 only last 5 should appear
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "many-lines" -- bash -c 'for i in $(seq 1 100); do echo "line-$i"; done; exit 1'
"""
        )
        result = bash(
            script,
            {
                "QUALITY_HOOKS_KEEP_GOING": "true",
                "QUALITY_HOOKS_KEEP_GOING_TAIL_LINES": "5",
            },
        )
        # Should have last 5 lines but not earlier lines
        assert "line-100" in result.stderr
        assert "line-96" in result.stderr
        # line-95 is outside the last 5, so it must not appear
        assert "line-95" not in result.stderr

    def test_default_tail_lines_is_40(self) -> None:
        # With default (40), lines 61-100 visible, line 60 not
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "many-lines" -- bash -c 'for i in $(seq 1 100); do echo "line-$i"; done; exit 1'
"""
        )
        env = {k: v for k, v in os.environ.items() if k != "QUALITY_HOOKS_KEEP_GOING_TAIL_LINES"}
        env.update({"ROOT_DIR": str(REPO_ROOT), "QUALITY_HOOKS_KEEP_GOING": "true"})
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        assert "line-100" in result.stderr
        assert "line-61" in result.stderr
        assert "line-60" not in result.stderr


class TestKeepGoingFinalize:
    """keep_going_finalize emits marker line, per-check status, correct trailer, exits 0/1."""

    def test_finalize_all_pass_exits_zero(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "ok-check" -- true
keep_going_finalize
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        assert "===== quality-hooks keep-going summary =====" in result.stdout
        assert "all checks passed" in result.stdout
        assert "PASS" in result.stdout

    def test_finalize_with_failure_exits_one(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "ok-check" -- true
run_check "bad-check" -- false
keep_going_finalize
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
        assert "===== quality-hooks keep-going summary =====" in result.stdout
        assert "1 check(s) failed" in result.stdout
        assert "FAIL" in result.stdout
        assert "PASS" in result.stdout

    def test_finalize_emits_marker_header(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "check-a" -- true
keep_going_finalize
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert "===== quality-hooks keep-going summary =====" in result.stdout

    def test_finalize_emits_metric_on_success(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "pass-check" -- true
keep_going_finalize
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true", "QUALITY_HOOKS_PHASE": "fast"})
        combined = result.stdout + result.stderr
        assert "quality_hooks_keep_going_total" in combined
        assert "status=success" in combined

    def test_finalize_emits_metric_on_failure(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
run_check "fail-check" -- false
keep_going_finalize || true
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true", "QUALITY_HOOKS_PHASE": "fast"})
        combined = result.stdout + result.stderr
        assert "quality_hooks_keep_going_total" in combined
        assert "status=failure" in combined


class TestTmpdirCleanup:
    """tmpdir cleaned up after script exits."""

    def test_tmpdir_cleaned_up_after_exit(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
_my_tmpdir="$_KG_TMPDIR"
run_check "check" -- true
keep_going_finalize
echo "tmpdir_was=${_my_tmpdir}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        assert result.returncode == 0, result.stderr
        # Extract tmpdir path from output
        for line in result.stdout.splitlines():
            if line.startswith("tmpdir_was="):
                tmpdir = line.split("=", 1)[1]
                assert not Path(tmpdir).exists(), f"tmpdir {tmpdir} was not cleaned up"
                break
        else:
            assert False, f"Expected tmpdir_was= in output. stdout={result.stdout!r}"

    def test_tmpdir_cleaned_up_even_on_failure(self) -> None:
        script = (
            PREAMBLE
            + """
keep_going_init
_my_tmpdir="$_KG_TMPDIR"
run_check "bad-check" -- false
keep_going_finalize || true
echo "tmpdir_was=${_my_tmpdir}"
"""
        )
        result = bash(script, {"QUALITY_HOOKS_KEEP_GOING": "true"})
        for line in result.stdout.splitlines():
            if line.startswith("tmpdir_was="):
                tmpdir = line.split("=", 1)[1]
                assert not Path(tmpdir).exists(), f"tmpdir {tmpdir} was not cleaned up after failure"
                break
        else:
            assert False, f"Expected tmpdir_was= in output. stdout={result.stdout!r}"
