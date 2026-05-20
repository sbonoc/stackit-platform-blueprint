#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

observability_init_env() {
  set_default_env OBSERVABILITY_NAMESPACE "observability"
  set_default_env OTEL_COLLECTOR_SERVICE_DNS "otel-collector.observability.svc.cluster.local"
  set_default_env OTEL_COLLECTOR_GRPC_PORT "4317"
  set_default_env OTEL_COLLECTOR_HTTP_PORT "4318"
  set_default_env OTEL_PROTOCOL "grpc"
  set_default_env OTEL_TRACES_ENABLED "true"
  set_default_env OTEL_METRICS_ENABLED "true"
  set_default_env OTEL_LOGS_ENABLED "true"
  set_default_env FARO_COLLECT_PATH "/collect"
  set_default_env FARO_ENABLED "true"
  set_default_env OBSERVABILITY_RETENTION_DAYS "30"

  if [[ -z "${OTEL_EXPORTER_OTLP_ENDPOINT:-}" ]]; then
    export OTEL_EXPORTER_OTLP_ENDPOINT="http://${OTEL_COLLECTOR_SERVICE_DNS}:${OTEL_COLLECTOR_GRPC_PORT}"
  fi
}

observability_stackit_instance_id() {
  if [[ -n "${STACKIT_OBSERVABILITY_INSTANCE_ID:-}" ]]; then
    printf '%s' "$STACKIT_OBSERVABILITY_INSTANCE_ID"
    return 0
  fi
  printf 'stackit-observability-%s' "$(profile_environment)"
}

observability_stackit_grafana_url() {
  if [[ -n "${STACKIT_OBSERVABILITY_GRAFANA_URL:-}" ]]; then
    printf '%s' "$STACKIT_OBSERVABILITY_GRAFANA_URL"
    return 0
  fi
  printf 'https://grafana.%s.stackit.example.invalid' "$(profile_environment)"
}

observability_metrics_push_url() {
  stackit_foundation_output_value_or_default "observability_metrics_push_url" ""
}

observability_logs_push_url() {
  stackit_foundation_output_value_or_default "observability_logs_push_url" ""
}

observability_traces_push_url() {
  stackit_foundation_output_value_or_default "observability_traces_push_url" ""
}

observability_api_key() {
  printf '%s' ""
}

observability_secret_name() {
  printf 'blueprint-observability-auth'
}

observability_reconcile_runtime_secret() {
  local _username
  _username="$(stackit_foundation_output_value_or_default "observability_credential_username" "${OBSERVABILITY_USERNAME:-}")"
  apply_optional_module_secret_from_literals \
    "${OBSERVABILITY_NAMESPACE:-observability}" \
    "$(observability_secret_name)" \
    "username=${_username}" \
    "password=$(stackit_foundation_output_value_or_default "observability_credential_password" "")" \
    "METRICS_PUSH_URL=$(observability_metrics_push_url)" \
    "LOGS_PUSH_URL=$(observability_logs_push_url)" \
    "TRACES_PUSH_URL=$(observability_traces_push_url)"
}

observability_delete_runtime_secret() {
  delete_optional_module_secret "${OBSERVABILITY_NAMESPACE:-observability}" "$(observability_secret_name)"
}
