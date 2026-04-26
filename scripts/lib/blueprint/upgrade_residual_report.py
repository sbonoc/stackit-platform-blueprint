"""Stage 10: Residual report generator for the scripted upgrade pipeline.

Always emitted — even on partial failure — via the pipeline's EXIT trap.
Aggregates JSON artifacts from Stages 3, 5, 7, 9 plus the reconcile report
and a pyramid gap scan to produce artifacts/blueprint/upgrade-residual.md.

Every item in the report includes a prescribed action (FR-016).

Requirements: FR-015, FR-016, FR-017, FR-018.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Input artifact paths (relative to repo root)
# ---------------------------------------------------------------------------

_CONTRACT_DECISIONS = "artifacts/blueprint/contract_resolve_decisions.json"
_RECONCILE_REPORT = "artifacts/blueprint/upgrade/upgrade_reconcile_report.json"
_DOC_CHECK = "artifacts/blueprint/doc_target_check.json"
_VALIDATE_REPORT = "artifacts/blueprint/upgrade_validate.json"
_VERSION_PIN_DIFF = "artifacts/blueprint/version_pin_diff.json"
_RESIDUAL_MD = "artifacts/blueprint/upgrade-residual.md"
_PYRAMID_CONTRACT = "scripts/lib/quality/test_pyramid_contract.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json_safe(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _scan_pyramid_gaps(repo_root: Path) -> list[str]:
    """Return test file paths not covered by test_pyramid_contract.json.

    If the pyramid contract is absent, all discovered test files are gaps.
    """
    pyramid_path = repo_root / _PYRAMID_CONTRACT
    classified: set[str] = set()
    if pyramid_path.exists():
        try:
            data = json.loads(pyramid_path.read_text(encoding="utf-8"))
            # Collect all classified paths; contract format varies — scan all string values.
            def _walk(obj):
                if isinstance(obj, str):
                    classified.add(obj)
                elif isinstance(obj, list):
                    for item in obj:
                        _walk(item)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        _walk(v)
            _walk(data)
        except Exception:
            pass

    gaps: list[str] = []
    tests_root = repo_root / "tests"
    if tests_root.exists():
        for f in tests_root.rglob("*.py"):
            rel = str(f.relative_to(repo_root))
            if rel not in classified:
                gaps.append(rel)
    return sorted(gaps)


# ---------------------------------------------------------------------------
# Version pin changes section (Issue #164)
# ---------------------------------------------------------------------------

_PRESCRIBED_ACTION = (
    "After running `make infra-bootstrap`, verify and sync affected templates under "
    "`scripts/templates/infra/bootstrap/`, then re-run `make infra-validate`."
)


def _render_version_pin_section(repo_root: Path) -> list[str]:
    """Return Markdown lines for the Version Pin Changes section (FR-007–FR-009)."""
    section: list[str] = [
        "## Version Pin Changes",
        "",
    ]

    data = _load_json_safe(repo_root / _VERSION_PIN_DIFF)
    if not data:
        section += [
            "_Version pin diff unavailable: artifact not found or could not be read. "
            "Manual fallback: "
            "`git diff <baseline_ref> <target_ref> -- scripts/lib/infra/versions.sh`._",
        ]
        return section

    if "error" in data:
        err = data["error"]
        section += [
            f"_Version pin diff unavailable: `{err}`. "
            "Manual fallback: "
            "`git diff <baseline_ref> <target_ref> -- scripts/lib/infra/versions.sh`._",
        ]
        return section

    baseline_ref = data.get("baseline_ref", "<baseline>")
    target_ref = data.get("target_ref", "<target>")
    changed = data.get("changed_pins")
    new_pins = data.get("new_pins")
    removed = data.get("removed_pins")

    if not isinstance(changed, list) or not isinstance(new_pins, list) or not isinstance(removed, list):
        section += [
            "_Version pin diff unavailable: artifact has unexpected structure. "
            "Manual fallback: "
            "`git diff <baseline_ref> <target_ref> -- scripts/lib/infra/versions.sh`._",
        ]
        return section

    if not changed and not new_pins and not removed:
        section.append(
            f"No version pin changes detected between `{baseline_ref}` and `{target_ref}`."
        )
        return section

    if changed:
        section += ["### Changed Pins", ""]
        section += [
            "| Variable | Old Value | New Value | Template References | Action |",
            "|---|---|---|---|---|",
        ]
        for pin in changed:
            var = pin.get("variable", "")
            old = pin.get("old_value", "")
            new = pin.get("new_value", "")
            refs = pin.get("template_references") or []
            refs_str = ", ".join(f"`{r}`" for r in refs) if refs else "_none_"
            section.append(f"| `{var}` | `{old}` | `{new}` | {refs_str} | {_PRESCRIBED_ACTION} |")
        section.append("")

    if new_pins:
        section += ["### New Pins", ""]
        for pin in new_pins:
            var = pin.get("variable", "")
            new = pin.get("new_value", "")
            refs = pin.get("template_references") or []
            refs_str = ", ".join(f"`{r}`" for r in refs) if refs else "_none_"
            section.append(f"- **`{var}`** = `{new}` — template refs: {refs_str} — **Action**: {_PRESCRIBED_ACTION}")
        section.append("")

    if removed:
        section += ["### Removed Pins", ""]
        for pin in removed:
            var = pin.get("variable", "")
            old = pin.get("old_value", "")
            section.append(
                f"- **`{var}`** was `{old}` — removed from target `versions.sh`. "
                "**Action**: remove any references to this variable from consumer templates."
            )
        section.append("")

    return section


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------


def generate_residual_report(repo_root: Path, pipeline_exit: int = 0) -> None:
    """Generate artifacts/blueprint/upgrade-residual.md.

    Always writes the report, even if input artifacts are missing.
    """
    decisions = _load_json_safe(repo_root / _CONTRACT_DECISIONS)
    reconcile = _load_json_safe(repo_root / _RECONCILE_REPORT)
    doc_check = _load_json_safe(repo_root / _DOC_CHECK)
    validate_report_exists = (repo_root / _VALIDATE_REPORT).exists()
    validate = _load_json_safe(repo_root / _VALIDATE_REPORT)
    pyramid_gaps = _scan_pyramid_gaps(repo_root)

    dropped_required = decisions.get("dropped_required_files", [])
    dropped_globs = decisions.get("dropped_prune_globs", [])
    consumer_owned = (
        (reconcile.get("buckets") or {}).get("consumer_owned_manual_review", [])
    )
    missing_targets = doc_check.get("missing_targets", [])
    prune_glob_check = validate.get("prune_glob_check", {})
    prune_glob_scan_ran = validate_report_exists and bool(prune_glob_check)
    prune_glob_status = prune_glob_check.get("status", "")
    prune_glob_violations: list[dict] = prune_glob_check.get("violations", [])
    if not isinstance(prune_glob_violations, list):
        prune_glob_violations = []

    lines: list[str] = [
        "# Upgrade Residual Report",
        "",
        f"Pipeline exit code: `{pipeline_exit}`",
        "",
    ]

    # Gate status
    status = "PASSED" if pipeline_exit == 0 else "FAILED"
    lines += [
        "## Gate Status",
        "",
        f"**{status}** — pipeline exited with code `{pipeline_exit}`.",
        "",
    ]

    # FR-017: Consumer-owned files requiring manual review
    lines += [
        "## Consumer-Owned Files — Manual Review Required",
        "",
    ]
    if consumer_owned:
        lines.append(
            "The following files have `consumer_owned_manual_review` ownership. "
            "Inspect each file and apply changes manually as needed."
        )
        lines.append("")
        for path in consumer_owned:
            lines.append(f"- `{path}` — **Review**: inspect the diff and apply relevant blueprint changes manually.")
    else:
        lines.append("_None — no consumer-owned files flagged for manual review._")
    lines.append("")

    # FR-016: Dropped required_files entries
    lines += [
        "## Dropped `required_files` Entries",
        "",
    ]
    if dropped_required:
        lines.append(
            "The following consumer-added `required_files` entries were dropped because "
            "the files no longer exist on disk. Remove any references to these paths in "
            "consumer configuration or CI gates."
        )
        lines.append("")
        for path in dropped_required:
            lines.append(f"- `{path}` — **Remove**: delete this entry from any consumer configuration that references it.")
    else:
        lines.append("_None — no required_files entries were dropped._")
    lines.append("")

    # FR-016: Dropped prune globs
    lines += [
        "## Dropped `source_artifact_prune_globs_on_init` Entries",
        "",
    ]
    if dropped_globs:
        lines.append(
            "The following prune globs were dropped because they match existing consumer "
            "content. Verify the matched paths are intentional consumer work items."
        )
        lines.append("")
        for glob in dropped_globs:
            lines.append(f"- `{glob}` — **Verify**: confirm paths matching this glob are intentional consumer content.")
    else:
        lines.append("_None — all prune globs were safe to keep._")
    lines.append("")

    # FR-012 / FR-016: Missing make targets from Stage 7
    lines += [
        "## Missing Make Targets in Documentation",
        "",
    ]
    if missing_targets:
        lines.append(
            "The following make targets are referenced in modified markdown files but "
            "are not declared in any `.PHONY` block. Add them to the appropriate `.mk` file."
        )
        lines.append("")
        for target in missing_targets:
            lines.append(f"- `make {target}` — **Add**: declare `{target}` in the appropriate `.mk` file with a `.PHONY` entry.")
    else:
        lines.append("_None — all make targets referenced in docs are declared._")
    lines.append("")

    # Prune-glob violations: files matching source_artifact_prune_globs_on_init that must be removed
    lines += [
        "## Prune-Glob Violations — Blueprint-Internal Files in Consumer Repo",
        "",
    ]
    if not prune_glob_scan_ran:
        lines.append(
            "_Scan not run — `upgrade_validate.json` was not produced. "
            "Stage 9 may have failed before `make blueprint-upgrade-consumer-validate` executed. "
            "Re-run the pipeline or run `make blueprint-upgrade-consumer-validate` directly to check._"
        )
    elif prune_glob_status == "skipped":
        lines.append("_Skipped — repo is not a generated-consumer; prune-glob check does not apply._")
    elif prune_glob_violations:
        lines.append(
            "The following files match `source_artifact_prune_globs_on_init` and must not exist "
            "in generated-consumer repos. Remove them before re-running "
            "`make blueprint-upgrade-consumer-postcheck`."
        )
        lines.append("")
        for entry in prune_glob_violations:
            path = entry.get("path", str(entry)) if isinstance(entry, dict) else str(entry)
            matched = entry.get("matched_glob", "") if isinstance(entry, dict) else ""
            if matched:
                lines.append(f"- `{path}` (matches `{matched}`) — **Remove**: delete this file; it is a blueprint-internal artifact forbidden in consumer repos.")
            else:
                lines.append(f"- `{path}` — **Remove**: delete this file; it is a blueprint-internal artifact forbidden in consumer repos.")
    else:
        lines.append("_None — no files matching prune globs were found in the working tree._")
    lines.append("")

    # FR-018: Pyramid classification gaps
    lines += [
        "## Test Pyramid Classification Gaps",
        "",
    ]
    if pyramid_gaps:
        lines.append(
            f"{len(pyramid_gaps)} test file(s) are not classified in "
            "`scripts/lib/quality/test_pyramid_contract.json`. "
            "Add each file to the appropriate pyramid tier."
        )
        lines.append("")
        for gap in pyramid_gaps[:20]:  # cap at 20 for readability
            lines.append(f"- `{gap}` — **Classify**: add to `test_pyramid_contract.json` under the appropriate tier.")
        if len(pyramid_gaps) > 20:
            lines.append(f"- _... and {len(pyramid_gaps) - 20} more (see full scan output)_")
    else:
        lines.append("_None — all test files are classified in the pyramid contract._")
    lines.append("")

    # Version pin changes (FR-007, FR-008, FR-009)
    lines += _render_version_pin_section(repo_root)
    lines.append("")

    report_path = repo_root / _RESIDUAL_MD
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Stage 10: generate the upgrade residual report.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--pipeline-exit",
        type=int,
        default=0,
        help="Exit code of the pipeline (0=success, non-zero=partial failure).",
    )
    parser.add_argument("--output-path", type=Path, default=None)
    args = parser.parse_args()

    generate_residual_report(args.repo_root, pipeline_exit=args.pipeline_exit)
    output_path = args.output_path or (args.repo_root / _RESIDUAL_MD)
    print(f"[PIPELINE] Stage 10: residual report written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
