#!/usr/bin/env python3
"""Write infra smoke result and diagnostics artifacts from environment contract."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "false") == "true"


def main() -> int:
    modules = [value for value in os.environ.get("SMOKE_ENABLED_MODULES", "").split(",") if value]
    workload_health_path = Path(os.environ.get("SMOKE_WORKLOAD_HEALTH_PATH", ""))
    pod_snapshot_path = Path(os.environ.get("SMOKE_POD_SNAPSHOT_PATH", ""))
    app_runtime_gitops_enabled = _env_bool("SMOKE_APP_RUNTIME_GITOPS_ENABLED")
    app_runtime_min_workloads = int(os.environ.get("SMOKE_APP_RUNTIME_MIN_WORKLOADS", "0") or "0")

    workload_report: dict[str, object] = {}
    if workload_health_path.is_file():
        workload_report = json.loads(workload_health_path.read_text(encoding="utf-8"))

    result_payload = {
        "status": os.environ.get("SMOKE_RESULT_STATUS", ""),
        "profile": os.environ.get("SMOKE_PROFILE", ""),
        "stack": os.environ.get("SMOKE_STACK", ""),
        "environment": os.environ.get("SMOKE_ENVIRONMENT", ""),
        "toolingMode": os.environ.get("SMOKE_TOOLING_MODE", ""),
        "observabilityEnabled": _env_bool("SMOKE_OBSERVABILITY_ENABLED"),
        "enabledModules": modules,
        "startedAtEpoch": int(os.environ.get("SMOKE_STARTED_AT", "0")),
        "finishedAtEpoch": int(os.environ.get("SMOKE_FINISHED_AT", "0")),
    }
    diagnostics_payload = {
        "profile": os.environ.get("SMOKE_PROFILE", ""),
        "stack": os.environ.get("SMOKE_STACK", ""),
        "environment": os.environ.get("SMOKE_ENVIRONMENT", ""),
        "toolingMode": os.environ.get("SMOKE_TOOLING_MODE", ""),
        "observabilityEnabled": _env_bool("SMOKE_OBSERVABILITY_ENABLED"),
        "enabledModules": modules,
        "kubectlContext": os.environ.get("SMOKE_KUBECTL_CONTEXT", "") or None,
        "appRuntime": {
            "gitopsEnabled": app_runtime_gitops_enabled,
            "minimumExpectedWorkloads": app_runtime_min_workloads,
        },
        "artifacts": {
            "provision": _env_bool("SMOKE_PROVISION_PRESENT"),
            "deploy": _env_bool("SMOKE_DEPLOY_PRESENT"),
            "coreRuntimeSmoke": _env_bool("SMOKE_CORE_RUNTIME_PRESENT"),
            "appsSmoke": _env_bool("SMOKE_APPS_PRESENT"),
        },
        "workloadHealth": {
            "reportPath": str(workload_health_path) if workload_health_path else "",
            "reportPresent": workload_health_path.is_file(),
            "podSnapshotPath": str(pod_snapshot_path) if pod_snapshot_path else "",
            "podSnapshotPresent": pod_snapshot_path.is_file(),
            "monitoredNamespaces": [
                value for value in os.environ.get("SMOKE_WORKLOAD_NAMESPACES", "").split(",") if value
            ],
            "status": workload_report.get("status"),
            "statusReason": workload_report.get("statusReason"),
            "checkedPodCount": workload_report.get("checkedPodCount"),
            "namespacePodCounts": workload_report.get("namespacePodCounts"),
            "requiredNamespaceMinimumPods": workload_report.get("requiredNamespaceMinimumPods"),
            "emptyRuntimeNamespaceCount": workload_report.get("emptyRuntimeNamespaceCount"),
            "emptyRuntimeNamespaces": workload_report.get("emptyRuntimeNamespaces"),
            "unhealthyPodCount": workload_report.get("unhealthyPodCount"),
        },
    }

    result_path = Path(os.environ["SMOKE_RESULT_PATH"])
    diagnostics_path = Path(os.environ["SMOKE_DIAGNOSTICS_PATH"])
    result_path.write_text(json.dumps(result_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    diagnostics_path.write_text(json.dumps(diagnostics_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
