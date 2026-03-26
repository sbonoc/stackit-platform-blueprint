#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh"

start_script_metric_trap "infra_smoke"

usage() {
  cat <<'EOF'
Usage: smoke.sh

Contract-driven smoke wrapper:
- validates repository contract,
- validates provision/deploy state artifacts,
- executes base and module smoke checks.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SMOKE_RESULT_PATH="$ROOT_DIR/artifacts/infra/smoke_result.json"
SMOKE_DIAGNOSTICS_PATH="$ROOT_DIR/artifacts/infra/smoke_diagnostics.json"
SMOKE_STARTED_AT="$(date +%s)"
SMOKE_STATUS="failure"

write_smoke_json_artifacts() {
  local finished_at result_status
  finished_at="$(date +%s)"
  result_status="$1"
  ensure_dir "$(dirname "$SMOKE_RESULT_PATH")"
  SMOKE_RESULT_PATH="$SMOKE_RESULT_PATH" \
  SMOKE_DIAGNOSTICS_PATH="$SMOKE_DIAGNOSTICS_PATH" \
  SMOKE_RESULT_STATUS="$result_status" \
  SMOKE_PROFILE="$BLUEPRINT_PROFILE" \
  SMOKE_STACK="$(active_stack)" \
  SMOKE_ENVIRONMENT="$(profile_environment)" \
  SMOKE_TOOLING_MODE="$(tooling_execution_mode)" \
  SMOKE_OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED_NORMALIZED" \
  SMOKE_ENABLED_MODULES="$(enabled_modules_csv)" \
  SMOKE_STARTED_AT="$SMOKE_STARTED_AT" \
  SMOKE_FINISHED_AT="$finished_at" \
  SMOKE_PROVISION_PRESENT="$(state_file_exists provision && echo true || echo false)" \
  SMOKE_DEPLOY_PRESENT="$(state_file_exists deploy && echo true || echo false)" \
  SMOKE_CORE_RUNTIME_PRESENT="$(state_file_exists core_runtime_smoke && echo true || echo false)" \
  SMOKE_APPS_PRESENT="$(state_file_exists apps_smoke apps && echo true || echo false)" \
  SMOKE_KUBECTL_CONTEXT="$(
    if command -v kubectl >/dev/null 2>&1; then
      kubectl config current-context 2>/dev/null || true
    fi
  )" \
  python3 - <<'PY'
import json
import os

modules = [value for value in os.environ.get("SMOKE_ENABLED_MODULES", "").split(",") if value]
result_payload = {
    "status": os.environ.get("SMOKE_RESULT_STATUS", ""),
    "profile": os.environ.get("SMOKE_PROFILE", ""),
    "stack": os.environ.get("SMOKE_STACK", ""),
    "environment": os.environ.get("SMOKE_ENVIRONMENT", ""),
    "toolingMode": os.environ.get("SMOKE_TOOLING_MODE", ""),
    "observabilityEnabled": os.environ.get("SMOKE_OBSERVABILITY_ENABLED", "false") == "true",
    "enabledModules": modules,
    "startedAtEpoch": int(os.environ.get("SMOKE_STARTED_AT", "0")),
    "finishedAtEpoch": int(os.environ.get("SMOKE_FINISHED_AT", "0")),
}
diagnostics_payload = {
    "profile": os.environ.get("SMOKE_PROFILE", ""),
    "stack": os.environ.get("SMOKE_STACK", ""),
    "environment": os.environ.get("SMOKE_ENVIRONMENT", ""),
    "toolingMode": os.environ.get("SMOKE_TOOLING_MODE", ""),
    "observabilityEnabled": os.environ.get("SMOKE_OBSERVABILITY_ENABLED", "false") == "true",
    "enabledModules": modules,
    "kubectlContext": os.environ.get("SMOKE_KUBECTL_CONTEXT", "") or None,
    "artifacts": {
        "provision": os.environ.get("SMOKE_PROVISION_PRESENT", "false") == "true",
        "deploy": os.environ.get("SMOKE_DEPLOY_PRESENT", "false") == "true",
        "coreRuntimeSmoke": os.environ.get("SMOKE_CORE_RUNTIME_PRESENT", "false") == "true",
        "appsSmoke": os.environ.get("SMOKE_APPS_PRESENT", "false") == "true",
    },
}
with open(os.environ["SMOKE_RESULT_PATH"], "w", encoding="utf-8") as handle:
    json.dump(result_payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
with open(os.environ["SMOKE_DIAGNOSTICS_PATH"], "w", encoding="utf-8") as handle:
    json.dump(diagnostics_payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
}

smoke_exit_handler() {
  local exit_code="$1"
  local result_status="failure"
  if [[ "$exit_code" -eq 0 ]]; then
    result_status="success"
  fi
  # Emit machine-readable artifacts on both success and failure so CI and
  # operator tooling can inspect the last attempted smoke run deterministically.
  write_smoke_json_artifacts "$result_status" || true
}

trap 'smoke_exit_handler $?' EXIT

log_info "smoke start profile=$BLUEPRINT_PROFILE stack=$(active_stack) observability=$OBSERVABILITY_ENABLED_NORMALIZED"
run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

if ! state_file_exists provision; then
  log_warn "provision state artifact missing"
fi
if ! state_file_exists deploy; then
  log_warn "deploy state artifact missing"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/core_runtime_smoke.sh"

run_enabled_modules_action smoke observability

run_cmd "$ROOT_DIR/scripts/bin/platform/apps/smoke.sh"

run_enabled_modules_action smoke \
  workflows langfuse postgres neo4j \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy

core_runtime_smoke_state="none"
if state_file_exists core_runtime_smoke; then
  core_runtime_smoke_state="$ROOT_DIR/artifacts/infra/core_runtime_smoke.env"
fi

apps_smoke_state="none"
if state_file_exists apps_smoke apps; then
  apps_smoke_state="$(state_file_path apps_smoke apps)"
fi

state_file="$(
  write_state_file "smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "core_runtime_smoke_state=$core_runtime_smoke_state" \
    "apps_smoke_state=$apps_smoke_state" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "smoke_result_path=$SMOKE_RESULT_PATH" \
    "smoke_diagnostics_path=$SMOKE_DIAGNOSTICS_PATH" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "smoke state written to $state_file"
log_info "infra smoke complete"
