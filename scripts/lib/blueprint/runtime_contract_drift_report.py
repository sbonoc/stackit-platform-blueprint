#!/usr/bin/env python3
"""Generate runtime contract drift report for CI/operator visibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402


RUNTIME_CONTRACT_KEYS: tuple[str, ...] = (
    "app_runtime_gitops_contract",
    "event_messaging_contract",
    "zero_downtime_evolution_contract",
    "tenant_context_contract",
)


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _resolve_toggle_enabled(spec_raw: dict[str, object], contract_section: dict[str, object]) -> bool:
    enabled_by_default = bool(contract_section.get("enabled_by_default", False))
    enable_flag = contract_section.get("enable_flag")
    if not isinstance(enable_flag, str) or enable_flag.strip() == "":
        return enabled_by_default
    env_value = (
        __import__("os").environ.get(enable_flag, "").strip().lower()
    )
    if env_value in {"1", "true", "yes", "on"}:
        return True
    if env_value in {"0", "false", "no", "off"}:
        return False
    return enabled_by_default


def build_report(repo_root: Path) -> dict[str, object]:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    spec_raw = _mapping(contract.raw.get("spec"))

    contract_summaries: dict[str, object] = {}
    total_drift = 0
    for contract_key in RUNTIME_CONTRACT_KEYS:
        section = _mapping(spec_raw.get(contract_key))
        docs_paths = _as_str_list(section.get("docs_paths"))
        required_paths = _as_str_list(section.get("required_paths_when_enabled"))
        enabled = _resolve_toggle_enabled(spec_raw, section)

        missing_docs = sorted(path for path in docs_paths if not (repo_root / path).is_file())
        missing_required_paths: list[str] = []
        if enabled:
            missing_required_paths = sorted(path for path in required_paths if not (repo_root / path).exists())

        drift_count = len(missing_docs) + len(missing_required_paths)
        total_drift += drift_count
        contract_summaries[contract_key] = {
            "enabled": enabled,
            "enableFlag": section.get("enable_flag", ""),
            "docsPaths": docs_paths,
            "requiredPathsWhenEnabled": required_paths,
            "missingDocsPaths": missing_docs,
            "missingRequiredPaths": missing_required_paths,
            "driftCount": drift_count,
        }

    dependency_edge_errors: list[dict[str, str]] = []
    for consumer_path, dependency_path in RUNTIME_DEPENDENCY_EDGES:
        consumer = repo_root / consumer_path
        dependency = repo_root / dependency_path
        if not consumer.is_file():
            continue
        content = consumer.read_text(encoding="utf-8", errors="surrogateescape")
        if dependency_path not in content:
            continue
        if dependency.is_file():
            continue
        dependency_edge_errors.append(
            {
                "consumerPath": consumer_path,
                "dependencyPath": dependency_path,
                "reason": "missing_dependency_file",
            }
        )

    total_drift += len(dependency_edge_errors)
    return {
        "status": "drift-detected" if total_drift > 0 else "in-sync",
        "repoMode": contract.repository.repo_mode,
        "runtimeContracts": contract_summaries,
        "runtimeDependencyEdges": {
            "total": len(RUNTIME_DEPENDENCY_EDGES),
            "broken": dependency_edge_errors,
            "brokenCount": len(dependency_edge_errors),
        },
        "totalDriftCount": total_drift,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve contract and artifact paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/blueprint/runtime_contract_drift_report.json"),
        help="Output report path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when drift is detected.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_path = args.output if args.output.is_absolute() else repo_root / args.output

    report = build_report(repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"runtime contract drift report written: {output_path}")
    print(f"status={report['status']} total_drift={report['totalDriftCount']}")

    if args.strict and int(report["totalDriftCount"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
