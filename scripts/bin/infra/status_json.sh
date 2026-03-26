#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_status_json"

usage() {
  cat <<'USAGE'
Usage: status_json.sh

Emits canonical infra status snapshot in JSON format.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

state_flag() {
  local artifact_name="$1"
  if state_file_exists "$artifact_name"; then
    echo "true"
    return 0
  fi
  echo "false"
}

export STATUS_PROFILE="$BLUEPRINT_PROFILE"
export STATUS_STACK="$(active_stack)"
export STATUS_ENVIRONMENT="$(profile_environment)"
export STATUS_ENABLED_MODULES="$(enabled_modules_csv)"
export STATUS_TOOLING_MODE="$(tooling_execution_mode)"
export STATUS_OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED_NORMALIZED"
export STATUS_PROVISION_PRESENT="$(state_flag provision)"
export STATUS_DEPLOY_PRESENT="$(state_flag deploy)"
export STATUS_SMOKE_PRESENT="$(state_flag smoke)"
export STATUS_STACKIT_BOOTSTRAP_APPLY_PRESENT="$(state_flag stackit_bootstrap_apply)"
export STATUS_STACKIT_FOUNDATION_APPLY_PRESENT="$(state_flag stackit_foundation_apply)"
export STATUS_STACKIT_RUNTIME_DEPLOY_PRESENT="$(state_flag stackit_runtime_deploy)"
export STATUS_STACKIT_SMOKE_RUNTIME_PRESENT="$(state_flag stackit_smoke_runtime)"
export STATUS_KUBECTL_CONTEXT="$(
  if command -v kubectl >/dev/null 2>&1; then
    kubectl config current-context 2>/dev/null || true
  fi
)"
export STATUS_SMOKE_RESULT_PATH="$ROOT_DIR/artifacts/infra/smoke_result.json"
export STATUS_SMOKE_DIAGNOSTICS_PATH="$ROOT_DIR/artifacts/infra/smoke_diagnostics.json"

json_payload="$(
  python3 - <<'PY'
import json
import os
from pathlib import Path

modules = [value for value in os.environ.get("STATUS_ENABLED_MODULES", "").split(",") if value]
smoke_result_path = Path(os.environ.get("STATUS_SMOKE_RESULT_PATH", ""))
smoke_diagnostics_path = Path(os.environ.get("STATUS_SMOKE_DIAGNOSTICS_PATH", ""))
latest_smoke = {
    "resultPath": str(smoke_result_path) if smoke_result_path else "",
    "diagnosticsPath": str(smoke_diagnostics_path) if smoke_diagnostics_path else "",
    "resultPresent": smoke_result_path.is_file(),
    "diagnosticsPresent": smoke_diagnostics_path.is_file(),
    "status": "",
}
# Keep the latest-smoke shape stable even when the most recent run failed before
# writing both artifacts; callers can rely on presence flags instead of guessing.
if smoke_result_path.is_file():
    result_payload = json.loads(smoke_result_path.read_text(encoding="utf-8"))
    latest_smoke["status"] = str(result_payload.get("status", ""))
payload = {
    "profile": os.environ.get("STATUS_PROFILE", ""),
    "stack": os.environ.get("STATUS_STACK", ""),
    "environment": os.environ.get("STATUS_ENVIRONMENT", ""),
    "toolingMode": os.environ.get("STATUS_TOOLING_MODE", ""),
    "observabilityEnabled": os.environ.get("STATUS_OBSERVABILITY_ENABLED", "false") == "true",
    "enabledModules": modules,
    "kubectlContext": os.environ.get("STATUS_KUBECTL_CONTEXT", "") or None,
    "latestSmoke": latest_smoke,
    "artifacts": {
        "provision": os.environ.get("STATUS_PROVISION_PRESENT", "false") == "true",
        "deploy": os.environ.get("STATUS_DEPLOY_PRESENT", "false") == "true",
        "smoke": os.environ.get("STATUS_SMOKE_PRESENT", "false") == "true",
        "stackitBootstrapApply": os.environ.get("STATUS_STACKIT_BOOTSTRAP_APPLY_PRESENT", "false") == "true",
        "stackitFoundationApply": os.environ.get("STATUS_STACKIT_FOUNDATION_APPLY_PRESENT", "false") == "true",
        "stackitRuntimeDeploy": os.environ.get("STATUS_STACKIT_RUNTIME_DEPLOY_PRESENT", "false") == "true",
        "stackitSmokeRuntime": os.environ.get("STATUS_STACKIT_SMOKE_RUNTIME_PRESENT", "false") == "true",
    },
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY
)"

snapshot_path="$ROOT_DIR/artifacts/infra/infra_status_snapshot.json"
ensure_dir "$(dirname "$snapshot_path")"
printf '%s\n' "$json_payload" >"$snapshot_path"
printf '%s\n' "$json_payload"

state_file="$(
  write_state_file "infra_status_json" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "snapshot_path=$snapshot_path" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra status JSON snapshot written to $snapshot_path"
log_info "infra status-json state written to $state_file"
