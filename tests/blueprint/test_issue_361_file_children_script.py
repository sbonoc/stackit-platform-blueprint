"""Idempotency + body-shape tests for the #361 parent helper scripts.

Covers AC-010 (file_children.sh), AC-011 (add_deferred_triggers.sh), and
AC-013 (no auto-close keyword targeting parent #361 in any generated body)
per the parent spec at specs/2026-06-18-issue-361-orchestrator-service/.

The gh CLI is stubbed via PATH injection: a generated shell stub records each
invocation to a log file the test inspects. The AGENTS.backlog.md target is
redirected via the BACKLOG_FILE environment variable that the script reads.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import unittest

from tests._shared.helpers import REPO_ROOT


# AC-013 — case-insensitive auto-close keyword regex targeting parent #361.
# Matches any of: Close, Closes, Closed, Fix, Fixes, Fixed, Resolve, Resolves,
# Resolved, immediately followed by `#361` with a trailing word boundary.
#
# Word-boundary scope (per Claude review on PR #372): `\b` after `1` followed
# by `.` IS still a word boundary (`.` is non-word), so the regex matches
# `Closes #361.5` as well as `Closes #361`. This is the desired (strict)
# behavior — GitHub's own autolinker also resolves `#361.5` as a link to
# issue #361, so any form `<keyword> #361.<N>` would also auto-close `#361`
# at merge time. The earlier version of this comment incorrectly claimed
# GitHub treats `#361.N` as plain text; it does not — fixing the comment to
# reflect the regex's actual (and intentionally strict) coverage.
#
# No body in this PR's scope pairs an auto-close keyword with any `#361.N`
# form today; the strict regex guards future drift in either direction.
PARENT_AUTOCLOSE_REGEX = re.compile(
    r"\b(close[ds]?|fix(?:e[ds])?|resolve[ds]?)\s+#361\b",
    re.IGNORECASE,
)


SPEC_DIR = REPO_ROOT / "specs" / "2026-06-18-issue-361-orchestrator-service"
FILE_CHILDREN_SCRIPT = SPEC_DIR / "file_children.sh"
ADD_TRIGGERS_SCRIPT = SPEC_DIR / "add_deferred_triggers.sh"


GH_STUB_TEMPLATE = r"""#!/usr/bin/env bash
# Recording stub for gh used by tests. Logs every invocation, then implements
# the minimal command surface the scripts under test require.
set -euo pipefail

LOG_FILE="${GH_STUB_LOG:?GH_STUB_LOG must be set}"
EXISTING_TITLES_FILE="${GH_STUB_EXISTING_TITLES:-/dev/null}"
GH_STUB_LIST_FAIL="${GH_STUB_LIST_FAIL:-0}"

# Record the invocation, one line per arg (newline-quoted so multi-line bodies
# preserve their newlines as \n literals).
{
  printf 'INVOCATION\n'
  for arg in "$@"; do
    printf 'ARG\t%s\n' "${arg//$'\n'/\\n}"
  done
  printf 'END\n'
} >> "$LOG_FILE"

case "${1:-}" in
  auth)
    # auth status — succeed (the script only checks exit code).
    exit 0
    ;;
  issue)
    case "${2:-}" in
      list)
        # Fault injection: when GH_STUB_LIST_FAIL=1 the stub simulates a real
        # gh-list failure (e.g., stale auth, network down). The hardened
        # script MUST detect this and abort rather than treat as "issue absent".
        if [[ "$GH_STUB_LIST_FAIL" = "1" ]]; then
          printf 'gh stub: simulated list failure\n' >&2
          exit 1
        fi
        # Emit every line from the existing-titles file (one title per line).
        # The script filters via `grep -Fxq` against the title it expects.
        cat "$EXISTING_TITLES_FILE"
        exit 0
        ;;
      create)
        # Print a fake URL so callers that capture stdout do not error.
        printf 'https://github.com/example/repo/issues/%d\n' "$RANDOM"
        exit 0
        ;;
    esac
    ;;
esac

printf 'gh stub: unhandled command: %s\n' "$*" >&2
exit 64
"""


def _write_gh_stub(tmpdir: Path, log_path: Path, existing_titles_path: Path) -> Path:
    bin_dir = tmpdir / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(GH_STUB_TEMPLATE)
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # The script will only ever look for `gh` on PATH; we also expose GH_BIN for
    # explicit override paths.
    return gh_path


def _parse_invocations(log_path: Path) -> list[list[str]]:
    """Split the recorded log into one list-of-args per invocation."""
    invocations: list[list[str]] = []
    current: list[str] | None = None
    if not log_path.exists():
        return invocations
    for line in log_path.read_text().splitlines():
        if line == "INVOCATION":
            current = []
        elif line == "END":
            if current is not None:
                invocations.append(current)
                current = None
        elif line.startswith("ARG\t") and current is not None:
            current.append(line[len("ARG\t"):].replace("\\n", "\n"))
    return invocations


def _create_invocations(invocations: list[list[str]]) -> list[list[str]]:
    return [args for args in invocations if len(args) >= 2 and args[0] == "issue" and args[1] == "create"]


def _arg_value(args: list[str], flag: str) -> str | None:
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            return args[i + 1]
    return None


def _run_file_children(
    tmpdir: Path,
    log_path: Path,
    existing_titles_path: Path,
    *,
    list_fail: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GH_STUB_LOG"] = str(log_path)
    env["GH_STUB_EXISTING_TITLES"] = str(existing_titles_path)
    env["GH_STUB_LIST_FAIL"] = "1" if list_fail else "0"
    env["PATH"] = f"{tmpdir / 'bin'}:{env.get('PATH', '')}"
    env["GH_BIN"] = str(tmpdir / "bin" / "gh")
    # Skip the repo-identity check (tmpdir is not a clone of the real repo;
    # the stub gh would still answer, but we want to assert the issue-create
    # logic in isolation).
    env["PRECHECK_SKIP_REPO"] = "1"
    return subprocess.run(
        ["bash", str(FILE_CHILDREN_SCRIPT)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _run_add_triggers(backlog_file: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BACKLOG_FILE"] = str(backlog_file)
    return subprocess.run(
        ["bash", str(ADD_TRIGGERS_SCRIPT)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


class FileChildrenScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(self.enterContext(_tmp_dir()))
        self.log_path = self.tmpdir / "gh_log.txt"
        self.existing_titles_path = self.tmpdir / "existing_titles.txt"
        self.existing_titles_path.write_text("")  # no pre-existing issues
        _write_gh_stub(self.tmpdir, self.log_path, self.existing_titles_path)

    def test_file_children_first_run(self) -> None:
        result = _run_file_children(self.tmpdir, self.log_path, self.existing_titles_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        invocations = _parse_invocations(self.log_path)
        create_calls = _create_invocations(invocations)

        # AC-010 (a) — exactly 4 issue-create calls
        self.assertEqual(
            len(create_calls), 4,
            msg=f"expected 4 issue-create calls, got {len(create_calls)}: {create_calls}",
        )

        # AC-010 (a) cont. — one call per child slug in {1,2,4,5}, none for 3
        titles = [_arg_value(args, "--title") for args in create_calls]
        expected_slugs = {"1", "2", "4", "5"}
        found_slugs = set()
        for title in titles:
            self.assertIsNotNone(title, msg=f"create call missing --title: {create_calls}")
            for slug in expected_slugs:
                if f"(Child {slug} of #361)" in title:
                    found_slugs.add(slug)
        self.assertEqual(found_slugs, expected_slugs)
        for title in titles:
            self.assertNotIn(
                "(Child 3 of #361)", title,
                msg="AC-010 (a): #361.3 MUST NOT be filed by file_children.sh",
            )

        # AC-010 (b) — body cites parent spec path + boundary type + FR range
        # + Activation section (Codex P1 PR #372: blocked-vs-unblocked rule must
        # be explicit on every child body so the operator knows whether the
        # agent-ready label is present).
        for args in create_calls:
            body = _arg_value(args, "--body") or ""
            title = _arg_value(args, "--title") or ""
            self.assertIn(
                "specs/2026-06-18-issue-361-orchestrator-service/", body,
                msg="body must cite parent spec path",
            )
            self.assertIn("**Boundary type:**", body, msg="body must label boundary type")
            # Codex P2 PR #372 3rd-review + PR #372 strategic-alignment audit
            # 2026-06-19: boundary type MUST be canonical per
            # ADR-issue-337-light-decomposition-policy "Allowed boundary types"
            # (EXACTLY ONE OF bounded-context / architectural-layer /
            # user-visible-feature-behavior). Per the strategic-audit
            # re-classification, the parent decomposes along TWO axes via
            # ADR-issue-337's multi-axis exception for manually-authored
            # parent coordination specs: #361.1/.2/.3/.4 = architectural-layer
            # (runtime); #361.5 = bounded-context (governance/expert-panel).
            if "(Child 5 of #361)" in title:
                self.assertIn(
                    "`bounded-context`", body,
                    msg=f"body {title!r} must use canonical boundary type `bounded-context`",
                )
            else:
                self.assertIn(
                    "`architectural-layer`", body,
                    msg=f"body {title!r} must use canonical boundary type `architectural-layer`",
                )
            self.assertIn(
                "**Boundary value:**", body,
                msg=f"body {title!r} must declare a Boundary value per ADR policy",
            )
            self.assertIn("**FR range owned:**", body, msg="body must cite FR range")
            self.assertIn(
                "## Activation", body,
                msg=f"body {title!r} must carry an ## Activation section",
            )

        # AC-010 (c) — per-child label policy (amended per Codex P1 review of
        # PR #372): #361.1 is unblocked and gets `agent-ready` at filing;
        # #361.2/#361.4/#361.5 declare blockers and do NOT get `agent-ready`
        # at filing (a human applies it manually once each blocker chain
        # clears, per ADR-issue-337-trigger-authorization-model).
        common_labels = sorted(["enhancement", "infrastructure", "priority:p1"])
        unblocked_labels = sorted([*common_labels, "agent-ready"])
        for args in create_calls:
            title = _arg_value(args, "--title") or ""
            labels = sorted((_arg_value(args, "--label") or "").split(","))
            if "(Child 1 of #361)" in title:
                self.assertEqual(
                    labels, unblocked_labels,
                    msg=f"#361.1 (unblocked) MUST carry agent-ready at filing; got {labels}",
                )
            else:
                self.assertEqual(
                    labels, common_labels,
                    msg=f"blocked child {title!r} MUST NOT carry agent-ready at filing; got {labels}",
                )
                self.assertNotIn(
                    "agent-ready", labels,
                    msg=f"blocked child {title!r} MUST NOT carry agent-ready (Codex P1 PR #372)",
                )

    def test_no_child_body_auto_closes_parent(self) -> None:
        # AC-013 / FR-017 — every generated child body MUST cite parent #361 as
        # `Tracks #361` (informational only) and MUST NOT use any GitHub auto-
        # close keyword targeting #361. `#361.5` legitimately uses
        # `Closes #369` (a different issue) — that does not match the regex.
        result = _run_file_children(self.tmpdir, self.log_path, self.existing_titles_path)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        create_calls = _create_invocations(_parse_invocations(self.log_path))
        self.assertEqual(len(create_calls), 4)
        for args in create_calls:
            body = _arg_value(args, "--body") or ""
            title = _arg_value(args, "--title") or ""
            self.assertIn(
                "Tracks #361", body,
                msg=(
                    f"AC-013: child {title!r} body MUST cite parent #361 as "
                    f"`Tracks #361` (informational). Body: {body!r}"
                ),
            )
            match = PARENT_AUTOCLOSE_REGEX.search(body)
            self.assertIsNone(
                match,
                msg=(
                    f"AC-013: child {title!r} body MUST NOT use any GitHub "
                    f"auto-close keyword targeting parent #361. Matched: "
                    f"{match.group(0) if match else None!r}. Body: {body!r}"
                ),
            )

    def test_file_children_aborts_on_gh_list_failure(self) -> None:
        # Pre-signoff finding 3: a stale gh auth (gh-list returns non-zero)
        # MUST NOT be silently treated as "issue absent". The hardened script
        # exits 2 and creates zero issues.
        result = _run_file_children(
            self.tmpdir,
            self.log_path,
            self.existing_titles_path,
            list_fail=True,
        )
        self.assertEqual(
            result.returncode, 2,
            msg=f"hardened script MUST exit 2 on gh-list failure; got {result.returncode}. stderr: {result.stderr}",
        )
        # Zero issue-create calls — the failure mode that previously silently
        # filed duplicates.
        create_calls = _create_invocations(_parse_invocations(self.log_path))
        self.assertEqual(
            len(create_calls), 0,
            msg=f"gh-list failure MUST NOT produce any issue-create calls; got {len(create_calls)}: {create_calls}",
        )

    def test_file_children_idempotent_second_run(self) -> None:
        # First run as in test_file_children_first_run.
        first = _run_file_children(self.tmpdir, self.log_path, self.existing_titles_path)
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_create_count = len(_create_invocations(_parse_invocations(self.log_path)))
        self.assertEqual(first_create_count, 4)

        # Simulate the 4 issues now existing — populate the stub's title file.
        # Extract titles from the recorded create calls.
        first_titles = [
            _arg_value(args, "--title")
            for args in _create_invocations(_parse_invocations(self.log_path))
        ]
        self.existing_titles_path.write_text("\n".join(t for t in first_titles if t) + "\n")

        # Clear the log so the second run's invocations are isolated.
        self.log_path.write_text("")

        second = _run_file_children(self.tmpdir, self.log_path, self.existing_titles_path)
        # AC-010 (e) — exit code 0
        self.assertEqual(second.returncode, 0, msg=second.stderr)

        # AC-010 (d) — second run produces zero issue-create calls
        second_create_calls = _create_invocations(_parse_invocations(self.log_path))
        self.assertEqual(
            len(second_create_calls), 0,
            msg=f"idempotent re-run must create 0 issues, got {len(second_create_calls)}: {second_create_calls}",
        )


_BACKLOG_FIXTURE_WITH_EXISTING_336_SECTION = """\
# Blueprint Backlog

## Parked Proposals

### on-scope: infra

- [ ] (parked) proposal(some-other-ticket): an unrelated entry.
      trigger: on-scope: infra
      rationale: pre-existing entry the test should not touch.

### after: issue-336

- [ ] (parked) proposal(issue-337-factory-phase-0-foundations): pre-existing entry under after: issue-336.
      trigger: after: issue-336
      rationale: this entry MUST NOT be removed by the script; the new entry MUST be inserted under the same section.

---

## Long Horizon

- [ ] Some long-horizon item that the script MUST NOT disturb.
"""


def _section_index(content: str, header: str) -> int:
    """Return the line index of `header` in `content`, or -1 if absent."""
    for i, line in enumerate(content.splitlines()):
        if line == header:
            return i
    return -1


class AddDeferredTriggersScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(self.enterContext(_tmp_dir()))
        self.backlog = self.tmpdir / "AGENTS.backlog.md"
        # Seed with a realistic backlog file that has a pre-existing
        # `### after: issue-336` section (matching the real-repo state) AND
        # a `## Long Horizon` section that MUST be respected as the
        # boundary for new-section creation.
        self.backlog.write_text(_BACKLOG_FIXTURE_WITH_EXISTING_336_SECTION)

    def test_add_deferred_triggers_first_run(self) -> None:
        result = _run_add_triggers(self.backlog)
        # AC-011 (c) — exit code 0
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        content = self.backlog.read_text()
        # AC-011 (a) — two entries with the literal trigger strings, both
        # citing the parent spec path (>= 2 occurrences; each entry also
        # cites the git rm paths per FR-016 lifecycle binding).
        self.assertIn("trigger: after: issue-335", content)
        self.assertIn("trigger: after: issue-336", content)
        self.assertGreaterEqual(content.count("specs/2026-06-18-issue-361-orchestrator-service/"), 2)
        # FR-016 — both entries cite the git rm responsibility for #361.3.
        self.assertIn("git rm", content)
        self.assertIn("file_children.sh", content)
        self.assertIn("add_deferred_triggers.sh", content)

        # Section-placement: per FR-015 § injection convention, each new entry
        # MUST land under its `### after: issue-NNN` section header, NOT
        # appended at end of file or under `## Long Horizon`.
        idx_335_header = _section_index(content, "### after: issue-335")
        idx_336_header = _section_index(content, "### after: issue-336")
        idx_long_horizon = _section_index(content, "## Long Horizon")
        idx_335_entry = _section_index(
            content,
            "      trigger: after: issue-335",
        )
        idx_336_entry = _section_index(
            content,
            "      trigger: after: issue-336",
        )

        self.assertGreater(idx_335_header, -1, msg="`### after: issue-335` header MUST be created")
        self.assertGreater(idx_336_header, -1, msg="`### after: issue-336` header MUST be preserved")
        self.assertGreater(idx_long_horizon, -1, msg="`## Long Horizon` MUST be preserved")
        self.assertGreater(idx_335_entry, -1, msg="`trigger: after: issue-335` entry MUST exist")
        self.assertGreater(idx_336_entry, -1, msg="`trigger: after: issue-336` entry MUST exist")

        # Each entry MUST appear after its own section header AND before the
        # Long Horizon section.
        self.assertGreater(idx_335_entry, idx_335_header)
        self.assertGreater(idx_336_entry, idx_336_header)
        self.assertLess(idx_335_entry, idx_long_horizon)
        self.assertLess(idx_336_entry, idx_long_horizon)

        # Codex P2 re-review of PR #372: the newly-created `### after: issue-335`
        # section MUST land BEFORE the `---` separator that closes `## Parked
        # Proposals` — NOT in the gap between `---` and `## Long Horizon`
        # (which would be visually outside Parked Proposals and would defeat
        # the FR-015 convention that these trigger sections live under
        # `## Parked Proposals`).
        lines = content.splitlines()
        idx_parked_proposals = _section_index(content, "## Parked Proposals")
        # Find the FIRST `---` separator that follows `## Parked Proposals`
        # (the one that closes the block).
        idx_closing_separator = -1
        for i, line in enumerate(lines):
            if i > idx_parked_proposals and line == "---":
                idx_closing_separator = i
                break
        self.assertGreater(idx_parked_proposals, -1, msg="`## Parked Proposals` header MUST be preserved")
        self.assertGreater(
            idx_closing_separator, -1,
            msg="`---` closing separator of Parked Proposals MUST be preserved",
        )
        self.assertGreater(
            idx_335_header, idx_parked_proposals,
            msg="newly-created `### after: issue-335` MUST land AFTER `## Parked Proposals`",
        )
        self.assertLess(
            idx_335_header, idx_closing_separator,
            msg=(
                "Codex P2 PR #372: `### after: issue-335` MUST land BEFORE the "
                f"`---` closing separator (saw header at line {idx_335_header}, "
                f"separator at line {idx_closing_separator}). Otherwise the new "
                f"section is visually outside `## Parked Proposals`, defeating "
                f"FR-015 convention."
            ),
        )
        self.assertLess(
            idx_336_header, idx_closing_separator,
            msg="pre-existing `### after: issue-336` MUST stay inside Parked Proposals",
        )

        # The pre-existing `### after: issue-336` entry must survive (the
        # script appends, never replaces).
        self.assertIn(
            "proposal(issue-337-factory-phase-0-foundations): pre-existing entry under after: issue-336",
            content,
        )

    def test_no_deferred_trigger_rationale_auto_closes_parent(self) -> None:
        # AC-013 / FR-017 — the appended backlog text MUST embed the same
        # no-auto-close rule for the #361.3 PR the operator drafts later.
        result = _run_add_triggers(self.backlog)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        content = self.backlog.read_text()
        match = PARENT_AUTOCLOSE_REGEX.search(content)
        self.assertIsNone(
            match,
            msg=(
                f"AC-013: deferred-trigger rationale MUST NOT use any GitHub "
                f"auto-close keyword targeting parent #361. Matched: "
                f"{match.group(0) if match else None!r}."
            ),
        )
        # And it MUST positively instruct the operator to use `Tracks #361`.
        self.assertIn("Tracks #361", content)

    def test_add_deferred_triggers_idempotent_second_run(self) -> None:
        first = _run_add_triggers(self.backlog)
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        after_first = self.backlog.read_text()

        second = _run_add_triggers(self.backlog)
        # AC-011 (c) — exit code 0
        self.assertEqual(second.returncode, 0, msg=second.stderr)

        # AC-011 (b) — second run appends zero new entries
        after_second = self.backlog.read_text()
        self.assertEqual(after_first, after_second)


# Small helper to support `self.enterContext(_tmp_dir())` without unittest.TestCase.enterContext
# typing fuss on older interpreters.
from contextlib import contextmanager
import tempfile


@contextmanager
def _tmp_dir():
    d = tempfile.mkdtemp(prefix="issue361-")
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
