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

ensure_dir "$ROOT_DIR/apps/backend"
ensure_dir "$ROOT_DIR/apps/touchpoints"
ensure_dir "$ROOT_DIR/apps/catalog"

manifest_content=$'schemaVersion: v1\nappVersionContract:\n  appVersionEnv: APP_VERSION\n  appBuildIdEnv: APP_BUILD_ID\n  appReleaseEnv: APP_RELEASE\nruntimePinnedVersions:\n  python: '"$PYTHON_RUNTIME_BASE_IMAGE_VERSION"$'\n  node: '"$NODE_RUNTIME_BASE_IMAGE_VERSION"$'\n  nginx: '"$NGINX_RUNTIME_BASE_IMAGE_VERSION"$'\nframeworkPinnedVersions:\n  fastapi: '"$FASTAPI_VERSION"$'\n  pydantic: '"$PYDANTIC_VERSION"$'\n  vue: '"$VUE_VERSION"$'\n  pinia: '"$PINIA_VERSION"$'\n'
# Keep observability wiring explicit in the app catalog contract so runtime consumers
# (backend/UI) can be configured consistently from one canonical source.
if is_module_enabled observability; then
  observability_init_env
  manifest_content+=$'observabilityRuntimeContract:\n  enabled: true\n  otel:\n    endpoint: '"$OTEL_EXPORTER_OTLP_ENDPOINT"$'\n    protocol: '"$OTEL_PROTOCOL"$'\n    tracesEnabled: '"$OTEL_TRACES_ENABLED"$'\n    metricsEnabled: '"$OTEL_METRICS_ENABLED"$'\n    logsEnabled: '"$OTEL_LOGS_ENABLED"$'\n  faro:\n    enabled: '"$FARO_ENABLED"$'\n    collectPath: '"$FARO_COLLECT_PATH"$'\n'
else
  manifest_content+=$'observabilityRuntimeContract:\n  enabled: false\n  otel:\n    endpoint: ""\n    protocol: ""\n    tracesEnabled: false\n    metricsEnabled: false\n    logsEnabled: false\n  faro:\n    enabled: false\n    collectPath: ""\n'
fi
versions_content=$'PYTHON_RUNTIME_BASE_IMAGE_VERSION='"$PYTHON_RUNTIME_BASE_IMAGE_VERSION"$'\nNODE_RUNTIME_BASE_IMAGE_VERSION='"$NODE_RUNTIME_BASE_IMAGE_VERSION"$'\nNGINX_RUNTIME_BASE_IMAGE_VERSION='"$NGINX_RUNTIME_BASE_IMAGE_VERSION"$'\nFASTAPI_VERSION='"$FASTAPI_VERSION"$'\nPYDANTIC_VERSION='"$PYDANTIC_VERSION"$'\nVUE_VERSION='"$VUE_VERSION"$'\nPINIA_VERSION='"$PINIA_VERSION"$'\n'

printf '%s' "$manifest_content" >"$ROOT_DIR/apps/catalog/manifest.yaml"
printf '%s' "$versions_content" >"$ROOT_DIR/apps/catalog/versions.lock"

state_file="$(
  write_state_file "apps_bootstrap" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "observability_module_enabled=$(is_module_enabled observability && echo true || echo false)" \
    "otel_endpoint=${OTEL_EXPORTER_OTLP_ENDPOINT:-}" \
    "faro_collect_path=${FARO_COLLECT_PATH:-}" \
    "app_manifest=$ROOT_DIR/apps/catalog/manifest.yaml" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps bootstrap state written to $state_file"
log_info "apps bootstrap complete"
