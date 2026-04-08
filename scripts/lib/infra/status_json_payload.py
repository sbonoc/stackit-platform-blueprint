#!/usr/bin/env python3
"""Build canonical infra status snapshot payload from environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "false") == "true"


def main() -> int:
    modules = [value for value in os.environ.get("STATUS_ENABLED_MODULES", "").split(",") if value]
    smoke_result_path = Path(os.environ.get("STATUS_SMOKE_RESULT_PATH", ""))
    smoke_diagnostics_path = Path(os.environ.get("STATUS_SMOKE_DIAGNOSTICS_PATH", ""))

    latest_smoke: dict[str, object] = {
        "resultPath": str(smoke_result_path) if smoke_result_path else "",
        "diagnosticsPath": str(smoke_diagnostics_path) if smoke_diagnostics_path else "",
        "resultPresent": smoke_result_path.is_file(),
        "diagnosticsPresent": smoke_diagnostics_path.is_file(),
        "status": "",
        "workloadHealth": {},
    }

    # Keep the latest-smoke shape stable even when the most recent run failed
    # before writing both artifacts; callers can rely on presence flags.
    if smoke_result_path.is_file():
        result_payload = json.loads(smoke_result_path.read_text(encoding="utf-8"))
        latest_smoke["status"] = str(result_payload.get("status", ""))
    if smoke_diagnostics_path.is_file():
        diagnostics_payload = json.loads(smoke_diagnostics_path.read_text(encoding="utf-8"))
        latest_smoke["workloadHealth"] = diagnostics_payload.get("workloadHealth", {})

    payload = {
        "profile": os.environ.get("STATUS_PROFILE", ""),
        "stack": os.environ.get("STATUS_STACK", ""),
        "environment": os.environ.get("STATUS_ENVIRONMENT", ""),
        "toolingMode": os.environ.get("STATUS_TOOLING_MODE", ""),
        "observabilityEnabled": _env_bool("STATUS_OBSERVABILITY_ENABLED"),
        "enabledModules": modules,
        "kubectlContext": os.environ.get("STATUS_KUBECTL_CONTEXT", "") or None,
        "kubeconfigPath": os.environ.get("STATUS_KUBECONFIG_PATH", "") or None,
        "kubeAccessSource": os.environ.get("STATUS_KUBE_ACCESS_SOURCE", "") or None,
        "latestSmoke": latest_smoke,
        "artifacts": {
            "provision": _env_bool("STATUS_PROVISION_PRESENT"),
            "deploy": _env_bool("STATUS_DEPLOY_PRESENT"),
            "smoke": _env_bool("STATUS_SMOKE_PRESENT"),
            "stackitBootstrapApply": _env_bool("STATUS_STACKIT_BOOTSTRAP_APPLY_PRESENT"),
            "stackitFoundationApply": _env_bool("STATUS_STACKIT_FOUNDATION_APPLY_PRESENT"),
            "stackitRuntimeDeploy": _env_bool("STATUS_STACKIT_RUNTIME_DEPLOY_PRESENT"),
            "stackitSmokeRuntime": _env_bool("STATUS_STACKIT_SMOKE_RUNTIME_PRESENT"),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
