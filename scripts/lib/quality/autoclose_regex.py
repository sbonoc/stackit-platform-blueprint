"""Canonical GitHub auto-close keyword regex for must-not-auto-close checks.

REQ-003: defined once here; all consumers import from this module.
"""

from __future__ import annotations

import re

# Matches GitHub's auto-close keyword set followed by a specific issue number.
# Keyword forms: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved.
# Optional colon separator. Case-insensitive. Word boundary after issue number.
_AUTOCLOSE_PATTERN = r"\b(close[ds]?|fix(?:e[ds])?|resolve[ds]?):?\s+#{issue}\b"


def build_pattern(issue_number: int) -> re.Pattern[str]:
    """Return a compiled regex matching auto-close keywords targeting *issue_number*."""
    return re.compile(
        _AUTOCLOSE_PATTERN.format(issue=issue_number),
        re.IGNORECASE,
    )
