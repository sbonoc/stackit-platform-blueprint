from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._shared.helpers import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "scripts/lib/blueprint/uplift_status.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("uplift_status", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_m = _load_module()
_parse_backlog = _m._parse_backlog
_query_issue_state = _m._query_issue_state
_build_report = _m._build_report
UpliftEntry = _m.UpliftEntry


# ---------------------------------------------------------------------------
# Backlog parsing
# ---------------------------------------------------------------------------

class BacklogParsingTests(unittest.TestCase):

    def _write_backlog(self, tmpdir: str, content: str) -> Path:
        p = Path(tmpdir) / "AGENTS.backlog.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_unchecked_markdown_link_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [ ] [#25](https://github.com/org/repo/issues/25) async scaffold.\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].issue_id, 25)
            self.assertEqual(entries[0].line_no, 1)

    def test_checked_line_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [x] [#13](https://github.com/org/repo/issues/13) done item.\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(entries, [])

    def test_indented_unchecked_line_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [ ] Track upstream issues:\n"
                "  - [ ] [#1](https://github.com/org/repo/issues/1) OpenSearch.\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].issue_id, 1)

    def test_unchecked_group_header_without_issue_link_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [ ] Track upstream P1 issues (can run in parallel after P0 starts landing):\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(entries, [])

    def test_mixed_checked_and_unchecked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "- [ ] Track upstream P1 issues:\n"
                "  - [ ] [#25](https://github.com/org/repo/issues/25) async Pact.\n"
                "  - [x] [#13](https://github.com/org/repo/issues/13) optional scaffold.\n"
                "  - [ ] [#1](https://github.com/org/repo/issues/1) OpenSearch.\n"
                "  - [x] [#12](https://github.com/org/repo/issues/12) kube helper.\n"
            )
            p = self._write_backlog(tmpdir, content)
            entries = _parse_backlog(p, "org/repo")
            ids = [e.issue_id for e in entries]
            self.assertEqual(sorted(ids), [1, 25])

    def test_wrong_repo_url_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [ ] [#5](https://github.com/other/repo/issues/5) some item.\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(entries, [])

    def test_multiple_links_on_same_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = self._write_backlog(tmpdir, (
                "- [ ] [#3](https://github.com/org/repo/issues/3) and [#4](https://github.com/org/repo/issues/4).\n"
            ))
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(sorted(e.issue_id for e in entries), [3, 4])

    def test_missing_backlog_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "AGENTS.backlog.md"
            entries = _parse_backlog(p, "org/repo")
            self.assertEqual(entries, [])


# ---------------------------------------------------------------------------
# Issue state query (mocked gh CLI)
# ---------------------------------------------------------------------------

class QueryIssueStateTests(unittest.TestCase):

    def test_open_state_returned(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="OPEN\n", stderr="")
            state = _query_issue_state(25, "org/repo")
        self.assertEqual(state, "OPEN")

    def test_closed_state_returned(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="CLOSED\n", stderr="")
            state = _query_issue_state(13, "org/repo")
        self.assertEqual(state, "CLOSED")

    def test_nonzero_returncode_returns_unknown(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=1, stdout="", stderr="error")
            state = _query_issue_state(99, "org/repo")
        self.assertEqual(state, "UNKNOWN")

    def test_exception_returns_unknown(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("gh not found")):
            state = _query_issue_state(1, "org/repo")
        self.assertEqual(state, "UNKNOWN")

    def test_unexpected_state_value_returns_unknown(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="MERGED\n", stderr="")
            state = _query_issue_state(5, "org/repo")
        self.assertEqual(state, "UNKNOWN")


# ---------------------------------------------------------------------------
# Classification / report building
# ---------------------------------------------------------------------------

class BuildReportTests(unittest.TestCase):

    def _entries(self, *ids: int) -> list[UpliftEntry]:
        return [UpliftEntry(i, f"- [ ] line for #{i}", i) for i in ids]

    def _report(self, entries, issue_states, strict=False, query_failures=0):
        return _build_report(
            entries=entries,
            issue_states=issue_states,
            query_failures=query_failures,
            uplift_repo="org/repo",
            backlog_path="AGENTS.backlog.md",
            strict_mode=strict,
            repo_root=Path("/tmp/fake"),
        )

    def test_open_issue_classified_as_none(self) -> None:
        report = self._report(self._entries(25), {25: "OPEN"})
        self.assertEqual(report["issues"][0]["classification"], "none")
        self.assertEqual(report["open_count"], 1)
        self.assertEqual(report["action_required_count"], 0)

    def test_closed_issue_with_unresolved_lines_classified_as_required(self) -> None:
        report = self._report(self._entries(13), {13: "CLOSED"})
        self.assertEqual(report["issues"][0]["classification"], "required")
        self.assertEqual(report["action_required_count"], 1)
        self.assertIn(13, report["action_required_issues"])

    def test_unknown_state_classified_as_none_with_unknown_count(self) -> None:
        report = self._report(self._entries(99), {99: "UNKNOWN"}, query_failures=1)
        self.assertEqual(report["issues"][0]["classification"], "none")
        self.assertEqual(report["unknown_count"], 1)
        self.assertEqual(report["query_failures"], 1)

    def test_tracked_total_deduplicates_same_issue_on_multiple_lines(self) -> None:
        entries = [
            UpliftEntry(10, "line A", 1),
            UpliftEntry(10, "line B", 2),
        ]
        report = self._report(entries, {10: "CLOSED"})
        self.assertEqual(report["tracked_total"], 1)
        self.assertEqual(report["issues"][0]["unresolved_lines"], 2)
        self.assertEqual(report["action_required_count"], 1)

    def test_zero_tracked_produces_success(self) -> None:
        report = self._report([], {})
        self.assertEqual(report["tracked_total"], 0)
        self.assertEqual(report["status"], "success")

    def test_strict_mode_with_action_required_produces_failure_status(self) -> None:
        report = self._report(self._entries(13), {13: "CLOSED"}, strict=True)
        self.assertEqual(report["status"], "failure")

    def test_non_strict_mode_with_action_required_produces_success_status(self) -> None:
        report = self._report(self._entries(13), {13: "CLOSED"}, strict=False)
        self.assertEqual(report["status"], "success")

    def test_strict_mode_with_query_failures_produces_failure_status(self) -> None:
        report = self._report(self._entries(99), {99: "UNKNOWN"}, strict=True, query_failures=1)
        self.assertEqual(report["status"], "failure")

    def test_report_contains_required_fields(self) -> None:
        report = self._report(self._entries(25), {25: "OPEN"})
        for field in (
            "uplift_repo", "backlog_path", "strict_mode", "tracked_total",
            "open_count", "closed_count", "unknown_count", "aligned_closed_count",
            "action_required_count", "action_required_issues", "query_failures",
            "timestamp_utc", "issues", "status",
        ):
            self.assertIn(field, report, f"missing field: {field}")


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class MainIntegrationTests(unittest.TestCase):

    def _make_backlog(self, tmpdir: str, content: str) -> None:
        (Path(tmpdir) / "AGENTS.backlog.md").write_text(content, encoding="utf-8")

    def test_missing_uplift_repo_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            import io
            captured = io.StringIO()
            with mock.patch("sys.stderr", captured), \
                    mock.patch("sys.argv", ["uplift_status.py", "--uplift-repo", ""]):
                result = _m.main(repo_root=Path(tmpdir))
            self.assertNotEqual(result, 0)

    def test_zero_tracked_exits_zero_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._make_backlog(tmpdir, "- [ ] No issue links here.\n")
            with mock.patch("sys.argv", [
                "uplift_status.py",
                "--uplift-repo", "org/repo",
                "--output-path", "artifacts/blueprint/uplift_status.json",
            ]):
                result = _m.main(repo_root=root)
            self.assertEqual(result, 0)
            artifact = root / "artifacts/blueprint/uplift_status.json"
            self.assertTrue(artifact.is_file())
            data = json.loads(artifact.read_text())
            self.assertEqual(data["tracked_total"], 0)
            self.assertEqual(data["status"], "success")

    def test_closed_issue_action_required_exits_zero_without_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._make_backlog(tmpdir, (
                "  - [ ] [#5](https://github.com/org/repo/issues/5) pending item.\n"
            ))
            with mock.patch("sys.argv", [
                "uplift_status.py",
                "--uplift-repo", "org/repo",
                "--output-path", "artifacts/blueprint/uplift_status.json",
            ]):
                result = _m.main(
                    repo_root=root,
                    _issue_states_override={5: "CLOSED"},
                )
            self.assertEqual(result, 0)
            data = json.loads((root / "artifacts/blueprint/uplift_status.json").read_text())
            self.assertEqual(data["action_required_count"], 1)

    def test_strict_mode_exits_nonzero_when_action_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._make_backlog(tmpdir, (
                "  - [ ] [#5](https://github.com/org/repo/issues/5) pending item.\n"
            ))
            with mock.patch("sys.argv", [
                "uplift_status.py",
                "--uplift-repo", "org/repo",
                "--output-path", "artifacts/blueprint/uplift_status.json",
                "--strict",
            ]):
                result = _m.main(
                    repo_root=root,
                    _issue_states_override={5: "CLOSED"},
                )
            self.assertNotEqual(result, 0)

    def test_all_open_exits_zero_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._make_backlog(tmpdir, (
                "  - [ ] [#7](https://github.com/org/repo/issues/7) still open.\n"
            ))
            with mock.patch("sys.argv", [
                "uplift_status.py",
                "--uplift-repo", "org/repo",
                "--output-path", "artifacts/blueprint/uplift_status.json",
                "--strict",
            ]):
                result = _m.main(
                    repo_root=root,
                    _issue_states_override={7: "OPEN"},
                )
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
