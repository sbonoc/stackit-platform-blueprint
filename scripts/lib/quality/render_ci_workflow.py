#!/usr/bin/env python3
"""Render/check the source CI workflow from blueprint contract metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


DEFAULT_OUTPUT = Path(".github/workflows/ci.yml")
BLUEPRINT_QUALITY_LANE = ("make quality-ci-blueprint",)
BLUEPRINT_SLOW_INTEGRATION_LANE = ("make quality-ci-slow-integration",)
BLUEPRINT_FULL_PUSH_LANE = ("make quality-ci-full-e2e",)
GENERATED_CONSUMER_SMOKE_LANE = ("make quality-ci-generated-consumer-smoke",)
UPGRADE_E2E_VALIDATE_LANE = ("make quality-ci-upgrade-validate",)


def _indent_block(lines: tuple[str, ...], *, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" for line in lines)


def _render_ci(default_branch: str) -> str:
    return (
        "name: ci\n\n"
        "on:\n"
        "  pull_request:\n"
        "  push:\n"
        "    branches:\n"
        f"      - {default_branch}\n\n"
        "jobs:\n"
        "  blueprint-quality:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v6\n\n"
        "      - name: Prepare shared CI baseline\n"
        "        uses: ./.github/actions/prepare-blueprint-ci\n\n"
        "      - name: Run quality gates\n"
        "        run: |\n"
        f"{_indent_block(BLUEPRINT_QUALITY_LANE, spaces=10)}\n\n"
        f"      - name: Run canonical slow integration lane on {default_branch} updates\n"
        "        if: github.event_name == 'push'\n"
        "        run: |\n"
        f"{_indent_block(BLUEPRINT_SLOW_INTEGRATION_LANE, spaces=10)}\n\n"
        f"      - name: Run canonical full e2e lane on {default_branch} updates\n"
        "        if: github.event_name == 'push'\n"
        "        run: |\n"
        f"{_indent_block(BLUEPRINT_FULL_PUSH_LANE, spaces=10)}\n\n"
        "      - name: Upload runtime contract drift report artifact\n"
        "        if: always()\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: runtime-contract-drift-report\n"
        "          path: artifacts/blueprint/runtime_contract_drift_report.json\n"
        "          if-no-files-found: warn\n\n"
        "  generated-consumer-smoke:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v6\n\n"
        "      - name: Prepare shared CI baseline\n"
        "        uses: ./.github/actions/prepare-blueprint-ci\n\n"
        "      - name: Smoke generated consumer baseline\n"
        "        run: |\n"
        f"{_indent_block(GENERATED_CONSUMER_SMOKE_LANE, spaces=10)}\n\n"
        "  upgrade-e2e-validation:\n"
        "    runs-on: ubuntu-latest\n"
        "    if: github.event_name == 'push'\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v6\n\n"
        "      - name: Prepare shared CI baseline\n"
        "        uses: ./.github/actions/prepare-blueprint-ci\n\n"
        "      - name: Run upgrade e2e validation\n"
        "        run: |\n"
        f"{_indent_block(UPGRADE_E2E_VALIDATE_LANE, spaces=10)}\n\n"
        "      - name: Upload upgrade validation junit artifact\n"
        "        if: always()\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: upgrade-validate-junit\n"
        "          path: artifacts/blueprint/upgrade_validate/upgrade_validate_junit.xml\n"
        "          if-no-files-found: warn\n"
    )


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve contract and workflow paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Workflow output path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when the rendered workflow differs from the tracked file.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    output_path = args.output if args.output.is_absolute() else repo_root / args.output

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    rendered = _render_ci(contract.repository.default_branch)

    if args.check:
        if not output_path.exists():
            print(f"ci workflow missing: {display_repo_path(repo_root, output_path)}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(
                "ci workflow is out of date: "
                f"{display_repo_path(repo_root, output_path)}\n"
                "Run: python3 scripts/lib/quality/render_ci_workflow.py",
                file=sys.stderr,
            )
            return 1
        return 0

    changed = _write_if_changed(output_path, rendered)
    status = "rendered" if changed else "already up to date"
    print(
        f"{status}: {display_repo_path(repo_root, output_path)} "
        f"(default_branch={contract.repository.default_branch})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
