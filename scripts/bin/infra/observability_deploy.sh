#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/observability.sh"

start_script_metric_trap "infra_observability_deploy"

if ! is_module_enabled observability; then
  log_info "OBSERVABILITY_ENABLED=false; skipping observability deploy"
  exit 0
fi

if ! state_file_exists observability_runtime; then
  log_fatal "missing observability runtime artifact; run infra-observability-apply first"
fi

observability_init_env
deploy_path="$(argocd_optional_manifest "observability")"
run_manifest_apply "$deploy_path"

state_file="$(
  write_state_file "observability_deploy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "deploy_driver=argocd_optional_manifest" \
    "deploy_path=$deploy_path" \
    "otel_endpoint=$OTEL_EXPORTER_OTLP_ENDPOINT" \
    "faro_collect_path=$FARO_COLLECT_PATH" \
    "health_status=Healthy" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "observability deploy state written to $state_file"
