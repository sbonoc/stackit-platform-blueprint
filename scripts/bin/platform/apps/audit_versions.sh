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

log_audit_metric() {
  local var_name="$1"
  local status="$2"
  shift 2 || true
  if (($#)); then
    log_metric "apps_version_pin_audit_total" "1" "variable=$var_name status=$status $*"
    return 0
  fi
  log_metric "apps_version_pin_audit_total" "1" "variable=$var_name status=$status"
}

audit_var() {
  local var_name="$1"
  local current baseline
  current="${!var_name:-}"
  baseline="$(
    source "$ROOT_DIR/scripts/lib/platform/apps/versions.baseline.sh"
    printf '%s' "${!var_name:-}"
  )"

  if [[ -z "$current" ]]; then
    log_audit_metric "$var_name" "missing"
    log_error "missing pinned version for $var_name"
    failures=$((failures + 1))
    return
  fi
  if [[ "$current" == "latest" ]]; then
    log_audit_metric "$var_name" "unpinned_latest" "current=$current"
    log_error "unpinned value is forbidden for $var_name"
    failures=$((failures + 1))
    return
  fi
  if [[ -z "$baseline" ]]; then
    log_audit_metric "$var_name" "missing_baseline" "current=$current"
    log_warn "no baseline defined for $var_name; skipping drift check"
    warnings=$((warnings + 1))
    return
  fi

  local drift
  drift="$(classify_semver_drift "$current" "$baseline")"
  case "$drift" in
  same)
    log_audit_metric "$var_name" "same" "current=$current baseline=$baseline"
    ;;
  patch | major)
    log_audit_metric "$var_name" "${drift}_drift" "current=$current baseline=$baseline"
    log_error "$drift drift detected for $var_name: current=$current baseline=$baseline"
    failures=$((failures + 1))
    ;;
  minor)
    log_audit_metric "$var_name" "minor_drift" "current=$current baseline=$baseline"
    log_warn "minor drift detected for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  non-semver)
    log_audit_metric "$var_name" "non_semver" "current=$current baseline=$baseline"
    log_warn "non-semver drift comparison for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  *)
    log_audit_metric "$var_name" "unknown_drift" "current=$current baseline=$baseline drift=$drift"
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
  VUE_ROUTER_VERSION
  PINIA_VERSION
)

for var_name in "${tracked_vars[@]}"; do
  audit_var "$var_name"
done

contract_checks_run=0
contract_failures=0
catalog_lock="$ROOT_DIR/apps/catalog/versions.lock"
catalog_manifest="$ROOT_DIR/apps/catalog/manifest.yaml"

if [[ -f "$catalog_lock" || -f "$catalog_manifest" ]]; then
  contract_checker_args=(--mode catalog-check)
  [[ -f "$catalog_lock" ]] && contract_checker_args+=(--versions-lock "$catalog_lock")
  [[ -f "$catalog_manifest" ]] && contract_checker_args+=(--manifest "$catalog_manifest")
  for var_name in "${tracked_vars[@]}"; do
    contract_checker_args+=(--var "$var_name=${!var_name}")
  done
  contract_checks_run=1
  if ! run_cmd python3 "$ROOT_DIR/scripts/lib/platform/apps/version_contract_checker.py" \
      "${contract_checker_args[@]}"; then
    contract_failures=1
    failures=$((failures + 1))
  fi
fi
log_metric "apps_version_contract_check_total" "$contract_checks_run" \
  "status=$([ "$contract_failures" -eq 0 ] && echo success || echo failure)"

summary_status="success"
if [[ $warnings -gt 0 ]]; then
  summary_status="warning"
fi
if [[ $failures -gt 0 ]]; then
  summary_status="failure"
fi
log_metric \
  "apps_version_audit_summary_total" \
  "1" \
  "tracked=${#tracked_vars[@]} warnings=$warnings failures=$failures contract_checks=$contract_checks_run contract_failures=$contract_failures status=$summary_status"

if [[ $warnings -gt 0 ]]; then
  log_warn "apps version audit completed with $warnings warning(s)"
fi
if [[ $failures -gt 0 ]]; then
  log_fatal "apps version audit failed with $failures failure(s)"
fi

log_info "apps version audit passed"
