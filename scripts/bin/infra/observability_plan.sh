#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/observability.sh"

start_script_metric_trap "infra_observability_plan"

if ! is_module_enabled observability; then
  log_info "OBSERVABILITY_ENABLED=false; skipping observability plan"
  exit 0
fi

observability_init_env
provision_driver="none"
provision_path="none"

if is_stackit_profile; then
  provision_driver="foundation_contract"
  provision_path="$(stackit_terraform_layer_dir foundation)"
  if ! state_file_exists stackit_foundation_plan && ! state_file_exists stackit_foundation_apply; then
    log_warn "STACKIT foundation plan/apply state not found; run infra-stackit-foundation-plan for full terraform diff"
  fi
elif is_local_profile; then
  provision_driver="crossplane_plus_helm"
  provision_path="$(local_crossplane_kustomize_dir)"
  run_helm_template \
    "blueprint-observability" \
    "$OBSERVABILITY_NAMESPACE" \
    "grafana/k8s-monitoring" \
    "$GRAFANA_CHART_VERSION" \
    "$(local_observability_values_file)"
  run_helm_template \
    "blueprint-otel-collector" \
    "$OBSERVABILITY_NAMESPACE" \
    "open-telemetry/opentelemetry-collector" \
    "$OTEL_COLLECTOR_CHART_VERSION" \
    "$(local_otel_collector_values_file)"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(
  write_state_file "observability_plan" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "provision_driver=$provision_driver" \
    "provision_path=$provision_path" \
    "otel_endpoint=$OTEL_EXPORTER_OTLP_ENDPOINT" \
    "otel_protocol=$OTEL_PROTOCOL" \
    "otel_traces_enabled=$OTEL_TRACES_ENABLED" \
    "otel_metrics_enabled=$OTEL_METRICS_ENABLED" \
    "otel_logs_enabled=$OTEL_LOGS_ENABLED" \
    "faro_enabled=$FARO_ENABLED" \
    "faro_collect_path=$FARO_COLLECT_PATH" \
    "stackit_observability_instance_id=$(observability_stackit_instance_id)" \
    "stackit_observability_grafana_url=$(observability_stackit_grafana_url)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "observability plan state written to $state_file"
