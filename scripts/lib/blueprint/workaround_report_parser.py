"""Parse the structured workaround section from a GitHub issue body.

FR-012: Locates the ## Automated Workaround Catalogue Entry heading, extracts
the four required fields, and returns a ParsedWorkaroundReport (or None when
the section is absent or all fields are blank).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

_SECTION_HEADING = "## Automated Workaround Catalogue Entry"
_FIELD_RE = re.compile(r"^###\s+(\S+.*?)\s*$", re.MULTILINE)
_VALID_ACTION_KINDS: frozenset[str] = frozenset({"contract_merge", "patch", "python_script"})
_BLANK_VALUES: frozenset[str] = frozenset({"_No response_", "", "none", "n/a"})
_EXTENSION_MAP: dict[str, str] = {
    "contract_merge": ".yaml",
    "patch": ".patch",
    "python_script": ".py",
}


def _slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:max_len].rstrip("_")


@dataclass(frozen=True)
class ParsedWorkaroundReport:
    issue_number: str
    issue_url: str
    issue_title: str
    affected_version: str
    action_kind: str
    applies_when: str
    action_content: str
    action_filename: str = field(init=False, compare=False)
    action_path: str = field(init=False, compare=False)

    def __post_init__(self) -> None:
        ext = _EXTENSION_MAP[self.action_kind]
        slug = _slugify(self.issue_title)
        filename = f"{self.issue_number}_{slug}{ext}"
        version = self.affected_version.lstrip("v") if self.affected_version else "unknown"
        version_dir = f"v{version}" if not self.affected_version.startswith("v") else self.affected_version
        object.__setattr__(self, "action_filename", filename)
        object.__setattr__(self, "action_path", f"workarounds/{version_dir}/{filename}")

    def manifest_entry_stub(self) -> dict:
        title = re.sub(r"^\[workaround\]\s*", "", self.issue_title, flags=re.IGNORECASE).strip()
        return {
            "id": self.issue_number,
            "upstream_issue": self.issue_url,
            "title": title,
            "applies_when": self.applies_when or "always",
            "action_kind": self.action_kind,
            "action_path": self.action_path,
            "apply_phase": "# <set to before_apply or after_apply>",
            "landed_in": None,
        }


def _extract_section_fields(section_text: str) -> dict[str, str]:
    """Extract ### field_name / value pairs from the workaround section body."""
    fields: dict[str, str] = {}
    matches = list(_FIELD_RE.finditer(section_text))
    for i, match in enumerate(matches):
        field_name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        value = section_text[start:end].strip()
        fields[field_name] = value
    return fields


def _is_blank(value: str) -> bool:
    return not value or value.strip() in _BLANK_VALUES


def parse_issue_body(
    *,
    body: str,
    issue_number: str | int,
    issue_url: str,
    issue_title: str,
) -> ParsedWorkaroundReport | None:
    """Parse workaround fields from a GitHub issue body.

    Returns None when the ## Automated Workaround Catalogue Entry section is
    absent or all four fields are blank. Raises ValueError for unknown action_kind.
    """
    idx = body.find(_SECTION_HEADING)
    if idx == -1:
        return None

    section_text = body[idx + len(_SECTION_HEADING):]
    fields = _extract_section_fields(section_text)

    affected_version = fields.get("affected_version", "").strip()
    action_kind = fields.get("action_kind", "").strip()
    applies_when_raw = fields.get("applies_when", "").strip()
    action_content = fields.get("action_content", "").strip()

    if all(_is_blank(v) for v in (affected_version, action_kind, applies_when_raw, action_content)):
        return None

    if _is_blank(affected_version):
        raise ValueError(
            "affected_version is required to construct action_path but was blank. "
            "Fill in the affected_version field (e.g. 'v1.10.0') and resubmit."
        )

    if action_kind not in _VALID_ACTION_KINDS:
        raise ValueError(
            f"Unknown action_kind {action_kind!r}. "
            f"Must be one of: {', '.join(sorted(_VALID_ACTION_KINDS))}."
        )

    applies_when = applies_when_raw if not _is_blank(applies_when_raw) else "always"

    return ParsedWorkaroundReport(
        issue_number=str(issue_number),
        issue_url=issue_url,
        issue_title=issue_title,
        affected_version=affected_version,
        action_kind=action_kind,
        applies_when=applies_when,
        action_content=action_content,
    )
