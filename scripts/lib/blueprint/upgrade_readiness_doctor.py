#!/usr/bin/env python3
"""Generate consumer upgrade readiness diagnostics for blueprint repositories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402


REQUIRED_UPGRADE_TARGETS: tuple[str, ...] = (
    "blueprint-resync-consumer-seeds",
    "blueprint-upgrade-consumer-preflight",
    "blueprint-upgrade-consumer",
    "blueprint-upgrade-consumer-validate",
)


def _discover_make_targets(repo_root: Path) -> set[str]:
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    makefiles: list[Path] = []
    root_makefile = repo_root / "Makefile"
    if root_makefile.is_file():
        makefiles.append(root_makefile)
    make_dir = repo_root / "make"
    if make_dir.is_dir():
        makefiles.extend(sorted(path for path in make_dir.rglob("*.mk") if path.is_file()))

    targets: set[str] = set()
    for makefile in makefiles:
        for line in makefile.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            target = match.group(1)
            if target == ".PHONY":
                continue
            targets.add(target)
    return targets


def _load_json_if_exists(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def build_report(repo_root: Path) -> dict[str, object]:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    make_targets = _discover_make_targets(repo_root)

    missing_upgrade_targets = sorted(target for target in REQUIRED_UPGRADE_TARGETS if target not in make_targets)

    broken_dependency_edges: list[dict[str, str]] = []
    for consumer_path, dependency_path in RUNTIME_DEPENDENCY_EDGES:
        consumer_file = repo_root / consumer_path
        dependency_file = repo_root / dependency_path
        if not consumer_file.is_file():
            continue
        consumer_content = consumer_file.read_text(encoding="utf-8", errors="surrogateescape")
        if dependency_path not in consumer_content:
            continue
        if dependency_file.is_file():
            continue
        broken_dependency_edges.append(
            {
                "consumerPath": consumer_path,
                "dependencyPath": dependency_path,
                "reason": "missing_dependency_file",
            }
        )

    preflight_path = repo_root / "artifacts/blueprint/upgrade_preflight.json"
    preflight_payload = _load_json_if_exists(preflight_path)
    required_manual_actions: list[object] = []
    follow_up_commands: list[object] = []
    if preflight_payload is not None:
        raw_required_actions = preflight_payload.get("required_manual_actions")
        if isinstance(raw_required_actions, list):
            required_manual_actions = raw_required_actions
        raw_follow_ups = preflight_payload.get("follow_up_commands")
        if isinstance(raw_follow_ups, list):
            follow_up_commands = raw_follow_ups

    upgrade_apply_path = repo_root / "artifacts/blueprint/upgrade_apply.json"
    upgrade_apply_payload = _load_json_if_exists(upgrade_apply_path)

    apps_ci_bootstrap_placeholder = False
    platform_make = repo_root / "make/platform.mk"
    if platform_make.is_file():
        apps_ci_bootstrap_placeholder = "apps-ci-bootstrap-consumer placeholder active" in platform_make.read_text(
            encoding="utf-8"
        )

    warnings: list[str] = []
    if not preflight_path.is_file():
        warnings.append("upgrade_preflight.json not found; run make blueprint-upgrade-consumer-preflight")
    if apps_ci_bootstrap_placeholder and contract.repository.repo_mode == "generated-consumer":
        warnings.append(
            "apps-ci-bootstrap-consumer is still placeholder; replace with consumer-owned deterministic dependency bootstrap"
        )

    errors: list[str] = []
    if missing_upgrade_targets:
        errors.append("missing required upgrade make targets")
    if broken_dependency_edges:
        errors.append("runtime dependency edges are broken")

    return {
        "status": "ready" if not errors else "needs-attention",
        "repoMode": contract.repository.repo_mode,
        "requiredUpgradeTargets": list(REQUIRED_UPGRADE_TARGETS),
        "missingUpgradeTargets": missing_upgrade_targets,
        "runtimeDependencyEdges": {
            "total": len(RUNTIME_DEPENDENCY_EDGES),
            "broken": broken_dependency_edges,
            "brokenCount": len(broken_dependency_edges),
        },
        "preflight": {
            "path": str(preflight_path),
            "present": preflight_payload is not None,
            "requiredManualActionCount": len(required_manual_actions),
            "requiredManualActions": required_manual_actions,
            "followUpCommands": follow_up_commands,
        },
        "upgradeApply": {
            "path": str(upgrade_apply_path),
            "present": upgrade_apply_payload is not None,
        },
        "consumerOwnedBootstrap": {
            "appsCiBootstrapConsumerPlaceholder": apps_ci_bootstrap_placeholder,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/blueprint/upgrade_readiness_doctor.json"),
    )
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_path = args.output if args.output.is_absolute() else repo_root / args.output

    report = build_report(repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"upgrade readiness report written: {output_path}")
    print(f"status={report['status']} errors={len(report['errors'])} warnings={len(report['warnings'])}")

    if args.strict and report["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
