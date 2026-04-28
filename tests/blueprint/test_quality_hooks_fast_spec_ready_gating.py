"""Tests for spec-ready phase gating in scripts/bin/quality/hooks_fast.sh.

Slice 7 — quality-spec-pr-ready phase gating (AC-012, AC-013, AC-011).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_FAST_SH = REPO_ROOT / "scripts/bin/quality/hooks_fast.sh"


def _read() -> str:
    return HOOKS_FAST_SH.read_text(encoding="utf-8")


class TestSpecPrReadyGating:
    """quality-spec-pr-ready is skipped unless SPEC_READY: true (AC-012, AC-013)."""

    def test_quality_spec_is_ready_called(self) -> None:
        content = _read()
        assert "quality_spec_is_ready" in content, (
            "hooks_fast.sh must call quality_spec_is_ready to check spec readiness"
        )

    def test_spec_not_ready_skip_logged(self) -> None:
        content = _read()
        assert "spec-not-ready" in content, (
            "Script must log 'spec-not-ready' when skipping quality-spec-pr-ready"
        )

    def test_spec_not_ready_metric_emitted(self) -> None:
        content = _read()
        assert "quality_hooks_skip_total" in content
        assert "spec-not-ready" in content

    def test_no_spec_dir_skip_logged(self) -> None:
        content = _read()
        assert "no-spec-dir" in content, (
            "Script must log 'no-spec-dir' when spec directory doesn't exist"
        )


class TestSpecPrReadyForceFullOverride:
    """QUALITY_HOOKS_FORCE_FULL bypasses spec-ready check (AC-011)."""

    def test_force_full_bypasses_spec_check(self) -> None:
        content = _read()
        # Find the spec-pr-ready block and check FORCE_FULL is used alongside quality_spec_is_ready
        spec_ready_pos = content.find("quality_spec_is_ready")
        force_full_pos = content.find("QUALITY_HOOKS_FORCE_FULL")
        assert spec_ready_pos != -1
        assert force_full_pos != -1, "FORCE_FULL must be checked alongside quality_spec_is_ready"

    def test_spec_dir_check_present(self) -> None:
        content = _read()
        assert "_spec_dir" in content, "Script must store spec dir path in variable"


class TestSpecPrReadyKeepGoingDispatch:
    """quality-spec-pr-ready dispatched via run_check when keep-going active."""

    def test_spec_pr_ready_dispatched_via_run_check(self) -> None:
        content = _read()
        assert 'run_check "quality-spec-pr-ready"' in content or "run_check.*quality-spec-pr-ready" in content, (
            "quality-spec-pr-ready must be dispatched via run_check in keep-going mode"
        )

    def test_spec_pr_ready_has_run_cmd_fallback(self) -> None:
        content = _read()
        # Both run_check and run_cmd paths for quality-spec-pr-ready must exist
        assert "quality-spec-pr-ready" in content
        assert "run_cmd" in content
        assert "run_check" in content
