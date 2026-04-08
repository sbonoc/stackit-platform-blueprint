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

if [[ "$(tooling_execution_mode)" == "execute" ]] && command -v kubectl >/dev/null 2>&1; then
  prepare_cluster_access
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
    active_kube_context_name || true
  fi
)"
export STATUS_KUBECONFIG_PATH="$(active_kubeconfig_path)"
export STATUS_KUBE_ACCESS_SOURCE="$(active_kube_access_source)"
export STATUS_SMOKE_RESULT_PATH="$ROOT_DIR/artifacts/infra/smoke_result.json"
export STATUS_SMOKE_DIAGNOSTICS_PATH="$ROOT_DIR/artifacts/infra/smoke_diagnostics.json"

json_payload="$(
  python3 "$ROOT_DIR/scripts/lib/infra/status_json_payload.py"
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
