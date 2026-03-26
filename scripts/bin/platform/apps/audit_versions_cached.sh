#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/quality/audit_cache.sh"

start_script_metric_trap "apps_audit_versions_cached"

usage() {
  cat <<'USAGE'
Usage: audit_versions_cached.sh

Runs apps version audit with local success cache.

Environment variables:
  APPS_AUDIT_CACHE_ENABLED      true|false (default: true)
  APPS_AUDIT_CACHE_FORCE        true|false (default: false)
  APPS_AUDIT_CACHE_TTL_SECONDS  Cache TTL in seconds (default: 21600)
  APPS_AUDIT_CACHE_FILE         Cache metadata file path
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

normalize_bool() {
  local value="${1:-false}"
  case "$value" in
  1 | true | TRUE | True | yes | YES | on | ON)
    echo "true"
    ;;
  *)
    echo "false"
    ;;
  esac
}

set_default_env APPS_AUDIT_CACHE_ENABLED "true"
set_default_env APPS_AUDIT_CACHE_FORCE "false"
set_default_env APPS_AUDIT_CACHE_TTL_SECONDS "21600"
set_default_env APPS_AUDIT_CACHE_FILE "${XDG_CACHE_HOME:-$HOME/.cache}/stackit-platform-blueprint/apps_audit_versions.cache"

APPS_AUDIT_CACHE_ENABLED="$(normalize_bool "$APPS_AUDIT_CACHE_ENABLED")"
APPS_AUDIT_CACHE_FORCE="$(normalize_bool "$APPS_AUDIT_CACHE_FORCE")"

fingerprint_files=(
  "scripts/bin/platform/apps/audit_versions.sh"
  "scripts/lib/platform/apps/versions.sh"
  "scripts/lib/platform/apps/versions.baseline.sh"
  "scripts/lib/semver.sh"
)

audit_cache_run \
  "apps-audit-versions" \
  "$ROOT_DIR/scripts/bin/platform/apps/audit_versions.sh" \
  "$APPS_AUDIT_CACHE_FILE" \
  "$APPS_AUDIT_CACHE_TTL_SECONDS" \
  "$APPS_AUDIT_CACHE_ENABLED" \
  "$APPS_AUDIT_CACHE_FORCE" \
  "${fingerprint_files[@]}"
