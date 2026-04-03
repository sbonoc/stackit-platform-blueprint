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
FAST_QUALITY_COMMANDS = (
    "make quality-hooks-fast",
    "make quality-hooks-strict",
    "pre-commit run --hook-stage pre-push --all-files",
)
APPS_BASELINE_COMMANDS = (
    "BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-bootstrap",
    "BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-smoke",
)
DOCS_COMMANDS = (
    "make docs-install",
    "make docs-build",
    "make docs-smoke",
)
FAST_TEST_LANES = (
    "make test-unit-all",
    "make test-integration-all",
    "make test-contracts-all",
    "make test-e2e-all-local",
)
FULL_PUSH_LANES = ("make test-e2e-all-local-full",)
GENERATED_SMOKE_EXPORTS = (
    "export BLUEPRINT_TEMPLATE_SMOKE_SCENARIO=local-lite-baseline",
    "export BLUEPRINT_PROFILE=local-lite",
    "export OBSERVABILITY_ENABLED=false",
    "export WORKFLOWS_ENABLED=false",
    "export LANGFUSE_ENABLED=false",
    "export POSTGRES_ENABLED=false",
    "export NEO4J_ENABLED=false",
    "export OBJECT_STORAGE_ENABLED=false",
    "export RABBITMQ_ENABLED=false",
    "export DNS_ENABLED=false",
    "export PUBLIC_ENDPOINTS_ENABLED=false",
    "export SECRETS_MANAGER_ENABLED=false",
    "export KMS_ENABLED=false",
    "export IDENTITY_AWARE_PROXY_ENABLED=false",
)
GENERATED_SMOKE_RUN = (
    "BLUEPRINT_REPO_NAME=ci-smoke-blueprint \\",
    "BLUEPRINT_GITHUB_ORG=ci-smoke-org \\",
    "BLUEPRINT_GITHUB_REPO=ci-smoke-blueprint \\",
    "BLUEPRINT_DEFAULT_BRANCH=main \\",
    "make blueprint-template-smoke",
)


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
        f"{_indent_block(FAST_QUALITY_COMMANDS, spaces=10)}\n\n"
        "      - name: Validate app baseline\n"
        "        run: |\n"
        f"{_indent_block(APPS_BASELINE_COMMANDS, spaces=10)}\n\n"
        "      - name: Build and smoke docs\n"
        "        run: |\n"
        f"{_indent_block(DOCS_COMMANDS, spaces=10)}\n\n"
        "      - name: Run canonical fast test lanes\n"
        "        run: |\n"
        f"{_indent_block(FAST_TEST_LANES, spaces=10)}\n\n"
        f"      - name: Run canonical full e2e lane on {default_branch} updates\n"
        "        if: github.event_name == 'push'\n"
        "        run: |\n"
        f"{_indent_block(FULL_PUSH_LANES, spaces=10)}\n\n"
        "  generated-consumer-smoke:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v6\n\n"
        "      - name: Prepare shared CI baseline\n"
        "        uses: ./.github/actions/prepare-blueprint-ci\n\n"
        "      - name: Smoke generated consumer baseline\n"
        "        run: |\n"
        f"{_indent_block(GENERATED_SMOKE_EXPORTS, spaces=10)}\n"
        f"{_indent_block(GENERATED_SMOKE_RUN, spaces=10)}\n"
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
