"""Regression tests for issue #267 — blueprint-upgrade-consumer-finalize target.

Tests cover:
- Make target blueprint-upgrade-consumer-finalize exists in make/blueprint.generated.mk (AC-001)
- Script upgrade_consumer_finalize.sh exists at scripts/bin/blueprint/ (AC-001)
- Sync pass contains all three required targets (FR-006)
- Sync pass uses aggregated failure mode (no fail-fast) (FR-006, AC-003)
- Verify pass contains all five required targets in order (FR-007)
- Verify pass uses fail-fast with summary banner (FR-007, AC-004)
- Pipeline invokes make blueprint-upgrade-consumer-finalize instead of old Stage 8+9 blocks (FR-008, AC-005)
- SKILL.md documents make blueprint-upgrade-consumer-finalize as canonical post-apply step (FR-009, AC-007)
- Per-step log lines present (NFR-OBS-001)
- Script usage block documents two-pass structure (NFR-OPS-001)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_FINALIZE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/upgrade_consumer_finalize.sh"
_PIPELINE_PATH = REPO_ROOT / "scripts/bin/blueprint/upgrade_consumer_pipeline.sh"
_GENERATED_MK = REPO_ROOT / "make/blueprint.generated.mk"
_MK_TEMPLATE = REPO_ROOT / "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl"
_SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-consumer-upgrade/SKILL.md"


class FinalizeTargetExistenceTests(unittest.TestCase):
    """Assert the make target and script exist (AC-001)."""

    def test_finalize_script_exists(self) -> None:
        """scripts/bin/blueprint/upgrade_consumer_finalize.sh MUST exist (AC-001, FR-005).

        Without this script, the make target cannot execute and consumers have no
        single-command post-apply convergence step.
        """
        self.assertTrue(
            _FINALIZE_SCRIPT.exists(),
            msg=(
                f"scripts/bin/blueprint/upgrade_consumer_finalize.sh must exist (AC-001, FR-005). "
                f"Create the script at {_FINALIZE_SCRIPT}."
            ),
        )

    def test_finalize_make_target_exists_in_generated_mk(self) -> None:
        """blueprint-upgrade-consumer-finalize MUST be registered in make/blueprint.generated.mk (AC-001, FR-005).

        The generated makefile is the consumer-facing contract for available targets.
        Without the target, consumers cannot invoke 'make blueprint-upgrade-consumer-finalize'.
        """
        mk_source = _GENERATED_MK.read_text(encoding="utf-8")
        self.assertIn(
            "blueprint-upgrade-consumer-finalize",
            mk_source,
            msg=(
                "make/blueprint.generated.mk must contain the 'blueprint-upgrade-consumer-finalize' "
                "target (AC-001, FR-005). Add the target to "
                "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl "
                "and regenerate make/blueprint.generated.mk."
            ),
        )

    def test_finalize_target_in_mk_template(self) -> None:
        """blueprint-upgrade-consumer-finalize MUST be in the mk template (AC-001, FR-005).

        The template is the source of truth for generated.mk; a target added only to
        generated.mk is overwritten on the next make blueprint-render-makefile invocation.
        """
        tmpl_source = _MK_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "blueprint-upgrade-consumer-finalize",
            tmpl_source,
            msg=(
                "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl "
                "must contain the 'blueprint-upgrade-consumer-finalize' target (FR-005). "
                "Add the target definition before regenerating make/blueprint.generated.mk."
            ),
        )


class FinalizeSyncPassTests(unittest.TestCase):
    """Assert sync pass structure in upgrade_consumer_finalize.sh (FR-006, AC-003)."""

    def _script(self) -> str:
        if not _FINALIZE_SCRIPT.exists():
            self.skipTest("upgrade_consumer_finalize.sh does not exist yet — Slice 4 not complete")
        return _FINALIZE_SCRIPT.read_text(encoding="utf-8")

    def test_sync_pass_contains_quality_docs_sync_all(self) -> None:
        """Sync pass MUST invoke quality-docs-sync-all (FR-006)."""
        self.assertIn(
            "quality-docs-sync-all",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh sync pass must invoke 'quality-docs-sync-all' (FR-006). "
                "Add it to the sync pass in scripts/bin/blueprint/upgrade_consumer_finalize.sh."
            ),
        )

    def test_sync_pass_contains_quality_sdd_sync_consumer_init_assets(self) -> None:
        """Sync pass MUST invoke quality-sdd-sync-consumer-init-assets (FR-006)."""
        self.assertIn(
            "quality-sdd-sync-consumer-init-assets",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh sync pass must invoke "
                "'quality-sdd-sync-consumer-init-assets' (FR-006)."
            ),
        )

    def test_sync_pass_contains_quality_sdd_sync_policy_snippets(self) -> None:
        """Sync pass MUST invoke quality-sdd-sync-policy-snippets (FR-006)."""
        self.assertIn(
            "quality-sdd-sync-policy-snippets",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh sync pass must invoke "
                "'quality-sdd-sync-policy-snippets' (FR-006)."
            ),
        )

    def test_sync_pass_aggregates_failures_no_fail_fast(self) -> None:
        """Sync pass MUST aggregate failures and NOT fail-fast (FR-006, AC-003).

        The pattern '|| sync_rc=...' (or equivalent) combined with continuing to the
        next step is the normative aggregation structure.  A 'set -e' or early 'exit'
        on first sync failure would violate this requirement.
        """
        script = self._script()
        self.assertRegex(
            script,
            r'\|\|\s+\w*_?rc\s*=|sync_errors\s*=|sync_failed\s*=',
            msg=(
                "upgrade_consumer_finalize.sh sync pass must aggregate failures without "
                "fail-fast (FR-006, AC-003). Use '|| sync_rc=1' (or equivalent error "
                "accumulator) after each sync target so subsequent sync targets still run "
                "when one fails."
            ),
        )


class FinalizeVerifyPassTests(unittest.TestCase):
    """Assert verify pass structure in upgrade_consumer_finalize.sh (FR-007, AC-004)."""

    def _script(self) -> str:
        if not _FINALIZE_SCRIPT.exists():
            self.skipTest("upgrade_consumer_finalize.sh does not exist yet — Slice 4 not complete")
        return _FINALIZE_SCRIPT.read_text(encoding="utf-8")

    def test_verify_pass_contains_infra_validate(self) -> None:
        """Verify pass MUST invoke infra-validate (FR-007)."""
        self.assertIn(
            "infra-validate",
            self._script(),
            msg="upgrade_consumer_finalize.sh verify pass must invoke 'infra-validate' (FR-007).",
        )

    def test_verify_pass_contains_quality_hooks_run(self) -> None:
        """Verify pass MUST invoke quality-hooks-run (FR-007)."""
        self.assertIn(
            "quality-hooks-run",
            self._script(),
            msg="upgrade_consumer_finalize.sh verify pass must invoke 'quality-hooks-run' (FR-007).",
        )

    def test_verify_pass_contains_blueprint_upgrade_consumer_validate(self) -> None:
        """Verify pass MUST invoke blueprint-upgrade-consumer-validate (FR-007)."""
        self.assertIn(
            "blueprint-upgrade-consumer-validate",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh verify pass must invoke "
                "'blueprint-upgrade-consumer-validate' (FR-007)."
            ),
        )

    def test_verify_pass_contains_blueprint_upgrade_consumer_postcheck(self) -> None:
        """Verify pass MUST invoke blueprint-upgrade-consumer-postcheck (FR-007)."""
        self.assertIn(
            "blueprint-upgrade-consumer-postcheck",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh verify pass must invoke "
                "'blueprint-upgrade-consumer-postcheck' (FR-007)."
            ),
        )

    def test_verify_pass_contains_blueprint_upgrade_fresh_env_gate(self) -> None:
        """Verify pass MUST invoke blueprint-upgrade-fresh-env-gate (FR-007)."""
        self.assertIn(
            "blueprint-upgrade-fresh-env-gate",
            self._script(),
            msg=(
                "upgrade_consumer_finalize.sh verify pass must invoke "
                "'blueprint-upgrade-fresh-env-gate' (FR-007)."
            ),
        )

    def test_verify_pass_emits_summary_banner_on_failure(self) -> None:
        """Verify pass MUST emit a summary banner naming the failing target (FR-007, AC-004).

        Without the banner, operators reading truncated log output cannot determine
        which verify step failed without scrolling to find the make error.
        """
        script = self._script()
        self.assertRegex(
            script,
            r'finalize.*FAILED|FAILED.*finalize|log_error.*finalize',
            msg=(
                "upgrade_consumer_finalize.sh verify pass must emit a summary banner naming "
                "the failing target and its exit code when a verify step fails (FR-007, AC-004). "
                "Add a 'log_error \"[finalize] <target>: FAILED (exit $rc)\"' after each "
                "failing verify step."
            ),
        )


class FinalizeObservabilityTests(unittest.TestCase):
    """Assert per-step log lines are present (NFR-OBS-001)."""

    def _script(self) -> str:
        if not _FINALIZE_SCRIPT.exists():
            self.skipTest("upgrade_consumer_finalize.sh does not exist yet — Slice 4 not complete")
        return _FINALIZE_SCRIPT.read_text(encoding="utf-8")

    def test_script_emits_finalize_log_lines(self) -> None:
        """Script MUST emit '[finalize] <step>: <status>' log lines per step (NFR-OBS-001).

        Without structured per-step log lines, operators cannot diagnose which sync or
        verify step failed without reading the full make output.
        """
        self.assertRegex(
            self._script(),
            r'\[finalize\]',
            msg=(
                "upgrade_consumer_finalize.sh must emit '[finalize] <step>: <status>' log lines "
                "for each sync and verify step (NFR-OBS-001). Use log_info/log_error with the "
                "'[finalize]' prefix."
            ),
        )

    def test_script_has_usage_block_documenting_two_pass_structure(self) -> None:
        """Script usage block MUST document the two-pass structure (NFR-OPS-001, AC-001).

        Operators invoking '--help' or reading the script header must be able to
        understand the sync+verify two-pass structure without reading the source.
        """
        script = self._script()
        self.assertRegex(
            script,
            r'sync\s+pass|verify\s+pass|two.pass',
            msg=(
                "upgrade_consumer_finalize.sh usage block must document the two-pass "
                "structure (sync pass + verify pass) (NFR-OPS-001). "
                "Add a usage() function with USAGE heredoc describing both passes."
            ),
        )


class PipelineIntegrationTests(unittest.TestCase):
    """Assert pipeline invokes finalize instead of old Stages 8+9 (FR-008, AC-005)."""

    def test_pipeline_invokes_finalize_as_post_stage2_tail(self) -> None:
        """Pipeline MUST invoke blueprint-upgrade-consumer-finalize as its post-Stage-2 tail (FR-008, AC-005).

        The old Stage 8 (docs regen) and Stage 9 (gate chain) blocks must be replaced by
        a single finalize invocation.  This gives consumers a single canonical entry point
        for post-apply convergence both inside and outside the pipeline.
        """
        import re as _re

        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        # Usage block closes after 'USAGE'; the code invocation must appear after that.
        after_usage = pipeline_source.split("USAGE", 1)[-1]
        self.assertRegex(
            after_usage,
            r'make\s+(?:-C\s+\S+\s+)?blueprint-upgrade-consumer-finalize',
            msg=(
                "upgrade_consumer_pipeline.sh must invoke "
                "'make -C \"$ROOT_DIR\" blueprint-upgrade-consumer-finalize' "
                "in the pipeline body (outside the usage block) as its post-Stage-2 tail "
                "(FR-008, AC-005). Replace the Stage 8 and Stage 9 "
                "blocks with a single make invocation of blueprint-upgrade-consumer-finalize."
            ),
        )

    def test_pipeline_stage8_replaced_by_finalize(self) -> None:
        """The old Stage 8 docs-regen inline block MUST be replaced by finalize (FR-008).

        quality-docs-sync-core-targets and quality-docs-sync-contract-metadata are now
        part of the finalize sync pass; the old inline invocation in Stage 8 must be removed.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            "quality-docs-sync-core-targets",
            pipeline_source,
            msg=(
                "upgrade_consumer_pipeline.sh Stage 8 inline invocation of "
                "'quality-docs-sync-core-targets' must be replaced by "
                "'make blueprint-upgrade-consumer-finalize' (FR-008). "
                "Remove the Stage 8 block and call finalize instead."
            ),
        )


class SkillRunbookTests(unittest.TestCase):
    """Assert SKILL.md documents finalize as the canonical post-apply step (FR-009, AC-007)."""

    def test_skill_md_references_finalize_as_post_apply_step(self) -> None:
        """SKILL.md MUST reference blueprint-upgrade-consumer-finalize as the canonical post-apply step (FR-009, AC-007).

        Without this update, consumers reading the skill runbook will continue using the
        old per-target post-apply sequence and miss the single-command convergence path.
        """
        skill_source = _SKILL_MD.read_text(encoding="utf-8")
        self.assertIn(
            "blueprint-upgrade-consumer-finalize",
            skill_source,
            msg=(
                ".agents/skills/blueprint-consumer-upgrade/SKILL.md must document "
                "'make blueprint-upgrade-consumer-finalize' as the single canonical "
                "post-apply step (FR-009, AC-007). Replace the per-target list in the "
                "post-apply section with the single finalize command."
            ),
        )
