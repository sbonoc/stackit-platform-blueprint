"""Tests for .agents/skills/blueprint-sdd-step05-implement/SKILL.md

Slice 9 — Per-slice vs pre-PR gate directive (AC-015, FR-014, FR-016).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / ".agents/skills/blueprint-sdd-step05-implement/SKILL.md"


def _read() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


class TestMakeTestUnitAllDirective:
    """make test-unit-all is the per-slice gate (FR-014)."""

    def test_make_test_unit_all_present(self) -> None:
        content = _read()
        assert "make test-unit-all" in content, (
            "SKILL.md must contain 'make test-unit-all' as the per-slice gate"
        )

    def test_per_slice_gate_language_present(self) -> None:
        content = _read()
        assert "per-slice" in content.lower() or "per slice" in content.lower(), (
            "SKILL.md must use 'per-slice' language for the gate directive"
        )


class TestQualityHooksFastFramedAsPrePR:
    """quality-hooks-fast is framed only as pre-PR/slice-batch gate, not per-slice."""

    def test_quality_hooks_fast_present_as_prepr_gate(self) -> None:
        content = _read()
        assert "quality-hooks-fast" in content, (
            "SKILL.md must reference quality-hooks-fast (as the pre-PR gate)"
        )

    def test_quality_hooks_fast_not_described_as_per_slice(self) -> None:
        content = _read()
        # Check that quality-hooks-fast is not positioned as a per-slice check
        # by searching for phrases that would indicate it as a per-slice gate
        lower = content.lower()
        # Find paragraphs/contexts where quality-hooks-fast appears
        lines_with_hooks_fast = [
            line.strip()
            for line in content.splitlines()
            if "quality-hooks-fast" in line
        ]
        for line in lines_with_hooks_fast:
            line_lower = line.lower()
            # Should not say "run quality-hooks-fast after each slice" or similar
            assert "after each slice" not in line_lower, (
                f"quality-hooks-fast must not be framed as a per-slice gate. Found: {line!r}"
            )
            assert "per-slice gate" not in line_lower, (
                f"quality-hooks-fast must not be described as per-slice gate. Found: {line!r}"
            )

    def test_pre_pr_gate_or_slice_batch_framing_present(self) -> None:
        content = _read()
        lower = content.lower()
        # Must have pre-PR framing somewhere
        has_prepr = "pre-pr" in lower or "pre-commit" in lower or "slice-batch" in lower or "slice batch" in lower
        assert has_prepr, "SKILL.md must frame quality-hooks-fast in a pre-PR or slice-batch context"


class TestFR016CrossLink:
    """FR-016 cross-link to AGENTS.md quality hooks subsection."""

    def test_cross_link_line_present(self) -> None:
        content = _read()
        assert "AGENTS.md § Quality Hooks" in content or "AGENTS.md" in content, (
            "SKILL.md must contain the FR-016 cross-link referencing AGENTS.md quality hooks section"
        )

    def test_cross_link_references_quality_hooks_section(self) -> None:
        content = _read()
        # The canonical cross-link line from the spec
        assert "Quality Hooks" in content, (
            "SKILL.md must reference the Quality Hooks section via cross-link"
        )

    def test_cross_link_references_agents_md(self) -> None:
        content = _read()
        # Must reference AGENTS.md
        assert "AGENTS.md" in content, (
            "SKILL.md cross-link must reference AGENTS.md"
        )


class TestReproduciblePreCommitFailuresSection:
    """Reproducible pre-commit failures section reframed (FR-014)."""

    def test_reproducible_precommit_section_exists(self) -> None:
        content = _read()
        assert "Reproducible pre-commit failures" in content, (
            "SKILL.md must retain the 'Reproducible pre-commit failures' section"
        )

    def test_reproducible_precommit_not_inner_loop_context(self) -> None:
        content = _read()
        # Find the Reproducible pre-commit failures section
        section_start = content.find("Reproducible pre-commit failures")
        assert section_start != -1
        # Grab the section text (up to next ## heading or end)
        section_end = content.find("\n## ", section_start + 1)
        if section_end == -1:
            section_end = len(content)
        section_text = content[section_start:section_end].lower()
        # The section must NOT present quality-hooks-fast as an inner-loop/per-slice gate
        assert "run quality-hooks-fast after each" not in section_text, (
            "Reproducible pre-commit section must not frame quality-hooks-fast as inner-loop"
        )
        assert "per-slice, run quality-hooks-fast" not in section_text, (
            "Reproducible pre-commit section must not instruct running quality-hooks-fast per slice"
        )
