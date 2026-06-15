"""Cross-ticket amendment URLs are reachable (issue #364, FR-008 / AC-005).

`pr_context.md § Cross-Ticket Amendments` MUST list a comment URL per
ticket in CROSS_TICKET_AMENDMENT_TICKETS, and each URL MUST resolve to a
GitHub comment that the `gh` CLI can fetch (HTTP 200). This test reads
the table out of pr_context.md, extracts the URLs, and asserts each
exists via `gh api`.

Skips gracefully when the `gh` CLI is missing, unauthenticated, or
network-restricted (CI smoke runs without GitHub credentials) so the
local-only run is not penalized.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    CROSS_TICKET_AMENDMENT_TICKETS,
    REPO_ROOT,
)

PR_CONTEXT = (
    REPO_ROOT
    / "specs"
    / "2026-06-02-issue-364-factory-expert-persona-panel"
    / "pr_context.md"
)

_URL_PATTERN = re.compile(
    r"https://github\.com/[^/\s]+/[^/\s]+/(issues|pull)/(\d+)#issuecomment-(\d+)"
)


def _gh_available() -> bool:
    if shutil.which("gh") is None:
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _extract_amendment_section(body: str) -> str:
    start = body.find("## Cross-Ticket Amendments")
    assert start >= 0, "pr_context.md missing `## Cross-Ticket Amendments` section"
    end = body.find("\n## ", start + 1)
    return body[start:end] if end > 0 else body[start:]


def _ticket_url_map() -> dict[str, str]:
    body = PR_CONTEXT.read_text()
    section = _extract_amendment_section(body)
    mapping: dict[str, str] = {}
    for line in section.splitlines():
        if not line.startswith("|") or "#" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        ticket_cell = cells[0]
        url_match = _URL_PATTERN.search(line)
        if not url_match:
            continue
        ticket_num = re.search(r"#(\d+)", ticket_cell)
        if not ticket_num:
            continue
        mapping[f"#{ticket_num.group(1)}"] = url_match.group(0)
    return mapping


def test_pr_context_lists_an_amendment_url_for_every_required_ticket() -> None:
    mapping = _ticket_url_map()
    missing = [t for t in CROSS_TICKET_AMENDMENT_TICKETS if t not in mapping]
    assert not missing, (
        f"pr_context.md § Cross-Ticket Amendments is missing comment URLs "
        f"for ticket(s) {missing!r}; FR-008 / AC-005."
    )


@pytest.mark.parametrize("ticket", CROSS_TICKET_AMENDMENT_TICKETS)
def test_amendment_url_is_reachable_via_gh_api(ticket: str) -> None:
    if os.environ.get("BLUEPRINT_SKIP_NETWORK_TESTS") == "1":
        pytest.skip("network tests opted out via BLUEPRINT_SKIP_NETWORK_TESTS=1")
    if not _gh_available():
        pytest.skip("gh CLI unavailable or unauthenticated")

    mapping = _ticket_url_map()
    url = mapping.get(ticket)
    assert url, f"no URL recorded in pr_context.md for ticket {ticket}"

    match = _URL_PATTERN.search(url)
    assert match, f"recorded URL does not match the issuecomment pattern: {url}"

    owner_repo_match = re.search(r"github\.com/([^/]+)/([^/]+)/", url)
    assert owner_repo_match, f"could not parse owner/repo from {url}"
    owner, repo = owner_repo_match.group(1), owner_repo_match.group(2)
    comment_id = match.group(3)

    api_path = f"repos/{owner}/{repo}/issues/comments/{comment_id}"
    result = subprocess.run(
        ["gh", "api", api_path], capture_output=True, text=True, check=False, timeout=30
    )
    assert result.returncode == 0, (
        f"ticket {ticket} amendment URL did not resolve to a fetchable comment "
        f"({url}); `gh api {api_path}` exit={result.returncode}; "
        f"stderr={result.stderr.strip()!r}"
    )
