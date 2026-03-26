#!/usr/bin/env python3
"""Generate release notes for blueprint template releases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_scalar(lines: list[str], key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return ""


def _extract_section(lines: list[str], marker: str) -> list[str]:
    start = -1
    marker_indent = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"{marker}:":
            start = idx
            marker_indent = len(line) - len(line.lstrip(" "))
            break
    if start == -1:
        return []

    section: list[str] = []
    for line in lines[start + 1 :]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= marker_indent:
            break
        section.append(line)
    return section


def _extract_backlog_items(backlog_content: str, section_title: str) -> list[str]:
    lines = backlog_content.splitlines()
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == section_title:
            start = idx
            break
    if start == -1:
        return []

    items: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- [ ] "):
            items.append(stripped.removeprefix("- [ ] ").strip())
    return items


def _extract_latest_decisions(decisions_content: str) -> list[str]:
    lines = decisions_content.splitlines()
    start = -1
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            start = idx
            break
    if start == -1:
        return []

    items: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            items.append(stripped.removeprefix("- ").strip())
    return items


def render_release_notes(
    tag: str,
    contract_name: str,
    contract_version: str,
    template_version: str,
    minimum_supported_upgrade_from: str,
    upgrade_command: str,
    decisions: list[str],
    p0_items: list[str],
    p1_items: list[str],
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    title = tag or f"v{template_version}"
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- Generated at: `{timestamp}`")
    lines.append(f"- Contract: `{contract_name}` (`{contract_version}`)")
    lines.append(f"- Template version: `{template_version}`")
    lines.append("")
    lines.append("## Compatibility")
    lines.append(f"- Minimum supported upgrade source: `{minimum_supported_upgrade_from}`")
    lines.append(f"- Upgrade command: `{upgrade_command}`")
    lines.append("")
    lines.append("## Highlights")
    if decisions:
        for item in decisions:
            lines.append(f"- {item}")
    else:
        lines.append("- Governance and contract updates captured in `AGENTS.decisions.md`.")
    lines.append("")
    lines.append("## Remaining P0 Items")
    if p0_items:
        for item in p0_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Remaining P1 Items")
    if p1_items:
        for item in p1_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, help="Path to blueprint contract YAML.")
    parser.add_argument("--decisions", required=True, help="Path to AGENTS.decisions.md.")
    parser.add_argument("--backlog", required=True, help="Path to AGENTS.backlog.md.")
    parser.add_argument("--output", required=True, help="Output path for generated release notes.")
    parser.add_argument("--tag", default="", help="Release tag (optional).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract_path = Path(args.contract).resolve()
    decisions_path = Path(args.decisions).resolve()
    backlog_path = Path(args.backlog).resolve()
    output_path = Path(args.output).resolve()

    contract_lines = _read(contract_path).splitlines()
    contract_name = _extract_scalar(contract_lines, "name")
    contract_version = _extract_scalar(contract_lines, "version")
    template_bootstrap_section = _extract_section(_extract_section(contract_lines, "repository"), "template_bootstrap")
    template_version = _extract_scalar(template_bootstrap_section, "template_version")
    min_upgrade = _extract_scalar(template_bootstrap_section, "minimum_supported_upgrade_from")
    upgrade_command = _extract_scalar(template_bootstrap_section, "upgrade_command")

    decisions_items = _extract_latest_decisions(_read(decisions_path))
    backlog_content = _read(backlog_path)
    p0_items = _extract_backlog_items(backlog_content, "## P0 - v1.0 Template GA")
    p1_items = _extract_backlog_items(backlog_content, "## P1 - v1.1 Upgradeability")

    notes = render_release_notes(
        tag=args.tag,
        contract_name=contract_name,
        contract_version=contract_version,
        template_version=template_version,
        minimum_supported_upgrade_from=min_upgrade,
        upgrade_command=upgrade_command,
        decisions=decisions_items,
        p0_items=p0_items,
        p1_items=p1_items,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(notes, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
