#!/usr/bin/env python3
"""Regenerate WCAG 2.1 criterion rows in acr.md from a bundled W3C list.

Preserves existing Support / Notes / Evidence cell content for each criterion.
Adds any missing criteria rows from the bundled list. Rows whose SC value no
longer appears in the bundled list are left unchanged (avoid silent deletion of
consumer-authored content).

Usage:
    make quality-a11y-acr-sync
    python3 scripts/bin/platform/quality/sync_acr_criteria.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PREFIX = "[quality-a11y-acr-sync]"
ACR_PATH = REPO_ROOT / "docs" / "platform" / "accessibility" / "acr.md"

# Bundled WCAG 2.1 A+AA criteria (SC, Name, Level).
# Source: https://www.w3.org/TR/WCAG21/
_WCAG21_CRITERIA: list[tuple[str, str, str]] = [
    # Level A
    ("1.1.1", "Non-text Content", "A"),
    ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A"),
    ("1.2.2", "Captions (Prerecorded)", "A"),
    ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A"),
    ("1.3.1", "Info and Relationships", "A"),
    ("1.3.2", "Meaningful Sequence", "A"),
    ("1.3.3", "Sensory Characteristics", "A"),
    ("1.4.1", "Use of Color", "A"),
    ("1.4.2", "Audio Control", "A"),
    ("2.1.1", "Keyboard", "A"),
    ("2.1.2", "No Keyboard Trap", "A"),
    ("2.1.4", "Character Key Shortcuts", "A"),
    ("2.2.1", "Timing Adjustable", "A"),
    ("2.2.2", "Pause, Stop, Hide", "A"),
    ("2.3.1", "Three Flashes or Below Threshold", "A"),
    ("2.4.1", "Bypass Blocks", "A"),
    ("2.4.2", "Page Titled", "A"),
    ("2.4.3", "Focus Order", "A"),
    ("2.4.4", "Link Purpose (In Context)", "A"),
    ("2.5.1", "Pointer Gestures", "A"),
    ("2.5.2", "Pointer Cancellation", "A"),
    ("2.5.3", "Label in Name", "A"),
    ("2.5.4", "Motion Actuation", "A"),
    ("3.1.1", "Language of Page", "A"),
    ("3.2.1", "On Focus", "A"),
    ("3.2.2", "On Input", "A"),
    ("3.3.1", "Error Identification", "A"),
    ("3.3.2", "Labels or Instructions", "A"),
    ("4.1.1", "Parsing", "A"),
    ("4.1.2", "Name, Role, Value", "A"),
    # Level AA
    ("1.2.4", "Captions (Live)", "AA"),
    ("1.2.5", "Audio Description (Prerecorded)", "AA"),
    ("1.3.4", "Orientation", "AA"),
    ("1.3.5", "Identify Input Purpose", "AA"),
    ("1.4.3", "Contrast (Minimum)", "AA"),
    ("1.4.4", "Resize Text", "AA"),
    ("1.4.5", "Images of Text", "AA"),
    ("1.4.10", "Reflow", "AA"),
    ("1.4.11", "Non-text Contrast", "AA"),
    ("1.4.12", "Text Spacing", "AA"),
    ("1.4.13", "Content on Hover or Focus", "AA"),
    ("2.4.5", "Multiple Ways", "AA"),
    ("2.4.6", "Headings and Labels", "AA"),
    ("2.4.7", "Focus Visible", "AA"),
    ("3.1.2", "Language of Parts", "AA"),
    ("3.2.3", "Consistent Navigation", "AA"),
    ("3.2.4", "Consistent Identification", "AA"),
    ("3.3.3", "Error Suggestion", "AA"),
    ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA"),
    ("4.1.3", "Status Messages", "AA"),
]

_TABLE_ROW_RE = re.compile(
    r"^\|\s*([\d.]+)\s*\|\s*(.+?)\s*\|\s*(A{1,2})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$"
)


def _parse_existing_rows(content: str) -> dict[str, tuple[str, str, str]]:
    """Return {sc: (support, notes, evidence)} for each existing table row."""
    rows: dict[str, tuple[str, str, str]] = {}
    for line in content.splitlines():
        m = _TABLE_ROW_RE.match(line)
        if m:
            sc, _name, _level, support, notes, evidence = m.groups()
            rows[sc.strip()] = (support.strip(), notes.strip(), evidence.strip())
    return rows


def _render_row(sc: str, name: str, level: str, support: str, notes: str, evidence: str) -> str:
    return f"| {sc} | {name} | {level} | {support} | {notes} | {evidence} |"


def main() -> None:
    if not ACR_PATH.exists():
        print(
            f"{PREFIX} FAIL — {ACR_PATH.relative_to(REPO_ROOT)} does not exist; "
            f"run `make blueprint-upgrade-consumer` to seed the ACR scaffold first.",
            file=sys.stderr,
        )
        sys.exit(1)

    content = ACR_PATH.read_text(encoding="utf-8")
    existing = _parse_existing_rows(content)

    added = 0
    updated = 0

    new_rows_by_sc: dict[str, str] = {}
    for sc, name, level in _WCAG21_CRITERIA:
        if sc in existing:
            support, notes, evidence = existing[sc]
            new_rows_by_sc[sc] = _render_row(sc, name, level, support, notes, evidence)
        else:
            new_rows_by_sc[sc] = _render_row(sc, name, level, "Not Evaluated", "", "")
            added += 1

    def _replace_row(m: re.Match) -> str:
        sc = m.group(1).strip()
        if sc in new_rows_by_sc:
            replacement = new_rows_by_sc[sc]
            if replacement != m.group(0):
                nonlocal updated
                updated += 1
            return replacement
        return m.group(0)

    new_content = _TABLE_ROW_RE.sub(_replace_row, content)

    if added > 0:
        new_rows_to_insert = [
            new_rows_by_sc[sc]
            for sc, _, _ in _WCAG21_CRITERIA
            if sc not in existing
        ]
        lines = new_content.splitlines(keepends=True)
        last_table_idx = -1
        for i, line in enumerate(lines):
            if _TABLE_ROW_RE.match(line.rstrip("\n")):
                last_table_idx = i
        insert_block = "\n".join(new_rows_to_insert) + "\n"
        if last_table_idx >= 0:
            lines.insert(last_table_idx + 1, insert_block)
        else:
            lines.append(insert_block)
        new_content = "".join(lines)

    if new_content == content and added == 0:
        print(f"{PREFIX} OK — ACR criterion rows are up to date; no changes made.")
        return

    ACR_PATH.write_text(new_content, encoding="utf-8")
    print(
        f"{PREFIX} OK — ACR synced: {updated} row(s) updated, {added} row(s) added. "
        f"File: {ACR_PATH.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
