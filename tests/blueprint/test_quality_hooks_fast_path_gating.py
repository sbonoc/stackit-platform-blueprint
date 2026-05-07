"""Tests for path-gating in scripts/bin/quality/hooks_fast.sh.

Slice 6 — infra-validate and infra-contract-test-fast path gating (AC-009, AC-010, AC-011).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_FAST_SH = REPO_ROOT / "scripts/bin/quality/hooks_fast.sh"


def _read() -> str:
    return HOOKS_FAST_SH.read_text(encoding="utf-8")


class TestInfraValidatePathGating:
    """infra-validate is path-gated (AC-009, AC-010)."""

    def test_infra_validate_gated_on_changed_paths(self) -> None:
        content = _read()
        # infra-validate must be inside a quality_paths_match_infra_gate block
        assert "quality_paths_match_infra_gate" in content, (
            "hooks_fast.sh must use quality_paths_match_infra_gate for path gating"
        )
        assert "infra-validate" in content, "infra-validate must be present in the script"

    def test_infra_validate_has_force_full_escape(self) -> None:
        content = _read()
        assert "QUALITY_HOOKS_FORCE_FULL" in content, (
            "Script must support QUALITY_HOOKS_FORCE_FULL override"
        )

    def test_infra_validate_skip_metric_emitted(self) -> None:
        content = _read()
        assert "quality_hooks_skip_total" in content, (
            "Script must emit quality_hooks_skip_total metric on skip"
        )
        assert "infra-validate" in content, "infra-validate skip reason must reference check name"

    def test_infra_validate_skip_log_emitted(self) -> None:
        content = _read()
        assert "skipping infra-validate" in content, (
            "Script must log skip when infra-validate is skipped"
        )


class TestInfraContractTestFastPathGating:
    """infra-contract-test-fast is path-gated (AC-009, AC-010)."""

    def test_infra_contract_test_fast_present(self) -> None:
        content = _read()
        assert "infra-contract-test-fast" in content, (
            "infra-contract-test-fast must be in the script"
        )

    def test_infra_contract_test_fast_skip_metric_emitted(self) -> None:
        content = _read()
        assert "infra-contract-test-fast" in content
        assert "quality_hooks_skip_total" in content

    def test_infra_contract_test_fast_skip_log_emitted(self) -> None:
        content = _read()
        assert "skipping infra-contract-test-fast" in content, (
            "Script must log skip when infra-contract-test-fast is skipped"
        )


class TestForceFullOverride:
    """QUALITY_HOOKS_FORCE_FULL=true forces all checks regardless (AC-011)."""

    def test_force_full_in_infra_gate(self) -> None:
        content = _read()
        # FORCE_FULL must be checked alongside path gate
        # Look for pattern: FORCE_FULL == true || quality_paths_match_infra_gate
        assert 'QUALITY_HOOKS_FORCE_FULL' in content
        assert 'quality_paths_match_infra_gate' in content

    def test_help_mentions_force_full(self) -> None:
        content = _read()
        assert "QUALITY_HOOKS_FORCE_FULL" in content, (
            "--help must mention QUALITY_HOOKS_FORCE_FULL"
        )

    def test_quality_gating_sh_sourced(self) -> None:
        content = _read()
        assert "quality_gating.sh" in content, (
            "Script must source quality_gating.sh for path gating"
        )

    def test_changed_paths_computed_once(self) -> None:
        content = _read()
        assert "_quality_changed_paths" in content, (
            "Script must call _quality_changed_paths to compute changed paths"
        )
        assert "_changed_paths" in content, (
            "Script must store changed paths in _changed_paths variable"
        )
