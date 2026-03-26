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

manifest="$ROOT_DIR/apps/catalog/manifest.yaml"
versions_lock="$ROOT_DIR/apps/catalog/versions.lock"

if ! state_file_exists apps_bootstrap; then
  log_fatal "missing apps bootstrap state artifact; run make apps-bootstrap first"
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
    "manifest_path=$manifest" \
    "versions_lock_path=$versions_lock" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps smoke state written to $state_file"
log_info "apps smoke passed"
