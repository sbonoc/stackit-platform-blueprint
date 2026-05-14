"""Consumer skill extension — automatic workaround-report issue filer.

FR-013, FR-014: After a consumer agent applies a manual fix to a blueprint-managed
file not covered by Stage 1c, this module files a structured workaround-report issue
in the blueprint repo. Filing is non-blocking (NFR-REL-003).
"""
from __future__ import annotations

import json
import logging
import subprocess
import textwrap
from typing import Any

log = logging.getLogger(__name__)

_STUB = "n/a — filed automatically by blueprint-consumer-upgrade skill"


def _build_body(
    *,
    affected_version: str,
    action_kind: str,
    applies_when: str,
    action_content: str,
) -> str:
    return textwrap.dedent(
        f"""\
        ### What happened?

        {_STUB}

        ### Reproduction

        {_STUB}

        ### Expected behavior

        {_STUB}

        ### Temporary workaround path (if any)

        {_STUB}

        ### Replacement trigger

        {_STUB}

        ### Workaround review date

        {_STUB}

        ## Automated Workaround Catalogue Entry

        Fill this section only when you have a concrete consumer-side fix to automate. Then add the `workaround-report` label to trigger the scaffolder.

        ### affected_version

        {affected_version}

        ### action_kind

        {action_kind}

        ### applies_when

        {applies_when}

        ### action_content

        {action_content}
        """
    )


class WorkaroundReportFiler:
    """File a workaround-report issue in the blueprint repo via gh CLI.

    FR-013: title format `[workaround] <description> (v<version>)`.
    FR-014: duplicate detection via gh issue list --search "[workaround]".
    NFR-REL-003: all gh failures are non-fatal; returns None on failure.
    """

    def __init__(self, blueprint_repo: str) -> None:
        self._blueprint_repo = blueprint_repo

    def _search_duplicate(
        self, description: str, affected_version: str
    ) -> str | None:
        """FR-014: search for existing open issue matching the title pattern."""
        version = affected_version.lstrip("v")
        expected_title = f"[workaround] {description} (v{version})"
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--repo",
                    self._blueprint_repo,
                    "--label",
                    "workaround-report",
                    "--state",
                    "open",
                    "--search",
                    "[workaround]",
                    "--json",
                    "title,url",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None
            issues: list[dict[str, Any]] = json.loads(result.stdout or "[]")
            for issue in issues:
                if issue.get("title", "") == expected_title:
                    return str(issue.get("url", ""))
        except Exception as exc:
            log.warning("duplicate search failed: %s", exc)
        return None

    def file(
        self,
        *,
        affected_version: str,
        description: str,
        action_kind: str,
        applies_when: str,
        action_content: str,
    ) -> str | None:
        """File a workaround-report issue. Returns the issue URL or None.

        Returns None without raising when: a duplicate is found, gh fails, or
        any exception occurs.
        """
        version = affected_version.lstrip("v")
        title = f"[workaround] {description} (v{version})"

        # FR-014: duplicate check
        existing_url = self._search_duplicate(description, affected_version)
        if existing_url is not None:
            log.info("[UPGRADE] workaround-report already filed: %s", existing_url)
            print(f"[UPGRADE] workaround-report already filed: {existing_url}")
            return None

        body = _build_body(
            affected_version=affected_version,
            action_kind=action_kind,
            applies_when=applies_when,
            action_content=action_content,
        )

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    self._blueprint_repo,
                    "--title",
                    title,
                    "--label",
                    "workaround-report",
                    "--body",
                    body,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                reason = result.stderr.strip() or "unknown error"
                log.warning(
                    "[UPGRADE] warning: failed to file workaround-report issue — %s", reason
                )
                print(
                    f"[UPGRADE] warning: failed to file workaround-report issue — {reason}"
                )
                return None
            url = result.stdout.strip()
            log.info("[UPGRADE] filed workaround-report issue: %s", url)
            print(f"[UPGRADE] filed workaround-report issue: {url}")
            return url
        except Exception as exc:
            log.warning(
                "[UPGRADE] warning: failed to file workaround-report issue — %s", exc
            )
            print(
                f"[UPGRADE] warning: failed to file workaround-report issue — {exc}"
            )
            return None


def file_workaround_report(
    *,
    blueprint_repo: str,
    affected_version: str,
    description: str,
    action_kind: str,
    applies_when: str,
    action_content: str,
) -> str | None:
    """Convenience wrapper. NFR-REL-003: always returns, never raises."""
    filer = WorkaroundReportFiler(blueprint_repo=blueprint_repo)
    return filer.file(
        affected_version=affected_version,
        description=description,
        action_kind=action_kind,
        applies_when=applies_when,
        action_content=action_content,
    )
