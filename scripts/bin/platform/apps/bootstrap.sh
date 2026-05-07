#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/observability.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/platform/apps/versions.sh"

start_script_metric_trap "apps_bootstrap"
set_state_namespace apps

usage() {
  cat <<'EOF'
Usage: bootstrap.sh

Bootstraps app layer baseline:
- creates canonical app skeleton directories,
- materializes pinned versions manifest (if missing),
- persists app bootstrap state under artifacts/apps.
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

backend_runtime_image="python:${PYTHON_RUNTIME_BASE_IMAGE_VERSION}"
touchpoints_runtime_image="nginx:${NGINX_RUNTIME_BASE_IMAGE_VERSION}"

ensure_dir "$ROOT_DIR/apps/backend"
ensure_dir "$ROOT_DIR/apps/touchpoints"
manifest_path="none"
versions_lock_path="none"
if [[ "$app_catalog_scaffold_enabled" == "true" ]]; then
  ensure_dir "$ROOT_DIR/apps/catalog"
  manifest_path="$ROOT_DIR/apps/catalog/manifest.yaml"
  versions_lock_path="$ROOT_DIR/apps/catalog/versions.lock"
  observability_enabled_literal=""
  otel_exporter_otlp_endpoint=""
  otel_protocol=""
  otel_traces_enabled=""
  otel_metrics_enabled=""
  otel_logs_enabled=""
  faro_enabled=""
  faro_collect_path=""
  if is_module_enabled observability; then
    observability_init_env
    observability_enabled_literal="true"
    otel_exporter_otlp_endpoint="$OTEL_EXPORTER_OTLP_ENDPOINT"
    otel_protocol="$OTEL_PROTOCOL"
    otel_traces_enabled="$OTEL_TRACES_ENABLED"
    otel_metrics_enabled="$OTEL_METRICS_ENABLED"
    otel_logs_enabled="$OTEL_LOGS_ENABLED"
    faro_enabled="$FARO_ENABLED"
    faro_collect_path="$FARO_COLLECT_PATH"
  else
    observability_enabled_literal="false"
    otel_exporter_otlp_endpoint=""
    otel_protocol=""
    otel_traces_enabled="false"
    otel_metrics_enabled="false"
    otel_logs_enabled="false"
    faro_enabled="false"
    faro_collect_path=""
  fi

  run_cmd python3 "$ROOT_DIR/scripts/lib/platform/apps/catalog_scaffold_renderer.py" render \
    --manifest-template "$ROOT_DIR/scripts/templates/platform/apps/catalog/manifest.yaml.tmpl" \
    --versions-template "$ROOT_DIR/scripts/templates/platform/apps/catalog/versions.lock.tmpl" \
    --manifest-output "$manifest_path" \
    --versions-output "$versions_lock_path" \
    --python-runtime-base-image-version "$PYTHON_RUNTIME_BASE_IMAGE_VERSION" \
    --node-runtime-base-image-version "$NODE_RUNTIME_BASE_IMAGE_VERSION" \
    --nginx-runtime-base-image-version "$NGINX_RUNTIME_BASE_IMAGE_VERSION" \
    --fastapi-version "$FASTAPI_VERSION" \
    --pydantic-version "$PYDANTIC_VERSION" \
    --vue-version "$VUE_VERSION" \
    --vue-router-version "$VUE_ROUTER_VERSION" \
    --pinia-version "$PINIA_VERSION" \
    --app-runtime-gitops-enabled "$app_runtime_gitops_enabled" \
    --app-descriptor-path "$ROOT_DIR/apps/descriptor.yaml" \
    --component-image "backend-api=$backend_runtime_image" \
    --component-image "touchpoints-web=$touchpoints_runtime_image" \
    --component-image-env-var "backend-api=APP_RUNTIME_BACKEND_IMAGE" \
    --component-image-env-var "touchpoints-web=APP_RUNTIME_TOUCHPOINTS_IMAGE" \
    --observability-enabled "$observability_enabled_literal" \
    --otel-exporter-otlp-endpoint "$otel_exporter_otlp_endpoint" \
    --otel-protocol "$otel_protocol" \
    --otel-traces-enabled "$otel_traces_enabled" \
    --otel-metrics-enabled "$otel_metrics_enabled" \
    --otel-logs-enabled "$otel_logs_enabled" \
    --faro-enabled "$faro_enabled" \
    --faro-collect-path "$faro_collect_path"
else
  log_info "app catalog scaffold disabled; skipping apps/catalog manifest and lock generation"
fi

state_file="$(
  write_state_file "apps_bootstrap" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "app_catalog_scaffold_enabled=$app_catalog_scaffold_enabled" \
    "app_runtime_gitops_enabled=$app_runtime_gitops_enabled" \
    "app_runtime_backend_image=$backend_runtime_image" \
    "app_runtime_touchpoints_image=$touchpoints_runtime_image" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "observability_module_enabled=$(is_module_enabled observability && echo true || echo false)" \
    "otel_endpoint=${OTEL_EXPORTER_OTLP_ENDPOINT:-}" \
    "faro_collect_path=${FARO_COLLECT_PATH:-}" \
    "app_manifest=$manifest_path" \
    "app_versions_lock=$versions_lock_path" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps bootstrap state written to $state_file"
log_info "apps bootstrap complete"
