"""Tests for scripts/bin/quality/hooks_strict.sh keep-going integration.

Slice 4 — keep-going mode integration for strict phase (AC-002, AC-006).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_STRICT_SH = REPO_ROOT / "scripts/bin/quality/hooks_strict.sh"


def run_script(*args: str, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "ROOT_DIR": str(REPO_ROOT), **(env_overrides or {})}
    return subprocess.run(
        ["bash", str(HOOKS_STRICT_SH), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )


class TestHelpOutput:
    """--help mentions --keep-going, QUALITY_HOOKS_KEEP_GOING (AC-006)."""

    def test_help_mentions_keep_going_flag(self) -> None:
        result = run_script("--help")
        assert result.returncode == 0, result.stderr
        assert "--keep-going" in result.stdout, "--help must mention --keep-going flag"

    def test_help_mentions_keep_going_env_var(self) -> None:
        result = run_script("--help")
        assert "QUALITY_HOOKS_KEEP_GOING" in result.stdout, (
            "--help must mention QUALITY_HOOKS_KEEP_GOING env var"
        )


class TestKeepGoingFlagDetection:
    """Script detects --keep-going flag and sources keep_going.sh."""

    def test_keep_going_flag_parsed(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "--keep-going" in content, "Script must parse --keep-going flag"

    def test_keep_going_sh_sourced(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "keep_going.sh" in content, "Script must source keep_going.sh"

    def test_keep_going_init_called(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "keep_going_init" in content, "Script must call keep_going_init when active"

    def test_keep_going_finalize_called(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "keep_going_finalize" in content, "Script must call keep_going_finalize"

    def test_quality_hooks_phase_set_strict(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_PHASE" in content, "Script must set QUALITY_HOOKS_PHASE"
        assert "strict" in content, "Script must set QUALITY_HOOKS_PHASE=strict"


class TestRunCheckDispatch:
    """All strict checks dispatched via run_check when keep-going active (AC-002)."""

    def test_run_check_used_for_infra_audit_version(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "run_check" in content, "Script must use run_check for strict-phase checks"

    def test_infra_audit_version_present(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "infra-audit-version" in content, "infra-audit-version must be in strict gate"

    def test_apps_audit_versions_present(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "apps-audit-versions" in content, "apps-audit-versions must be in strict gate"

    def test_keep_going_active_check_present(self) -> None:
        content = HOOKS_STRICT_SH.read_text(encoding="utf-8")
        assert "keep_going_active" in content, "Script must check keep_going_active"
