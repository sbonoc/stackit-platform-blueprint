#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "apps_smoke"
set_state_namespace apps

usage() {
  cat <<'EOF'
Usage: smoke.sh

Runs app-layer smoke checks:
- verifies app bootstrap artifact exists,
- validates app manifest contract keys,
- records smoke artifact under artifacts/apps for orchestration traceability.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env APP_CATALOG_SCAFFOLD_ENABLED "false"
app_catalog_scaffold_enabled="$(shell_normalize_bool_truefalse "$APP_CATALOG_SCAFFOLD_ENABLED")"
log_metric "app_catalog_scaffold_enabled_total" "1" "enabled=$app_catalog_scaffold_enabled"
set_default_env APP_RUNTIME_GITOPS_ENABLED "true"
app_runtime_gitops_enabled="$(shell_normalize_bool_truefalse "$APP_RUNTIME_GITOPS_ENABLED")"
log_metric "app_runtime_gitops_enabled_total" "1" "enabled=$app_runtime_gitops_enabled"
set_default_env APP_RUNTIME_MIN_WORKLOADS "1"
if ! [[ "$APP_RUNTIME_MIN_WORKLOADS" =~ ^[0-9]+$ ]]; then
  log_fatal "APP_RUNTIME_MIN_WORKLOADS must be a non-negative integer; got: $APP_RUNTIME_MIN_WORKLOADS"
fi
app_runtime_min_workloads="$APP_RUNTIME_MIN_WORKLOADS"
if [[ "$app_runtime_gitops_enabled" != "true" ]]; then
  app_runtime_min_workloads="0"
fi
log_metric \
  "app_runtime_expected_min_workloads_total" \
  "$app_runtime_min_workloads" \
  "gitops_enabled=$app_runtime_gitops_enabled"

manifest="$ROOT_DIR/apps/catalog/manifest.yaml"
versions_lock="$ROOT_DIR/apps/catalog/versions.lock"

if ! state_file_exists apps_bootstrap; then
  log_fatal "missing apps bootstrap state artifact; run make apps-bootstrap first"
fi

bootstrap_state_file="$(state_file_path apps_bootstrap)"
bootstrap_scaffold_enabled_raw="$(
  awk -F= '$1=="app_catalog_scaffold_enabled"{print $2}' "$bootstrap_state_file" | tail -n 1
)"
if [[ -z "$bootstrap_scaffold_enabled_raw" ]]; then
  log_fatal \
    "apps bootstrap state missing app_catalog_scaffold_enabled marker; rerun make apps-bootstrap before apps-smoke"
fi
bootstrap_scaffold_enabled="$(shell_normalize_bool_truefalse "$bootstrap_scaffold_enabled_raw")"
if [[ "$bootstrap_scaffold_enabled" != "$app_catalog_scaffold_enabled" ]]; then
  log_fatal \
    "app catalog scaffold mode mismatch: apps_bootstrap used APP_CATALOG_SCAFFOLD_ENABLED=${bootstrap_scaffold_enabled}, apps-smoke is using ${app_catalog_scaffold_enabled}; rerun make apps-bootstrap with the current mode"
fi

bootstrap_runtime_gitops_enabled_raw="$(
  awk -F= '$1=="app_runtime_gitops_enabled"{print $2}' "$bootstrap_state_file" | tail -n 1
)"
if [[ -z "$bootstrap_runtime_gitops_enabled_raw" ]]; then
  log_fatal \
    "apps bootstrap state missing app_runtime_gitops_enabled marker; rerun make apps-bootstrap before apps-smoke"
fi
bootstrap_runtime_gitops_enabled="$(shell_normalize_bool_truefalse "$bootstrap_runtime_gitops_enabled_raw")"
if [[ "$bootstrap_runtime_gitops_enabled" != "$app_runtime_gitops_enabled" ]]; then
  log_fatal \
    "app runtime GitOps mode mismatch: apps_bootstrap used APP_RUNTIME_GITOPS_ENABLED=${bootstrap_runtime_gitops_enabled}, apps-smoke is using ${app_runtime_gitops_enabled}; rerun make apps-bootstrap with the current mode"
fi

runtime_workload_check_required="false"
runtime_workload_check_mode="skipped"
runtime_workload_check_reason="app-runtime-gitops-disabled"
runtime_workload_observed_count="0"

run_runtime_workload_presence_check() {
  if [[ "$app_runtime_gitops_enabled" != "true" ]]; then
    runtime_workload_check_mode="skipped"
    runtime_workload_check_reason="app-runtime-gitops-disabled"
    log_metric \
      "app_runtime_live_workload_presence_total" \
      "1" \
      "status=skipped reason=app-runtime-gitops-disabled required_min=0"
    log_info "app runtime workload live check skipped because APP_RUNTIME_GITOPS_ENABLED=false"
    return 0
  fi

  runtime_workload_check_required="true"
  local execution_mode
  execution_mode="$(tooling_execution_mode)"
  if [[ "$execution_mode" != "execute" ]]; then
    runtime_workload_check_mode="skipped"
    runtime_workload_check_reason="dry-run-mode"
    log_metric \
      "app_runtime_live_workload_presence_total" \
      "1" \
      "status=skipped reason=dry-run-mode required_min=$app_runtime_min_workloads"
    log_info \
      "app runtime workload live check skipped because tooling mode is dry-run (set DRY_RUN=false to execute)"
    return 0
  fi

  prepare_cluster_access
  runtime_workload_check_mode="execute"
  local app_runtime_namespace
  app_runtime_namespace="apps"

  local observed_count
  observed_count="$(
    kubectl get deployment,statefulset --namespace "$app_runtime_namespace" -o json \
      | python3 "$ROOT_DIR/scripts/lib/platform/apps/runtime_workload_helpers.py"
  )"
  if ! [[ "$observed_count" =~ ^[0-9]+$ ]]; then
    log_fatal "unable to parse app runtime workload count from kubectl response: $observed_count"
  fi
  runtime_workload_observed_count="$observed_count"

  if [[ "$runtime_workload_observed_count" -lt "$app_runtime_min_workloads" ]]; then
    runtime_workload_check_reason="empty-runtime-workloads"
    log_metric \
      "app_runtime_live_workload_presence_total" \
      "1" \
      "status=failed reason=empty-runtime-workloads namespace=$app_runtime_namespace required_min=$app_runtime_min_workloads observed=$runtime_workload_observed_count"
    log_error \
      "app runtime workload presence check failed namespace=$app_runtime_namespace observed=$runtime_workload_observed_count required_min=$app_runtime_min_workloads"
    return 1
  fi

  runtime_workload_check_reason="ok"
  log_metric \
    "app_runtime_live_workload_presence_total" \
    "1" \
    "status=passed namespace=$app_runtime_namespace required_min=$app_runtime_min_workloads observed=$runtime_workload_observed_count"
  log_info \
    "app runtime workload presence check passed namespace=$app_runtime_namespace observed=$runtime_workload_observed_count required_min=$app_runtime_min_workloads"
  return 0
}

runtime_workload_check_failed="0"
if ! run_runtime_workload_presence_check; then
  runtime_workload_check_failed="1"
fi

if [[ "$app_catalog_scaffold_enabled" != "true" ]]; then
  state_file="$(
    write_state_file "apps_smoke" \
      "profile=$BLUEPRINT_PROFILE" \
      "stack=$(active_stack)" \
      "app_catalog_scaffold_enabled=false" \
      "app_runtime_gitops_enabled=$app_runtime_gitops_enabled" \
      "app_runtime_min_workloads=$app_runtime_min_workloads" \
      "runtime_workload_check_required=$runtime_workload_check_required" \
      "runtime_workload_check_mode=$runtime_workload_check_mode" \
      "runtime_workload_check_reason=$runtime_workload_check_reason" \
      "runtime_workload_observed_count=$runtime_workload_observed_count" \
      "manifest_path=none" \
      "versions_lock_path=none" \
      "check_mode=skipped" \
      "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  )"
  log_info "app catalog scaffold disabled; skipping apps/catalog smoke assertions"
  log_info "apps smoke state written to $state_file"
  if [[ "$runtime_workload_check_failed" -ne 0 ]]; then
    log_fatal \
      "app runtime GitOps is enabled but no runtime workloads were found in execute mode; see artifacts/apps/apps_smoke.env"
  fi
  log_info "apps smoke passed"
  exit 0
fi

if [[ ! -f "$manifest" ]]; then
  log_fatal "missing app manifest: $manifest"
fi
if [[ ! -f "$versions_lock" ]]; then
  log_fatal "missing app versions lock: $versions_lock"
fi

run_cmd python3 "$ROOT_DIR/scripts/lib/platform/apps/catalog_scaffold_renderer.py" validate \
  --manifest-path "$manifest" \
  --app-runtime-gitops-enabled "$app_runtime_gitops_enabled" \
  --observability-enabled "$OBSERVABILITY_ENABLED_NORMALIZED"

state_file="$(
  write_state_file "apps_smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "app_catalog_scaffold_enabled=true" \
    "app_runtime_gitops_enabled=$app_runtime_gitops_enabled" \
    "app_runtime_min_workloads=$app_runtime_min_workloads" \
    "runtime_workload_check_required=$runtime_workload_check_required" \
    "runtime_workload_check_mode=$runtime_workload_check_mode" \
    "runtime_workload_check_reason=$runtime_workload_check_reason" \
    "runtime_workload_observed_count=$runtime_workload_observed_count" \
    "manifest_path=$manifest" \
    "versions_lock_path=$versions_lock" \
    "check_mode=enabled" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps smoke state written to $state_file"
if [[ "$runtime_workload_check_failed" -ne 0 ]]; then
  log_fatal \
    "app runtime GitOps is enabled but no runtime workloads were found in execute mode; see artifacts/apps/apps_smoke.env"
fi
log_info "apps smoke passed"
