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
SMOKE_WORKLOAD_HEALTH_PATH="$ROOT_DIR/artifacts/infra/workload_health.json"
SMOKE_POD_SNAPSHOT_PATH="$ROOT_DIR/artifacts/infra/workload_pods.json"
SMOKE_STARTED_AT="$(date +%s)"
SMOKE_STATUS="failure"
set_default_env APP_RUNTIME_GITOPS_ENABLED "true"
app_runtime_gitops_enabled="$(shell_normalize_bool_truefalse "$APP_RUNTIME_GITOPS_ENABLED")"
set_default_env APP_RUNTIME_MIN_WORKLOADS "1"
if ! [[ "$APP_RUNTIME_MIN_WORKLOADS" =~ ^[0-9]+$ ]]; then
  log_fatal "APP_RUNTIME_MIN_WORKLOADS must be a non-negative integer; got: $APP_RUNTIME_MIN_WORKLOADS"
fi
app_runtime_min_workloads="$APP_RUNTIME_MIN_WORKLOADS"
if [[ "$app_runtime_gitops_enabled" != "true" ]]; then
  app_runtime_min_workloads="0"
fi
log_metric \
  "infra_smoke_expected_runtime_min_workloads_total" \
  "$app_runtime_min_workloads" \
  "gitops_enabled=$app_runtime_gitops_enabled"

workload_health_namespaces() {
  cat <<'EOF'
apps
argocd
crossplane-system
data
envoy-gateway-system
external-secrets
messaging
network
observability
security
EOF
}

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
      active_kube_context_name || true
    fi
  )" \
  SMOKE_WORKLOAD_HEALTH_PATH="$SMOKE_WORKLOAD_HEALTH_PATH" \
  SMOKE_POD_SNAPSHOT_PATH="$SMOKE_POD_SNAPSHOT_PATH" \
  SMOKE_WORKLOAD_NAMESPACES="$(workload_health_namespaces | paste -sd, -)" \
  SMOKE_APP_RUNTIME_GITOPS_ENABLED="$app_runtime_gitops_enabled" \
  SMOKE_APP_RUNTIME_MIN_WORKLOADS="$app_runtime_min_workloads" \
  python3 "$ROOT_DIR/scripts/lib/infra/smoke_artifacts.py"
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

if [[ "$(tooling_execution_mode)" == "execute" ]] && command -v kubectl >/dev/null 2>&1; then
  prepare_cluster_access
fi

if ! state_file_exists provision; then
  log_warn "provision state artifact missing"
fi
if ! state_file_exists deploy; then
  log_warn "deploy state artifact missing"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/core_runtime_smoke.sh"
run_cmd "$ROOT_DIR/scripts/bin/platform/auth/reconcile_runtime_identity.sh"

run_enabled_modules_action smoke observability

apps_smoke_failed="0"
if ! run_cmd "$ROOT_DIR/scripts/bin/platform/apps/smoke.sh"; then
  apps_smoke_failed="1"
  log_metric "infra_smoke_component_failure_total" "1" "component=apps-smoke"
  log_error \
    "apps smoke failed; continuing with workload diagnostics so smoke_diagnostics.json captures empty-runtime/unhealthy context"
fi

run_enabled_modules_action smoke \
  workflows langfuse postgres neo4j \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy

if [[ "$(tooling_execution_mode)" == "execute" ]] && command -v kubectl >/dev/null 2>&1; then
  ensure_dir "$(dirname "$SMOKE_POD_SNAPSHOT_PATH")"
  namespace_args=()
  while IFS= read -r namespace; do
    [[ -n "$namespace" ]] || continue
    namespace_args+=(--namespace "$namespace")
  done < <(workload_health_namespaces)
  required_namespace_args=()
  if [[ "$app_runtime_min_workloads" -gt 0 ]]; then
    required_namespace_args+=(--required-namespace-min-pods "apps=$app_runtime_min_workloads")
  fi
  run_cmd_capture kubectl get pods -A -o json >"$SMOKE_POD_SNAPSHOT_PATH"
  run_cmd python3 "$ROOT_DIR/scripts/bin/infra/workload_health_check.py" \
    --input "$SMOKE_POD_SNAPSHOT_PATH" \
    --output "$SMOKE_WORKLOAD_HEALTH_PATH" \
    "${namespace_args[@]}" \
    "${required_namespace_args[@]}"
fi

core_runtime_smoke_state="none"
if state_file_exists core_runtime_smoke; then
  core_runtime_smoke_state="$ROOT_DIR/artifacts/infra/core_runtime_smoke.env"
fi

apps_smoke_state="none"
if state_file_exists apps_smoke apps; then
  apps_smoke_state="$(state_file_path apps_smoke apps)"
fi

runtime_credentials_state="none"
if state_file_exists runtime_credentials_eso_reconcile; then
  runtime_credentials_state="$(state_file_path runtime_credentials_eso_reconcile)"
fi

runtime_identity_state="none"
if state_file_exists runtime_identity_reconcile; then
  runtime_identity_state="$(state_file_path runtime_identity_reconcile)"
fi

apps_smoke_status="success"
if [[ "$apps_smoke_failed" -ne 0 ]]; then
  apps_smoke_status="failure"
fi
log_metric \
  "infra_smoke_component_status_total" \
  "1" \
  "component=apps-smoke status=$apps_smoke_status app_runtime_gitops_enabled=$app_runtime_gitops_enabled"

state_file="$(
  write_state_file "smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "core_runtime_smoke_state=$core_runtime_smoke_state" \
    "runtime_credentials_state=$runtime_credentials_state" \
    "runtime_identity_state=$runtime_identity_state" \
    "apps_smoke_state=$apps_smoke_state" \
    "apps_smoke_status=$apps_smoke_status" \
    "app_runtime_gitops_enabled=$app_runtime_gitops_enabled" \
    "app_runtime_min_workloads=$app_runtime_min_workloads" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "smoke_result_path=$SMOKE_RESULT_PATH" \
    "smoke_diagnostics_path=$SMOKE_DIAGNOSTICS_PATH" \
    "workload_health_path=$SMOKE_WORKLOAD_HEALTH_PATH" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "smoke state written to $state_file"
if [[ "$apps_smoke_failed" -ne 0 ]]; then
  log_fatal "infra smoke failed because apps smoke checks failed; inspect artifacts/apps/apps_smoke.env and artifacts/infra/smoke_diagnostics.json"
fi
log_info "infra smoke complete"
