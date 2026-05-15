"""Tests for AGENTS.md ↔ north_star.md cross-reference quality check.

AC-001: AGENTS.md.tmpl contains Architecture Invariants — Pointers section.
AC-002: AGENTS.md.tmpl Mandatory Workflow contains north_star.md anti-duplication rule.
AC-003: check_docs_cross_reference.py exits 1 on heading match without allowlist.
AC-004: exits 0 when matching heading is in Pointers table.
AC-005: exits 0 when matching heading is in allowlist with non-empty justification.
AC-007: exits 0 for clean files, absent AGENTS.md, absent north_star.md, missing allowlist.
AC-008: Blueprint's own AGENTS.md Mandatory Workflow contains north_star.md MUST-read rule.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONSUMER_INIT_TMPL = REPO_ROOT / "scripts/templates/consumer/init/AGENTS.md.tmpl"
BLUEPRINT_AGENTS_MD = REPO_ROOT / "AGENTS.md"
_SCRIPT_PATH = REPO_ROOT / "scripts/bin/quality/check_docs_cross_reference.py"


def _load_checker():
    name = "check_docs_cross_reference_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestTemplateSectionPresence:
    """AC-001: AGENTS.md.tmpl contains the Architecture Invariants — Pointers section."""

    def test_pointers_section_present(self) -> None:
        content = CONSUMER_INIT_TMPL.read_text(encoding="utf-8")
        assert "## Architecture Invariants — Pointers" in content, (
            "AGENTS.md.tmpl must contain '## Architecture Invariants — Pointers' section"
        )

    def test_anti_duplication_statement_present(self) -> None:
        content = CONSUMER_INIT_TMPL.read_text(encoding="utf-8")
        assert "AGENTS.md does NOT contain architecture content" in content, (
            "AGENTS.md.tmpl Pointers section must contain an explicit anti-duplication statement"
        )

    def test_pointers_table_has_placeholder_row(self) -> None:
        content = CONSUMER_INIT_TMPL.read_text(encoding="utf-8")
        assert "| Example Domain |" in content, (
            "AGENTS.md.tmpl Pointers table must include at least one placeholder domain row"
        )

    def test_add_to_north_star_instruction_present(self) -> None:
        content = CONSUMER_INIT_TMPL.read_text(encoding="utf-8")
        lower = content.lower()
        assert "north_star.md" in lower and ("do not inline" in lower or "must not" in lower or "must be recorded" in lower), (
            "AGENTS.md.tmpl must instruct consumers to add new concerns to north_star.md, not inline them"
        )


class TestTemplateMandatoryWorkflowRule:
    """AC-002: AGENTS.md.tmpl Mandatory Workflow contains north_star.md anti-duplication rule."""

    def _mandatory_workflow_body(self) -> str:
        content = CONSUMER_INIT_TMPL.read_text(encoding="utf-8")
        start = content.find("## Mandatory Workflow")
        assert start != -1, "Template must have ## Mandatory Workflow section"
        end = content.find("\n## ", start + 1)
        return content[start: end if end != -1 else len(content)]

    def test_mandatory_workflow_rule_present(self) -> None:
        body = self._mandatory_workflow_body()
        assert "north_star.md" in body, (
            "AGENTS.md.tmpl Mandatory Workflow must reference north_star.md"
        )

    def test_must_not_duplicate_language_present(self) -> None:
        body = self._mandatory_workflow_body()
        assert "MUST NOT" in body, (
            "AGENTS.md.tmpl Mandatory Workflow must use 'MUST NOT' to prohibit architecture content duplication"
        )


class TestBlueprintAgentsMd:
    """AC-008: Blueprint AGENTS.md Mandatory Workflow contains north_star.md MUST-read rule."""

    def _mandatory_workflow_body(self) -> str:
        content = BLUEPRINT_AGENTS_MD.read_text(encoding="utf-8")
        start = content.find("## Mandatory Workflow")
        assert start != -1, "Blueprint AGENTS.md must have ## Mandatory Workflow section"
        end = content.find("\n## ", start + 1)
        return content[start: end if end != -1 else len(content)]

    def test_blueprint_agents_md_north_star_rule_present(self) -> None:
        body = self._mandatory_workflow_body()
        assert "docs/blueprint/architecture/north_star.md" in body, (
            "Blueprint AGENTS.md Mandatory Workflow must reference docs/blueprint/architecture/north_star.md"
        )

    def test_blueprint_agents_md_must_not_duplicate(self) -> None:
        body = self._mandatory_workflow_body()
        assert "MUST NOT" in body, (
            "Blueprint AGENTS.md Mandatory Workflow must use 'MUST NOT' to prohibit content duplication"
        )


class TestHeadingDetection:
    """AC-003, AC-004, AC-005, AC-007: exit code semantics for heading detection."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    @pytest.fixture
    def repo(self, tmp_path: Path) -> Path:
        north_star_dir = tmp_path / "docs" / "blueprint" / "architecture"
        north_star_dir.mkdir(parents=True)
        return tmp_path

    def _write_agents(self, repo: Path, content: str) -> None:
        (repo / "AGENTS.md").write_text(content, encoding="utf-8")

    def _write_north_star(self, repo: Path, content: str) -> None:
        (repo / "docs" / "blueprint" / "architecture" / "north_star.md").write_text(
            content, encoding="utf-8"
        )

    def test_clean_files_exit_zero(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## Agent Rules\n\n- Do things.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_heading_match_without_allowlist_exits_one(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## Architecture Invariants\n\n- Some rule.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 1

    def test_heading_in_pointers_table_exits_zero(self, checker, repo: Path, monkeypatch) -> None:
        agents_content = (
            "## Architecture Invariants — Pointers\n\n"
            "| Domain | `north_star.md` section | Canonical ADR(s) |\n"
            "|---|---|---|\n"
            "| Architecture Invariants | § Architecture Invariants | ADR-XYZ |\n\n"
            "## Architecture Invariants\n\n- Pointer to north_star.md section.\n"
        )
        self._write_agents(repo, agents_content)
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_heading_in_allowlist_exits_zero(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## Architecture Invariants\n\n- Some rule.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        allowlist = (
            "entries:\n"
            "  - heading: Architecture Invariants\n"
            "    justification: Intentionally mirrored as a navigation pointer.\n"
        )
        (repo / ".quality-docs-cross-reference-allowlist.yml").write_text(allowlist, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_absent_agents_md_exits_zero(self, checker, repo: Path, monkeypatch) -> None:
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_absent_north_star_exits_zero(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## Architecture Invariants\n\n- Some rule.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_missing_allowlist_exits_zero(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## Agent Rules\n\n- Do things.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 0

    def test_case_insensitive_normalization(self, checker, repo: Path, monkeypatch) -> None:
        self._write_agents(repo, "## ARCHITECTURE INVARIANTS\n\n- Some rule.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        assert checker.main() == 1

    def test_allowlist_entry_missing_justification_does_not_exempt(
        self, checker, repo: Path, monkeypatch, capsys
    ) -> None:
        self._write_agents(repo, "## Architecture Invariants\n\n- Some rule.\n")
        self._write_north_star(repo, "## Architecture Invariants\n\nContent here.\n")
        allowlist = (
            "entries:\n"
            "  - heading: Architecture Invariants\n"
            "    justification: \n"
        )
        (repo / ".quality-docs-cross-reference-allowlist.yml").write_text(allowlist, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", repo)
        result = checker.main()
        assert result == 1
        assert "missing justification" in capsys.readouterr().err
