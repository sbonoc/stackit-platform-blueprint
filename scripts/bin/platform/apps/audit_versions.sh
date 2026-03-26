#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/platform/apps/versions.sh"
source "$ROOT_DIR/scripts/lib/platform/apps/versions.baseline.sh"
source "$ROOT_DIR/scripts/lib/semver.sh"

start_script_metric_trap "apps_audit_versions"

usage() {
  cat <<'EOF'
Usage: audit_versions.sh

Audits app pinned versions and checks drift against baseline policy:
- patch drift => fail
- minor drift => warn
- major drift => fail
- non-semver => warn
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

failures=0
warnings=0

audit_var() {
  local var_name="$1"
  local current baseline
  current="${!var_name:-}"
  baseline="$(
    source "$ROOT_DIR/scripts/lib/platform/apps/versions.baseline.sh"
    printf '%s' "${!var_name:-}"
  )"

  if [[ -z "$current" ]]; then
    log_error "missing pinned version for $var_name"
    failures=$((failures + 1))
    return
  fi
  if [[ "$current" == "latest" ]]; then
    log_error "unpinned value is forbidden for $var_name"
    failures=$((failures + 1))
    return
  fi
  if [[ -z "$baseline" ]]; then
    log_warn "no baseline defined for $var_name; skipping drift check"
    warnings=$((warnings + 1))
    return
  fi

  local drift
  drift="$(classify_semver_drift "$current" "$baseline")"
  case "$drift" in
  same)
    ;;
  patch | major)
    log_error "$drift drift detected for $var_name: current=$current baseline=$baseline"
    failures=$((failures + 1))
    ;;
  minor)
    log_warn "minor drift detected for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  non-semver)
    log_warn "non-semver drift comparison for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  *)
    log_error "unknown drift classification for $var_name: $drift"
    failures=$((failures + 1))
    ;;
  esac
}

tracked_vars=(
  PYTHON_RUNTIME_BASE_IMAGE_VERSION
  NODE_RUNTIME_BASE_IMAGE_VERSION
  NGINX_RUNTIME_BASE_IMAGE_VERSION
  FASTAPI_VERSION
  PYDANTIC_VERSION
  VUE_VERSION
  PINIA_VERSION
)

for var_name in "${tracked_vars[@]}"; do
  audit_var "$var_name"
done

if [[ $warnings -gt 0 ]]; then
  log_warn "apps version audit completed with $warnings warning(s)"
fi
if [[ $failures -gt 0 ]]; then
  log_fatal "apps version audit failed with $failures failure(s)"
fi

log_info "apps version audit passed"
