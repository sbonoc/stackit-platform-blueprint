"""Tests for workaround_report_filer — Slice 6b (issue-268-consumer-workarounds-catalogue).

FR-013, FR-014: After a consumer agent applies a manual fix to a blueprint-managed
file, the skill extension files a structured workaround-report issue. Before filing,
it checks for duplicates. Filing failure is non-fatal.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from scripts.lib.blueprint.workaround_report_filer import (
    WorkaroundReportFiler,
    file_workaround_report,
)


_BLUEPRINT_REPO = "sbonoc/stackit-platform-blueprint"
_AFFECTED_VERSION = "v1.10.0"
_DESCRIPTION = "template-smoke skip for generated-consumer"
_ACTION_KIND = "patch"
_APPLIES_WHEN = "repo_mode: generated-consumer"
_ACTION_CONTENT = "--- a/foo.py\n+++ b/foo.py\n@@ -1 +1,2 @@\n line\n+added\n"


class TestWorkaroundReportFilerCreateIssue(unittest.TestCase):
    """FR-013: gh issue create is called with correct fields."""

    @patch("scripts.lib.blueprint.workaround_report_filer.subprocess.run")
    def test_workaround_report_filer_calls_gh_issue_create_with_correct_fields(
        self, mock_run: MagicMock
    ) -> None:
        # First call: gh issue list (no duplicates found)
        list_result = MagicMock()
        list_result.returncode = 0
        list_result.stdout = "[]"
        # Second call: gh issue create (success)
        create_result = MagicMock()
        create_result.returncode = 0
        create_result.stdout = "https://github.com/sbonoc/stackit-platform-blueprint/issues/300"
        mock_run.side_effect = [list_result, create_result]

        filer = WorkaroundReportFiler(blueprint_repo=_BLUEPRINT_REPO)
        url = filer.file(
            affected_version=_AFFECTED_VERSION,
            description=_DESCRIPTION,
            action_kind=_ACTION_KIND,
            applies_when=_APPLIES_WHEN,
            action_content=_ACTION_CONTENT,
        )

        assert url is not None
        create_call = mock_run.call_args_list[1]
        cmd = create_call.args[0]
        body = cmd[cmd.index("--body") + 1]

        assert "[workaround]" in cmd[cmd.index("--title") + 1]
        assert f"v{_AFFECTED_VERSION.lstrip('v')}" in cmd[cmd.index("--title") + 1]
        assert "## Automated Workaround Catalogue Entry" in body
        assert _AFFECTED_VERSION in body
        assert _ACTION_KIND in body
        assert _APPLIES_WHEN in body
        assert "workaround-report" in cmd
        assert _BLUEPRINT_REPO in cmd

    @patch("scripts.lib.blueprint.workaround_report_filer.subprocess.run")
    def test_workaround_report_filer_skips_when_duplicate_exists(
        self, mock_run: MagicMock
    ) -> None:
        list_result = MagicMock()
        list_result.returncode = 0
        # Return a JSON list with a matching title
        import json
        list_result.stdout = json.dumps(
            [{"title": f"[workaround] {_DESCRIPTION} (v{_AFFECTED_VERSION.lstrip('v')})"}]
        )
        mock_run.return_value = list_result

        filer = WorkaroundReportFiler(blueprint_repo=_BLUEPRINT_REPO)
        url = filer.file(
            affected_version=_AFFECTED_VERSION,
            description=_DESCRIPTION,
            action_kind=_ACTION_KIND,
            applies_when=_APPLIES_WHEN,
            action_content=_ACTION_CONTENT,
        )

        # Only one subprocess call (the list search); gh issue create NOT called
        assert mock_run.call_count == 1
        assert url is None

    @patch("scripts.lib.blueprint.workaround_report_filer.subprocess.run")
    def test_workaround_report_filer_is_nonfatal_on_gh_failure(
        self, mock_run: MagicMock
    ) -> None:
        list_result = MagicMock()
        list_result.returncode = 0
        list_result.stdout = "[]"
        create_result = MagicMock()
        create_result.returncode = 1
        create_result.stderr = "gh: command failed"
        mock_run.side_effect = [list_result, create_result]

        filer = WorkaroundReportFiler(blueprint_repo=_BLUEPRINT_REPO)
        # Must not raise even when gh fails
        url = filer.file(
            affected_version=_AFFECTED_VERSION,
            description=_DESCRIPTION,
            action_kind=_ACTION_KIND,
            applies_when=_APPLIES_WHEN,
            action_content=_ACTION_CONTENT,
        )
        assert url is None


class TestFileWorkaroundReportHelper(unittest.TestCase):
    """Convenience wrapper returns None (non-fatal) on any failure."""

    @patch("scripts.lib.blueprint.workaround_report_filer.subprocess.run")
    def test_file_workaround_report_convenience_function(self, mock_run: MagicMock) -> None:
        list_result = MagicMock()
        list_result.returncode = 0
        list_result.stdout = "[]"
        create_result = MagicMock()
        create_result.returncode = 0
        create_result.stdout = "https://github.com/sbonoc/stackit-platform-blueprint/issues/301"
        mock_run.side_effect = [list_result, create_result]

        url = file_workaround_report(
            blueprint_repo=_BLUEPRINT_REPO,
            affected_version=_AFFECTED_VERSION,
            description=_DESCRIPTION,
            action_kind=_ACTION_KIND,
            applies_when=_APPLIES_WHEN,
            action_content=_ACTION_CONTENT,
        )
        assert url is not None
