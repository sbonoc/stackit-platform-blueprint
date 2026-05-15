"""Tests for AGENTS.md structural contract enforcement.

AC-011: check_agents_md_structure.py exits 1 and emits a named violation when:
        - AGENTS.md is missing ## Architecture Invariants — Pointers section header
        - AGENTS.md is missing north_star.md reference within ## Mandatory Workflow
        Each missing element produces exactly one violation.
AC-012: exits 0 when all required structural elements are present;
        exits 0 when AGENTS.md is absent (graceful skip).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = REPO_ROOT / "scripts/bin/quality/check_agents_md_structure.py"

_COMPLIANT_AGENTS_MD = """\
## Architecture Invariants — Pointers

AGENTS.md does NOT contain architecture content.

| Domain | `north_star.md` section | Canonical ADR(s) |
|---|---|---|
| Example Domain | § Example Section | ADR-issue-XXX |

## Mandatory Workflow
1. Read AGENTS.md before starting work.
2. Before any SDD work touching a domain, MUST read the north_star.md section and canonical ADRs. MUST NOT duplicate architecture content in AGENTS.md.
"""

_NO_POINTERS_SECTION = """\
## Mandatory Workflow
1. Read AGENTS.md before starting work.
2. Before any SDD work touching a domain, MUST read the north_star.md section. MUST NOT duplicate.
"""

_NO_NORTH_STAR_IN_MWF = """\
## Architecture Invariants — Pointers

AGENTS.md does NOT contain architecture content.

## Mandatory Workflow
1. Read AGENTS.md before starting work.
2. Follow the SDD lifecycle.
"""

_NEITHER = """\
## Mandatory Workflow
1. Read AGENTS.md before starting work.
2. Follow the SDD lifecycle.
"""


def _load_checker():
    name = "check_agents_md_structure_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestStructureCheckUnit:
    """Unit tests for _check_structure — pure function, no file I/O."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def test_compliant_content_returns_no_violations(self, checker) -> None:
        violations = checker._check_structure(_COMPLIANT_AGENTS_MD)
        assert violations == []

    def test_missing_pointers_section_returns_one_violation(self, checker) -> None:
        violations = checker._check_structure(_NO_POINTERS_SECTION)
        assert len(violations) == 1
        assert "Architecture Invariants" in violations[0]

    def test_missing_north_star_rule_returns_one_violation(self, checker) -> None:
        violations = checker._check_structure(_NO_NORTH_STAR_IN_MWF)
        assert len(violations) == 1
        assert "north_star.md" in violations[0]

    def test_both_missing_returns_two_violations(self, checker) -> None:
        violations = checker._check_structure(_NEITHER)
        assert len(violations) == 2


class TestStructureCheckMain:
    """Integration tests for main() — file I/O with temp repos."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def test_all_present_exits_zero(self, checker, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "AGENTS.md").write_text(_COMPLIANT_AGENTS_MD, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        assert checker.main() == 0

    def test_missing_pointers_section_exits_one(self, checker, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "AGENTS.md").write_text(_NO_POINTERS_SECTION, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        assert checker.main() == 1

    def test_missing_north_star_rule_exits_one(self, checker, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "AGENTS.md").write_text(_NO_NORTH_STAR_IN_MWF, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        assert checker.main() == 1

    def test_both_missing_exits_one_with_two_violations(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        (tmp_path / "AGENTS.md").write_text(_NEITHER, encoding="utf-8")
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        exit_code = checker.main()
        assert exit_code == 1
        stderr = capsys.readouterr().err
        assert stderr.count("[quality-docs-agents-md-structure-check]") == 2

    def test_absent_agents_md_exits_zero(self, checker, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        assert checker.main() == 0
