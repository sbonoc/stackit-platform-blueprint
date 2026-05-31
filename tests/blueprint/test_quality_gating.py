"""Tests for scripts/lib/shell/quality_gating.sh

Slice 2 — path-gate and phase-gate helpers unit contract.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATING_SH = REPO_ROOT / "scripts/lib/shell/quality_gating.sh"

PREAMBLE = f"""
set -euo pipefail
ROOT_DIR="{REPO_ROOT}"
SCRIPT_DIR="{REPO_ROOT}/scripts/bin/quality"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{QUALITY_GATING_SH}"
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


class TestQualityPathsMatchInfraGate:
    """quality_paths_match_infra_gate with paths under each gating prefix returns 0."""

    def _match(self, paths_str: str, env: dict | None = None) -> subprocess.CompletedProcess:
        script = PREAMBLE + f'quality_paths_match_infra_gate "{paths_str}"'
        return bash(script, env)

    def test_infra_prefix_matches(self) -> None:
        result = self._match("infra/local/helm/something.yaml")
        assert result.returncode == 0, f"infra/ prefix should match. stderr={result.stderr!r}"

    def test_blueprint_contract_matches(self) -> None:
        result = self._match("blueprint/contract.yaml")
        assert result.returncode == 0

    def test_scripts_lib_blueprint_matches(self) -> None:
        result = self._match("scripts/lib/blueprint/some_helper.py")
        assert result.returncode == 0

    def test_scripts_bin_blueprint_matches(self) -> None:
        result = self._match("scripts/bin/blueprint/validate.sh")
        assert result.returncode == 0

    def test_scripts_templates_blueprint_matches(self) -> None:
        result = self._match("scripts/templates/blueprint/bootstrap/make/Makefile")
        assert result.returncode == 0

    def test_make_prefix_matches(self) -> None:
        result = self._match("make/blueprint.generated.mk")
        assert result.returncode == 0

    def test_apps_prefix_matches(self) -> None:
        result = self._match("apps/backend-api/Dockerfile")
        assert result.returncode == 0

    def test_pyproject_toml_matches(self) -> None:
        result = self._match("pyproject.toml")
        assert result.returncode == 0

    def test_requirements_txt_matches(self) -> None:
        result = self._match("requirements.txt")
        assert result.returncode == 0

    def test_requirements_dev_txt_matches(self) -> None:
        result = self._match("requirements-dev.txt")
        assert result.returncode == 0

    def test_docs_only_does_not_match(self) -> None:
        result = self._match("docs/blueprint/operations/quality-gates.md")
        assert result.returncode != 0, "docs/ path should NOT match infra gate"

    def test_specs_only_does_not_match(self) -> None:
        result = self._match("specs/2026-04-28-my-spec/spec.md")
        assert result.returncode != 0, "specs/ path should NOT match infra gate"

    def test_readme_only_does_not_match(self) -> None:
        result = self._match("README.md")
        assert result.returncode != 0

    def test_multiple_paths_any_match_returns_zero(self) -> None:
        # Pass newline-separated list with one infra path and one docs path
        paths = "docs/something.md\ninfra/local/helm/core/values.yaml"
        result = self._match(paths)
        assert result.returncode == 0, "Any matching path should return 0"

    def test_multiple_paths_none_match_returns_one(self) -> None:
        paths = "docs/something.md\nspecs/my-spec/spec.md\nREADME.md"
        result = self._match(paths)
        assert result.returncode != 0


class TestQualityPathsMatchGitFailSafe:
    """FR-011: when git is unavailable or merge-base fails, return 0 (fail-safe: run infra checks)."""

    def test_git_merge_base_failure_forces_match(self) -> None:
        # Point QUALITY_HOOKS_MAIN_BRANCH at a branch that cannot be resolved so
        # git merge-base fails; quality_paths_match_infra_gate must return 0.
        script = PREAMBLE + "quality_paths_match_infra_gate"
        result = bash(script, {"QUALITY_HOOKS_MAIN_BRANCH": "nonexistent-branch-xyz-99999"})
        assert result.returncode == 0, (
            "git merge-base failure must return 0 (fail-safe: run infra checks). "
            f"stderr={result.stderr!r}"
        )


class TestQualityChangedPathsCallerFailSafe:
    """Caller idiom from hooks_fast.sh: _changed_paths="$(...)"; || _changed_paths="" must not exit under set -e.

    Regression test for the CI breakage where _quality_changed_paths returning 1 (on a shallow
    clone PR checkout where the main-branch ref is absent) caused hooks_fast.sh to exit under
    set -euo pipefail before reaching quality_paths_match_infra_gate.
    """

    def test_assignment_or_idiom_survives_git_failure(self) -> None:
        # Reproduce the hooks_fast.sh pattern under set -e.
        script = PREAMBLE + (
            '_changed_paths="$(_quality_changed_paths)" || _changed_paths=""\n'
            'printf "ok changed_paths='"'"'%s'"'"'\\n" "$_changed_paths"\n'
        )
        result = bash(script, {"QUALITY_HOOKS_MAIN_BRANCH": "nonexistent-branch-xyz-99999"})
        assert result.returncode == 0, (
            "set -e must not exit when _quality_changed_paths returns 1 and caller uses || idiom. "
            f"stderr={result.stderr!r}"
        )
        assert "ok" in result.stdout
        assert "changed_paths=''" in result.stdout

    def test_empty_paths_arg_triggers_fail_safe_in_gate(self) -> None:
        # After the || idiom produces _changed_paths="", the gate must still return 0 (FR-011).
        script = PREAMBLE + (
            '_changed_paths="$(_quality_changed_paths)" || _changed_paths=""\n'
            'quality_paths_match_infra_gate "$_changed_paths"\n'
        )
        result = bash(script, {"QUALITY_HOOKS_MAIN_BRANCH": "nonexistent-branch-xyz-99999"})
        assert result.returncode == 0, (
            "FR-011: gate must return 0 when called with empty paths from a git failure. "
            f"stderr={result.stderr!r}"
        )


class TestQualityPathsMatchForceFullOverride:
    """QUALITY_HOOKS_FORCE_FULL=true makes it return 0 regardless of paths."""

    def test_force_full_overrides_docs_only(self) -> None:
        script = PREAMBLE + 'quality_paths_match_infra_gate "docs/something.md"'
        result = bash(script, {"QUALITY_HOOKS_FORCE_FULL": "true"})
        assert result.returncode == 0, "FORCE_FULL should bypass path check"

    def test_force_full_overrides_empty_paths(self) -> None:
        script = PREAMBLE + 'quality_paths_match_infra_gate ""'
        result = bash(script, {"QUALITY_HOOKS_FORCE_FULL": "true"})
        assert result.returncode == 0

    def test_no_force_full_does_not_override(self) -> None:
        script = PREAMBLE + 'quality_paths_match_infra_gate "docs/README.md"'
        env = {k: v for k, v in os.environ.items() if k != "QUALITY_HOOKS_FORCE_FULL"}
        env["ROOT_DIR"] = str(REPO_ROOT)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0


class TestQualitySpecIsReady:
    """quality_spec_is_ready checks SPEC_READY status in spec.md."""

    def test_spec_ready_true_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            spec_md = spec_dir / "spec.md"
            spec_md.write_text("- SPEC_READY: true\n", encoding="utf-8")
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode == 0, f"SPEC_READY: true should return 0. stderr={result.stderr!r}"

    def test_spec_ready_false_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            spec_md = spec_dir / "spec.md"
            spec_md.write_text("- SPEC_READY: false\n", encoding="utf-8")
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode != 0

    def test_missing_spec_md_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            # No spec.md created
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode != 0

    def test_missing_spec_dir_returns_nonzero(self) -> None:
        script = PREAMBLE + 'quality_spec_is_ready "/nonexistent/path/to/spec"'
        result = bash(script)
        assert result.returncode != 0

    def test_empty_spec_dir_arg_returns_nonzero(self) -> None:
        script = PREAMBLE + 'quality_spec_is_ready ""'
        result = bash(script)
        assert result.returncode != 0

    def test_commented_out_spec_ready_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            spec_md = spec_dir / "spec.md"
            spec_md.write_text("# - SPEC_READY: true\n", encoding="utf-8")
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode != 0, "Commented-out SPEC_READY should return non-zero"

    def test_spec_ready_true_with_other_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            spec_md = spec_dir / "spec.md"
            spec_md.write_text(
                "# Spec Title\n\n"
                "- SPEC_READY: true\n"
                "- Author: test\n",
                encoding="utf-8",
            )
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode == 0

    def test_spec_ready_true_with_trailing_space(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "my-spec"
            spec_dir.mkdir()
            spec_md = spec_dir / "spec.md"
            spec_md.write_text("- SPEC_READY: true   \n", encoding="utf-8")
            script = PREAMBLE + f'quality_spec_is_ready "{spec_dir}"'
            result = bash(script)
            assert result.returncode == 0, "Trailing spaces should still match"


class TestStep05SkillGuardrails:
    """AC-007: step05 SKILL.md must have four new guardrails covering FR-005..FR-008."""

    SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step05-implement/SKILL.md"

    def _content(self) -> str:
        return self.SKILL_MD.read_text(encoding="utf-8")

    def test_spec_value_regression_test_guardrail(self) -> None:
        content = self._content()
        assert "spec-value regression" in content or "spec-enumerated value" in content, (
            "step05 SKILL.md must have a guardrail for spec-value regression tests (AC-007 / FR-005)"
        )

    def test_union_type_guardrail(self) -> None:
        content = self._content()
        assert "union" in content.lower() and "EXACTLY ONE OF" in content, (
            "step05 SKILL.md must have a guardrail for union types on spec-enumerated fields (AC-007 / FR-006)"
        )

    def test_ssot_enum_constant_guardrail(self) -> None:
        content = self._content()
        assert "single source of truth" in content.lower() or "SSOT" in content or "as const" in content, (
            "step05 SKILL.md must have a guardrail for SSOT enum constants (AC-007 / FR-007)"
        )

    def test_rendered_output_coverage_guardrail(self) -> None:
        content = self._content()
        assert "rendered" in content and "critical" in content, (
            "step05 SKILL.md must have a guardrail for mandatory rendered-output coverage (AC-007 / FR-008)"
        )


class TestStep05SkillPerProfileTable:
    """AC-008: step05 SKILL.md must contain a per-profile examples table with TS/Python/Kotlin/Go rows."""

    SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step05-implement/SKILL.md"

    def _content(self) -> str:
        return self.SKILL_MD.read_text(encoding="utf-8")

    def test_typescript_row_present(self) -> None:
        assert "TypeScript" in self._content(), (
            "step05 SKILL.md per-profile table must include a TypeScript row (AC-008 / FR-010)"
        )

    def test_python_row_present(self) -> None:
        assert "Python" in self._content() or "FastAPI" in self._content(), (
            "step05 SKILL.md per-profile table must include a Python row (AC-008 / FR-010)"
        )

    def test_kotlin_row_present(self) -> None:
        assert "Kotlin" in self._content(), (
            "step05 SKILL.md per-profile table must include a Kotlin row (AC-008 / FR-010)"
        )

    def test_go_row_present(self) -> None:
        assert "Go" in self._content() and "Gin" in self._content(), (
            "step05 SKILL.md per-profile table must include a Go row (AC-008 / FR-010)"
        )


class TestStep05SkillVitestEscalation:
    """AC-009: step05 SKILL.md must declare Vitest Browser Mode satisfaction + Playwright escalation rule."""

    SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step05-implement/SKILL.md"

    def _content(self) -> str:
        return self.SKILL_MD.read_text(encoding="utf-8")

    def test_vitest_browser_mode_satisfies_fr008(self) -> None:
        content = self._content()
        assert "Vitest Browser Mode" in content and (
            "satisfies" in content or "satisfy" in content
        ), (
            "step05 SKILL.md must state Vitest Browser Mode component test satisfies the rendered-output guardrail (AC-009 / FR-009)"
        )

    def test_playwright_escalation_rule_present(self) -> None:
        content = self._content()
        assert "Playwright" in content and (
            "route boundaries" in content or "auth/session" in content
        ), (
            "step05 SKILL.md must state Playwright is required when critical path crosses route boundaries or auth/session (AC-009 / FR-009)"
        )


class TestStep03SkillAcAuthoringRule:
    """AC-006: step03 SKILL.md must require the canonical AC form and reject label-only ACs."""

    SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md"

    def _content(self) -> str:
        return self.SKILL_MD.read_text(encoding="utf-8")

    def test_canonical_verified_by_phrase_present(self) -> None:
        assert "verified by T-" in self._content(), (
            "step03 SKILL.md must contain 'verified by T-' in AC authoring guidance (AC-006)"
        )

    def test_which_must_assert_phrase_present(self) -> None:
        assert "which MUST assert" in self._content(), (
            "step03 SKILL.md must contain 'which MUST assert' in AC authoring guidance (AC-006)"
        )

    def test_rejection_rule_for_label_only_acs_present(self) -> None:
        content = self._content()
        assert "label-only" in content or "REJECTED" in content or "reject" in content.lower(), (
            "step03 SKILL.md must contain an explicit rejection rule for label-only ACs (AC-006)"
        )


class TestStep01SkillAcAuthoringGuidance:
    """AC-011 (step01 part): step01 SKILL.md Discover-phase guidance must require canonical AC form."""

    SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step01-intake/SKILL.md"

    def _content(self) -> str:
        return self.SKILL_MD.read_text(encoding="utf-8")

    def test_canonical_verified_by_phrase_present(self) -> None:
        assert "verified by T-" in self._content(), (
            "step01 SKILL.md must contain 'verified by T-' in Discover-phase AC authoring guidance (AC-011 / FR-012)"
        )

    def test_which_must_assert_phrase_present(self) -> None:
        assert "which MUST assert" in self._content(), (
            "step01 SKILL.md must contain 'which MUST assert' in Discover-phase AC authoring guidance (AC-011 / FR-012)"
        )


class TestScaffoldTemplatesAcPlaceholder:
    """AC-011 (scaffold part): both spec scaffold templates must seed AC-001 in canonical form."""

    BLUEPRINT_TEMPLATE = REPO_ROOT / ".spec-kit/templates/blueprint/spec.md"
    CONSUMER_TEMPLATE = REPO_ROOT / ".spec-kit/templates/consumer/spec.md"

    def test_blueprint_template_ac_canonical_form(self) -> None:
        content = self.BLUEPRINT_TEMPLATE.read_text(encoding="utf-8")
        assert "verified by T-" in content, (
            "blueprint spec template AC placeholder must contain 'verified by T-' (AC-011 / FR-012)"
        )
        assert "which MUST assert" in content, (
            "blueprint spec template AC placeholder must contain 'which MUST assert' (AC-011 / FR-012)"
        )

    def test_blueprint_template_legacy_placeholder_removed(self) -> None:
        content = self.BLUEPRINT_TEMPLATE.read_text(encoding="utf-8")
        assert "AC-001 MUST be objectively testable." not in content, (
            "blueprint spec template must not contain the legacy 'AC-001 MUST be objectively testable.' placeholder (FR-012)"
        )

    def test_consumer_template_ac_canonical_form(self) -> None:
        content = self.CONSUMER_TEMPLATE.read_text(encoding="utf-8")
        assert "verified by T-" in content, (
            "consumer spec template AC placeholder must contain 'verified by T-' (AC-011 / FR-012)"
        )
        assert "which MUST assert" in content, (
            "consumer spec template AC placeholder must contain 'which MUST assert' (AC-011 / FR-012)"
        )

    def test_consumer_template_legacy_placeholder_removed(self) -> None:
        content = self.CONSUMER_TEMPLATE.read_text(encoding="utf-8")
        assert "AC-001 MUST be objectively testable." not in content, (
            "consumer spec template must not contain the legacy 'AC-001 MUST be objectively testable.' placeholder (FR-012)"
        )


class TestAgentsMandatoryGateStep03:
    """AC-010: AGENTS.md Mandatory Workflow classifies step03 as a mandatory gate
    and lists the exempt tracks upgrade and chore-with-no-specs."""

    AGENTS_MD = REPO_ROOT / "AGENTS.md"

    def _content(self) -> str:
        return self.AGENTS_MD.read_text(encoding="utf-8")

    def test_mandatory_gate_phrase_present(self) -> None:
        assert "mandatory gate" in self._content(), (
            "AGENTS.md must contain the literal phrase 'mandatory gate' (AC-010 / FR-001)"
        )

    def test_step03_skill_named_as_mandatory_gate(self) -> None:
        content = self._content()
        assert "blueprint-sdd-step03-spec-complete" in content, (
            "AGENTS.md must name blueprint-sdd-step03-spec-complete in the mandatory-gate context (AC-010)"
        )
        idx_gate = content.find("mandatory gate")
        idx_skill = content.find("blueprint-sdd-step03-spec-complete")
        assert abs(idx_gate - idx_skill) < 500, (
            "mandatory gate phrase and blueprint-sdd-step03-spec-complete must appear in close proximity (AC-010)"
        )

    def test_exempt_track_upgrade_present(self) -> None:
        assert "upgrade" in self._content(), (
            "AGENTS.md must list the 'upgrade' exempt track (AC-010 / FR-003)"
        )

    def test_exempt_track_chore_no_specs_present(self) -> None:
        content = self._content()
        assert "chore-with-no-specs" in content or "chore-no-specs" in content, (
            "AGENTS.md must list the chore-with-no-specs exempt track (AC-010 / FR-003)"
        )
