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
