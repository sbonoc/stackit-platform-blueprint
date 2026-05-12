"""Regression tests for issues #264 and #266 — pipeline/engine correctness.

Tests cover:
- Engine exits 0 (not 1) when 3-way merge produces file conflicts (AC-004)
- Apply artifact status is 'conflicts' (not 'failure') for file conflicts (AC-004)
- Engine retains exit 1 for unresolved merge-marker failures (AC-005)
- Pipeline defaults BLUEPRINT_UPGRADE_APPLY to true (AC-006)
- Pipeline emits plan-only banner when BLUEPRINT_UPGRADE_APPLY is false (AC-006)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_ENGINE_PATH = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer.py"
_PIPELINE_PATH = REPO_ROOT / "scripts/bin/blueprint/upgrade_consumer_pipeline.sh"


class EngineExitCodeIssue264Tests(unittest.TestCase):
    """Tests for issue #264 — engine exit code for file conflicts vs. merge markers."""

    def test_engine_exits_zero_on_conflicts(self) -> None:
        """Engine must exit 0 when 3-way merge produces file conflicts (AC-004).

        Currently the engine returns 1 for conflict_count > 0, which make wraps
        as exit 2. The pipeline's 'if [[ "$stage2_rc" -gt 1 ]]' then treats every
        conflict as a fatal error and aborts Stages 3–10.

        After the fix: the 'if args.apply and conflict_count > 0: return 1' guard
        must be removed; the engine must return 0 and write status='conflicts'.
        """
        engine_source = _ENGINE_PATH.read_text(encoding="utf-8")
        conflict_return_1 = re.search(
            r"if args\.apply and conflict_count > 0:.*?return 1",
            engine_source,
            re.DOTALL,
        )
        self.assertIsNone(
            conflict_return_1,
            (
                "Engine must exit 0 for file conflicts (AC-004). "
                "The 'if args.apply and conflict_count > 0: ... return 1' guard "
                "must be replaced with status='conflicts' in the artifact and return 0."
            ),
        )

    def test_apply_artifact_status_is_conflicts_when_conflicts_present(self) -> None:
        """Apply artifact status must be 'conflicts' (not 'failure') for file conflicts (AC-004).

        Currently apply_payload["status"] is set to "failure" for conflict_count > 0.
        After the fix: status must be "conflicts" so the pipeline can distinguish
        between a true error ("failure") and a deferrable conflict ("conflicts").
        """
        engine_source = _ENGINE_PATH.read_text(encoding="utf-8")
        self.assertRegex(
            engine_source,
            r'apply_payload\["status"\]\s*=.*"conflicts"',
            msg=(
                "Engine must assign apply_payload['status'] = 'conflicts' when file conflicts "
                "are present (AC-004). Currently status is set to 'failure'."
            ),
        )

    def test_engine_exits_nonzero_on_merge_markers(self) -> None:
        """Engine must retain exit 1 for unresolved merge-marker failures (AC-005).

        File-conflict resolution may leave merge markers in the working tree.
        When markers are detected after apply, this is a hard abort — the engine
        must still exit nonzero.  This test guards the abort path against
        accidental removal during the conflict-exit-code refactor.
        """
        engine_source = _ENGINE_PATH.read_text(encoding="utf-8")
        merge_marker_return = re.search(
            r"merge conflict markers detected.*?return 1",
            engine_source,
            re.DOTALL,
        )
        self.assertIsNotNone(
            merge_marker_return,
            (
                "Engine must retain 'return 1' for merge-marker failures (AC-005). "
                "The merge-markers abort path must not be removed or its exit code changed."
            ),
        )


class PipelineApplyDefaultIssue266Tests(unittest.TestCase):
    """Tests for issue #266 — pipeline BLUEPRINT_UPGRADE_APPLY default and banner."""

    def test_pipeline_apply_default_is_true(self) -> None:
        """Pipeline must default BLUEPRINT_UPGRADE_APPLY to true (AC-006).

        Currently the pipeline script has no 'set_default_env BLUEPRINT_UPGRADE_APPLY true'
        call, so every invocation silently runs in plan-only mode regardless of intent.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "set_default_env BLUEPRINT_UPGRADE_APPLY true",
            pipeline_source,
            msg=(
                "Pipeline must set BLUEPRINT_UPGRADE_APPLY=true as the default (AC-006). "
                "Add 'set_default_env BLUEPRINT_UPGRADE_APPLY true' to "
                "scripts/bin/blueprint/upgrade_consumer_pipeline.sh."
            ),
        )

    def test_pipeline_emits_banner_when_apply_false(self) -> None:
        """Pipeline must emit a plan-only banner when BLUEPRINT_UPGRADE_APPLY is false (AC-006).

        Without a visible banner, operators cannot tell that a pipeline run was
        plan-only (no files changed) and may incorrectly assume the upgrade applied.
        The banner must be present so plan-only runs are never silently ambiguous.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "PLAN-ONLY mode",
            pipeline_source,
            msg=(
                "Pipeline must emit a 'PLAN-ONLY mode' banner when "
                "BLUEPRINT_UPGRADE_APPLY is not true (AC-006). "
                "Add a visible log statement to "
                "scripts/bin/blueprint/upgrade_consumer_pipeline.sh."
            ),
        )
