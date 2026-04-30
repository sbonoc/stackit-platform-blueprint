#!/usr/bin/env python3
"""Validate the Accessibility Conformance Report (ACR) exists, is dated, and is within staleness window.

Exits non-zero with a diagnostic message when:
  - docs/platform/accessibility/acr.md does not exist
  - The "Report date (last reviewed):" field is missing or still a placeholder
  - The date is older than ACR_STALENESS_DAYS (env var) or blueprint/contract.yaml
    spec.quality.accessibility.acr_staleness_days (default: 90)

Usage:
    make quality-a11y-acr-check
    ACR_STALENESS_DAYS=180 python3 scripts/bin/platform/quality/check_acr_freshness.py
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
PREFIX = "[quality-a11y-acr-check]"
ACR_PATH = REPO_ROOT / "docs" / "platform" / "accessibility" / "acr.md"
CONTRACT_PATH = REPO_ROOT / "blueprint" / "contract.yaml"

_DATE_FIELD_RE = re.compile(
    r"^\s*[-*]?\s*\*{0,2}Report date \(last reviewed\):\*{0,2}\s*(.+)$",
    re.IGNORECASE,
)
_PLACEHOLDER_RE = re.compile(
    r"^\s*$|placeholder|yyyy-mm-dd|<date>|TBD|TBC|\?",
    re.IGNORECASE,
)
_DATE_FORMATS = ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%d/%m/%Y")


def _load_staleness_days() -> int:
    env_val = os.environ.get("ACR_STALENESS_DAYS", "").strip()
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            pass

    try:
        with CONTRACT_PATH.open(encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
        days = (
            contract.get("spec", {})
            .get("quality", {})
            .get("accessibility", {})
            .get("acr_staleness_days")
        )
        if isinstance(days, int):
            return days
    except Exception:
        pass

    return 90


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def main() -> None:
    staleness_days = _load_staleness_days()

    if not ACR_PATH.exists():
        print(
            f"{PREFIX} FAIL — {ACR_PATH.relative_to(REPO_ROOT)} does not exist.\n"
            f"  Remediation: run `make blueprint-upgrade-consumer` to seed the ACR scaffold,\n"
            f"  then fill in the product information and set the Report date.",
            file=sys.stderr,
        )
        sys.exit(1)

    content = ACR_PATH.read_text(encoding="utf-8")
    report_date_raw: str | None = None

    for line in content.splitlines():
        m = _DATE_FIELD_RE.match(line)
        if m:
            report_date_raw = m.group(1).strip()
            break

    if report_date_raw is None:
        print(
            f"{PREFIX} FAIL — `Report date (last reviewed):` field not found in {ACR_PATH.relative_to(REPO_ROOT)}.\n"
            f"  Remediation: add `- **Report date (last reviewed):** YYYY-MM-DD` to the Product Information section.",
            file=sys.stderr,
        )
        sys.exit(1)

    if _PLACEHOLDER_RE.search(report_date_raw):
        print(
            f"{PREFIX} FAIL — `Report date (last reviewed):` is a placeholder ({report_date_raw!r}).\n"
            f"  Remediation: replace with the actual review date in YYYY-MM-DD format.",
            file=sys.stderr,
        )
        sys.exit(1)

    report_date = _parse_date(report_date_raw)
    if report_date is None:
        print(
            f"{PREFIX} FAIL — `Report date (last reviewed):` value {report_date_raw!r} is not a recognisable date.\n"
            f"  Remediation: use YYYY-MM-DD format (e.g. 2026-04-30).",
            file=sys.stderr,
        )
        sys.exit(1)

    today = date.today()
    days_elapsed = (today - report_date).days

    if days_elapsed > staleness_days:
        print(
            f"{PREFIX} FAIL — ACR is stale: last reviewed {days_elapsed} day(s) ago "
            f"({report_date}), configured window is {staleness_days} day(s).\n"
            f"  File: {ACR_PATH.relative_to(REPO_ROOT)}\n"
            f"  Remediation: review and update the ACR, then set `Report date (last reviewed):` to today ({today}).\n"
            f"  Override window: ACR_STALENESS_DAYS env var or blueprint/contract.yaml spec.quality.accessibility.acr_staleness_days.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"{PREFIX} OK — ACR reviewed {days_elapsed} day(s) ago ({report_date}); "
        f"within {staleness_days}-day window."
    )


if __name__ == "__main__":
    main()
