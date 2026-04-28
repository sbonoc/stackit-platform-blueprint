"""Tests for AGENTS.md quality hooks subsection and consumer-init template mirror.

Slice 10 — AC-016 (subsection body invariants, consumer template mirror).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_MD = REPO_ROOT / "AGENTS.md"
CONSUMER_INIT_TMPL = REPO_ROOT / "scripts/templates/consumer/init/AGENTS.md.tmpl"


def _read_agents() -> str:
    return AGENTS_MD.read_text(encoding="utf-8")


def _read_tmpl() -> str:
    return CONSUMER_INIT_TMPL.read_text(encoding="utf-8")


class TestAgentsMdQualityHooksSubsection:
    """AGENTS.md contains the canonical Quality Hooks subsection (AC-016)."""

    def test_subsection_title_present(self) -> None:
        content = _read_agents()
        assert "## Quality Hooks — Inner-Loop and Pre-PR Usage" in content, (
            "AGENTS.md must contain '## Quality Hooks — Inner-Loop and Pre-PR Usage' subsection"
        )

    def test_quality_hooks_keep_going_env_var_documented(self) -> None:
        content = _read_agents()
        assert "QUALITY_HOOKS_KEEP_GOING" in content, (
            "AGENTS.md must document QUALITY_HOOKS_KEEP_GOING env var"
        )

    def test_must_language_present(self) -> None:
        content = _read_agents()
        # Check for normative MUST language
        assert "MUST" in content, "AGENTS.md quality hooks section must use normative MUST language"

    def test_per_slice_gate_documented(self) -> None:
        content = _read_agents()
        assert "per-slice" in content.lower() or "per slice" in content.lower(), (
            "AGENTS.md must document the per-slice gate"
        )
        assert "test-unit-all" in content, "AGENTS.md must reference make test-unit-all as per-slice gate"

    def test_pre_pr_gate_documented(self) -> None:
        content = _read_agents()
        assert "quality-hooks-fast" in content, (
            "AGENTS.md must document quality-hooks-fast as the pre-PR gate"
        )

    def test_quality_hooks_force_full_documented(self) -> None:
        content = _read_agents()
        assert "QUALITY_HOOKS_FORCE_FULL" in content, (
            "AGENTS.md must document QUALITY_HOOKS_FORCE_FULL env var"
        )

    def test_path_gating_described(self) -> None:
        content = _read_agents()
        lower = content.lower()
        assert "path-gating" in lower or "path gating" in lower, (
            "AGENTS.md must describe path-gating concept"
        )

    def test_failure_cascade_caveat_present(self) -> None:
        content = _read_agents()
        lower = content.lower()
        assert "failure-cascade" in lower or "failure cascade" in lower or "root cause" in lower, (
            "AGENTS.md must include failure-cascade caveat"
        )


class TestConsumerInitTemplateMirror:
    """Consumer-init AGENTS.md.tmpl mirrors the quality hooks subsection (AC-016)."""

    def test_consumer_template_has_quality_hooks_section(self) -> None:
        content = _read_tmpl()
        assert "Quality Hooks" in content, (
            "Consumer-init AGENTS.md.tmpl must mirror the Quality Hooks section"
        )

    def test_consumer_template_has_keep_going_env_var(self) -> None:
        content = _read_tmpl()
        assert "QUALITY_HOOKS_KEEP_GOING" in content, (
            "Consumer-init AGENTS.md.tmpl must reference QUALITY_HOOKS_KEEP_GOING"
        )
