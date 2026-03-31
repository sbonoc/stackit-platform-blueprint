#!/usr/bin/env python3
"""Sync generated runtime identity contract summary blocks in docs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.infra.runtime_identity_contract import load_runtime_identity_contract  # noqa: E402


BEGIN_MARKER = "<!-- BEGIN GENERATED RUNTIME IDENTITY CONTRACT SUMMARY -->"
END_MARKER = "<!-- END GENERATED RUNTIME IDENTITY CONTRACT SUMMARY -->"


DOC_PATHS = (
    Path("docs/platform/consumer/runtime_credentials_eso.md"),
    Path("scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md"),
)


def _replace_marked_block(content: str, replacement: str, path: Path) -> str:
    start = content.find(BEGIN_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"missing generated runtime identity summary markers in {path}")
    end += len(END_MARKER)
    return content[:start] + replacement + content[end:]


def _render_summary(repo_root: Path) -> str:
    contract = load_runtime_identity_contract(repo_root / "blueprint/runtime_identity_contract.yaml")
    lines: list[str] = []
    lines.append(BEGIN_MARKER)
    lines.append("## Contract Summary (Generated)")
    lines.append("")
    lines.append("### Runtime Defaults")
    for env_default in contract.runtime_env_defaults:
        lines.append(f"- `{env_default.name}`: `{env_default.default}`")
    lines.append("")
    lines.append("### ESO Target Secrets")
    lines.append("| Contract ID | Module Gate | Namespace | ExternalSecret | Target Secret | Required Keys |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in contract.eso_contracts:
        module_gate = item.module_id if item.module_id else "mandatory"
        lines.append(
            "| "
            f"`{item.contract_id}` | "
            f"`{module_gate}` | "
            f"`{item.namespace}` | "
            f"`{item.external_secret_name}` | "
            f"`{item.target_secret_name}` | "
            f"`{','.join(item.target_secret_keys)}` |"
        )
    lines.append("")
    lines.append("### Keycloak Realms")
    lines.append("| Realm ID | Module Gate | Realm Env | Default Realm | Client Display | Roles | Admin Role |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for realm in contract.keycloak_realms:
        roles = ",".join(realm.role_names) if realm.role_names else "-"
        admin_role = realm.admin_role if realm.admin_role else "-"
        lines.append(
            "| "
            f"`{realm.realm_id}` | "
            f"`{realm.module_id}` | "
            f"`{realm.realm_env}` | "
            f"`{realm.default_realm_name}` | "
            f"`{realm.client_display_name}` | "
            f"`{roles}` | "
            f"`{admin_role}` |"
        )
    lines.append(END_MARKER)
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve docs and contract paths.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when docs are out of sync.",
    )
    return parser.parse_args()


def _apply(path: Path, updated: str, check: bool, summary: ChangeSummary, repo_root: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"missing runtime identity doc path: {path}")
    original = path.read_text(encoding="utf-8")
    if original == updated:
        summary.skipped_path(path, "already synchronized")
        return []
    if check:
        return [display_repo_path(repo_root, path)]
    path.write_text(updated, encoding="utf-8")
    summary.updated_path(path)
    return []


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    summary = ChangeSummary("quality-docs-sync-runtime-identity-contract-summary")
    rendered_block = _render_summary(repo_root)

    out_of_date: list[str] = []
    for relative_path in DOC_PATHS:
        path = repo_root / relative_path
        updated = _replace_marked_block(path.read_text(encoding="utf-8"), rendered_block, path)
        out_of_date.extend(_apply(path, updated, args.check, summary, repo_root))

    if args.check:
        if out_of_date:
            for relative_path in out_of_date:
                print(f"runtime identity summary doc out of date: {relative_path}", file=sys.stderr)
            print(
                "Run: python3 scripts/lib/docs/sync_runtime_identity_contract_summary.py",
                file=sys.stderr,
            )
            return 1
        return 0

    summary.emit(dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
