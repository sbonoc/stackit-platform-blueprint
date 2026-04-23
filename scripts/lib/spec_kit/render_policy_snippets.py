#!/usr/bin/env python3
"""Render/check generated SDD policy snippets in AGENTS and docs from contract fields."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402

BEGIN = "<!-- BEGIN GENERATED:SDD_POLICY_SNAPSHOT -->"
END = "<!-- END GENERATED:SDD_POLICY_SNAPSHOT -->"
TARGETS = (
    Path("AGENTS.md"),
    Path("scripts/templates/consumer/init/AGENTS.md.tmpl"),
    Path("docs/blueprint/governance/spec_driven_development.md"),
)


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _build_snapshot(contract_raw: dict[str, Any]) -> str:
    spec_raw = _as_mapping(contract_raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    lifecycle_raw = _as_mapping(sdd_raw.get("lifecycle"))
    readiness_raw = _as_mapping(sdd_raw.get("readiness_gate"))
    normative_raw = _as_mapping(sdd_raw.get("normative_language"))

    phases = _as_list_of_str(lifecycle_raw.get("phases"))
    required_zero_fields = _as_list_of_str(readiness_raw.get("required_zero_fields"))
    required_signoffs = _as_list_of_str(readiness_raw.get("required_signoffs"))
    allowed_keywords = _as_list_of_str(normative_raw.get("allowed_keywords"))
    forbidden_terms = _as_list_of_str(normative_raw.get("forbidden_ambiguous_terms_in_normative_sections"))

    status_field = str(readiness_raw.get("status_field", "SPEC_READY")).strip()
    required_value = str(readiness_raw.get("required_value", "true")).strip()
    blocked_marker = str(readiness_raw.get("blocked_marker", "BLOCKED_MISSING_INPUTS")).strip()
    intake_status_field = str(readiness_raw.get("intake_status_field", "SPEC_PRODUCT_READY")).strip()
    intake_required_signoffs = _as_list_of_str(readiness_raw.get("intake_required_signoffs"))

    lines: list[str] = []
    lines.append("- Lifecycle order (contract): " + " -> ".join(phases))
    lines.append(f"- Readiness gate: `{status_field}={required_value}`")
    lines.append(f"- Intake gate: `{intake_status_field}=true`")
    lines.append(f"- Missing-input blocker token: `{blocked_marker}`")
    lines.append("- Required zero-count fields: " + ", ".join(f"`{field}`" for field in required_zero_fields))
    lines.append("- Required sign-offs: " + ", ".join(f"`{field}`" for field in required_signoffs))
    lines.append("- Intake required sign-offs: " + ", ".join(f"`{field}`" for field in intake_required_signoffs))
    lines.append("- Allowed normative keywords: " + ", ".join(f"`{term}`" for term in allowed_keywords))
    lines.append("- Forbidden ambiguous terms: " + ", ".join(f"`{term}`" for term in forbidden_terms))
    return "\n".join(lines)


def _replace_between_markers(content: str, rendered: str, target: Path) -> str:
    if BEGIN not in content or END not in content:
        raise ValueError(f"missing policy snippet markers in {target}")

    before, rest = content.split(BEGIN, 1)
    _, after = rest.split(END, 1)
    block = f"{BEGIN}\n{rendered}\n{END}"
    return before + block + after


def _sync(repo_root: Path, check: bool) -> int:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    rendered = _build_snapshot(contract.raw)
    exit_code = 0

    for relative in TARGETS:
        path = repo_root / relative
        if not path.is_file():
            raise ValueError(f"missing target file for policy snippet rendering: {relative}")

        content = path.read_text(encoding="utf-8", errors="surrogateescape")
        updated = _replace_between_markers(content, rendered, relative)

        if updated == content:
            print(f"policy snippet already up to date: {relative.as_posix()}")
            continue

        if check:
            print(f"policy snippet drift detected: {relative.as_posix()}", file=sys.stderr)
            exit_code = 1
            continue

        path.write_text(updated, encoding="utf-8")
        print(f"updated policy snippet: {relative.as_posix()}")

    if check and exit_code:
        print("Run: python3 scripts/lib/spec_kit/render_policy_snippets.py", file=sys.stderr)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    return _sync(repo_root=repo_root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
