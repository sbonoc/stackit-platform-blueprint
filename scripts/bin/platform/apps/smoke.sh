#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

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

if [[ "$app_catalog_scaffold_enabled" != "true" ]]; then
  state_file="$(
    write_state_file "apps_smoke" \
      "profile=$BLUEPRINT_PROFILE" \
      "stack=$(active_stack)" \
      "app_catalog_scaffold_enabled=false" \
      "manifest_path=none" \
      "versions_lock_path=none" \
      "check_mode=skipped" \
      "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  )"
  log_info "app catalog scaffold disabled; skipping apps/catalog smoke assertions"
  log_info "apps smoke state written to $state_file"
  log_info "apps smoke passed"
  exit 0
fi

if [[ ! -f "$manifest" ]]; then
  log_fatal "missing app manifest: $manifest"
fi
if [[ ! -f "$versions_lock" ]]; then
  log_fatal "missing app versions lock: $versions_lock"
fi

required_manifest_keys=(
  "schemaVersion:"
  "appVersionContract:"
  "runtimePinnedVersions:"
  "frameworkPinnedVersions:"
  "observabilityRuntimeContract:"
)

for key in "${required_manifest_keys[@]}"; do
  if ! grep -q "$key" "$manifest"; then
    log_fatal "manifest key missing ($key): $manifest"
  fi
done

if is_module_enabled observability; then
  if ! grep -q 'enabled: true' "$manifest"; then
    log_fatal "observabilityRuntimeContract.enabled must be true when OBSERVABILITY_ENABLED=true"
  fi
  if ! grep -q 'endpoint: http' "$manifest"; then
    log_fatal "observabilityRuntimeContract.otel.endpoint must be set when observability is enabled"
  fi
else
  if ! grep -q 'enabled: false' "$manifest"; then
    log_fatal "observabilityRuntimeContract.enabled must be false when OBSERVABILITY_ENABLED=false"
  fi
fi

state_file="$(
  write_state_file "apps_smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "app_catalog_scaffold_enabled=true" \
    "manifest_path=$manifest" \
    "versions_lock_path=$versions_lock" \
    "check_mode=enabled" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps smoke state written to $state_file"
log_info "apps smoke passed"
