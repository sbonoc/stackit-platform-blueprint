"""Tests for workaround_report_parser — Slice 0 (issue-268-consumer-workarounds-catalogue).

FR-012: Parser extracts structured fields from the ## Automated Workaround Catalogue Entry
section of a GitHub issue body rendered as markdown.
"""
from __future__ import annotations

import textwrap

import pytest

from scripts.lib.blueprint.workaround_report_parser import (
    ParsedWorkaroundReport,
    parse_issue_body,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KNOWN_VALID_BODY = textwrap.dedent(
    """
    ### What happened?

    Something broke.

    ### Reproduction

    ```bash
    make something
    ```

    ### Expected behavior

    It should work.

    ### Temporary workaround path (if any)

    docs/troubleshooting.md

    ### Replacement trigger

    merged PR in blueprint repo

    ### Workaround review date

    2026-12-01

    ## Automated Workaround Catalogue Entry

    Fill this section only when you have a concrete consumer-side fix to automate.

    ### affected_version

    v1.10.0

    ### action_kind

    contract_merge

    ### applies_when

    always

    ### action_content

    source_only:
      - pyproject.toml
      - uv.lock
    """
)

_ISSUE_NUMBER = "258"
_ISSUE_URL = "https://github.com/sbonoc/stackit-platform-blueprint/issues/258"
_ISSUE_TITLE = "v1.10.0: source-tree coverage gap — 4 unclassified source files"


# ---------------------------------------------------------------------------
# FR-012: parser extracts all four fields
# ---------------------------------------------------------------------------


def test_workaround_report_parser_extracts_all_fields() -> None:
    result = parse_issue_body(
        body=_KNOWN_VALID_BODY,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title=_ISSUE_TITLE,
    )
    assert result is not None
    assert isinstance(result, ParsedWorkaroundReport)
    assert result.issue_number == "258"
    assert result.issue_url == _ISSUE_URL
    assert result.issue_title == _ISSUE_TITLE
    assert result.affected_version == "v1.10.0"
    assert result.action_kind == "contract_merge"
    assert result.applies_when == "always"
    assert "pyproject.toml" in result.action_content
    assert "uv.lock" in result.action_content


# ---------------------------------------------------------------------------
# FR-012: action file name derivation
# ---------------------------------------------------------------------------


def test_workaround_report_parser_produces_correct_action_filename() -> None:
    result = parse_issue_body(
        body=_KNOWN_VALID_BODY,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title=_ISSUE_TITLE,
    )
    assert result is not None
    # contract_merge → .yaml extension
    assert result.action_filename.endswith(".yaml")
    # filename starts with issue number
    assert result.action_filename.startswith("258_")
    # full action_path is version-prefixed
    assert result.action_path == f"workarounds/v1.10.0/{result.action_filename}"


# ---------------------------------------------------------------------------
# FR-012: manifest entry stub has all 8 required fields
# ---------------------------------------------------------------------------


def test_workaround_report_parser_produces_manifest_entry_stub() -> None:
    result = parse_issue_body(
        body=_KNOWN_VALID_BODY,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title=_ISSUE_TITLE,
    )
    assert result is not None
    stub = result.manifest_entry_stub()
    assert stub["id"] == "258"
    assert stub["upstream_issue"] == _ISSUE_URL
    assert stub["title"] == _ISSUE_TITLE
    assert stub["applies_when"] == "always"
    assert stub["action_kind"] == "contract_merge"
    assert stub["action_path"] == result.action_path
    assert "before_apply" in stub["apply_phase"] or "after_apply" in stub["apply_phase"]
    assert stub["landed_in"] is None


# ---------------------------------------------------------------------------
# FR-012: unknown action_kind raises ValueError
# ---------------------------------------------------------------------------


def test_workaround_report_parser_unknown_action_kind_raises() -> None:
    body_with_bad_kind = _KNOWN_VALID_BODY.replace(
        "### action_kind\n\ncontract_merge",
        "### action_kind\n\nenv_var",
    )
    with pytest.raises(ValueError, match="action_kind"):
        parse_issue_body(
            body=body_with_bad_kind,
            issue_number=_ISSUE_NUMBER,
            issue_url=_ISSUE_URL,
            issue_title=_ISSUE_TITLE,
        )


# ---------------------------------------------------------------------------
# FR-012: section absent → None
# ---------------------------------------------------------------------------


def test_workaround_report_parser_returns_none_when_section_absent() -> None:
    body_without_section = "### What happened?\n\nSomething broke.\n"
    result = parse_issue_body(
        body=body_without_section,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title=_ISSUE_TITLE,
    )
    assert result is None


# ---------------------------------------------------------------------------
# FR-012: all blank fields → None
# ---------------------------------------------------------------------------


def test_workaround_report_parser_returns_none_when_all_fields_blank() -> None:
    body_blank = textwrap.dedent(
        """
        ## Automated Workaround Catalogue Entry

        ### affected_version

        _No response_

        ### action_kind

        _No response_

        ### applies_when

        _No response_

        ### action_content

        _No response_
        """
    )
    result = parse_issue_body(
        body=body_blank,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title=_ISSUE_TITLE,
    )
    assert result is None


# ---------------------------------------------------------------------------
# FR-012: blank affected_version raises ValueError (action_path would be malformed)
# ---------------------------------------------------------------------------


def test_workaround_report_parser_raises_when_affected_version_blank() -> None:
    body_no_version = _KNOWN_VALID_BODY.replace(
        "### affected_version\n\nv1.10.0",
        "### affected_version\n\n_No response_",
    )
    with pytest.raises(ValueError, match="affected_version"):
        parse_issue_body(
            body=body_no_version,
            issue_number=_ISSUE_NUMBER,
            issue_url=_ISSUE_URL,
            issue_title=_ISSUE_TITLE,
        )


# ---------------------------------------------------------------------------
# FR-012: manifest_entry_stub strips [workaround] prefix from title
# ---------------------------------------------------------------------------


def test_workaround_report_parser_strips_workaround_prefix_from_stub_title() -> None:
    result = parse_issue_body(
        body=_KNOWN_VALID_BODY,
        issue_number=_ISSUE_NUMBER,
        issue_url=_ISSUE_URL,
        issue_title="[workaround] v1.10.0: source-tree coverage gap",
    )
    assert result is not None
    stub = result.manifest_entry_stub()
    assert stub["title"] == "v1.10.0: source-tree coverage gap"


# ---------------------------------------------------------------------------
# patch action kind → .patch extension
# ---------------------------------------------------------------------------


def test_workaround_report_parser_patch_extension() -> None:
    body_patch = _KNOWN_VALID_BODY.replace(
        "### action_kind\n\ncontract_merge",
        "### action_kind\n\npatch",
    )
    result = parse_issue_body(
        body=body_patch,
        issue_number="260",
        issue_url="https://github.com/sbonoc/stackit-platform-blueprint/issues/260",
        issue_title="v1.10.0: template-smoke skip for generated-consumer",
    )
    assert result is not None
    assert result.action_filename.endswith(".patch")


# ---------------------------------------------------------------------------
# python_script action kind → .py extension
# ---------------------------------------------------------------------------


def test_workaround_report_parser_python_script_extension() -> None:
    body_py = _KNOWN_VALID_BODY.replace(
        "### action_kind\n\ncontract_merge",
        "### action_kind\n\npython_script",
    )
    result = parse_issue_body(
        body=body_py,
        issue_number="999",
        issue_url="https://github.com/sbonoc/stackit-platform-blueprint/issues/999",
        issue_title="v1.10.0: some python fix",
    )
    assert result is not None
    assert result.action_filename.endswith(".py")
