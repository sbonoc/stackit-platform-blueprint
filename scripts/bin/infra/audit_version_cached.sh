#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/quality/audit_cache.sh"

start_script_metric_trap "infra_audit_version_cached"

usage() {
  cat <<'USAGE'
Usage: audit_version_cached.sh

Runs infra version audit with local success cache.

Environment variables:
  INFRA_AUDIT_CACHE_ENABLED      true|false (default: true)
  INFRA_AUDIT_CACHE_FORCE        true|false (default: false)
  INFRA_AUDIT_CACHE_TTL_SECONDS  Cache TTL in seconds (default: 21600)
  INFRA_AUDIT_CACHE_FILE         Cache metadata file path
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

set_default_env INFRA_AUDIT_CACHE_ENABLED "true"
set_default_env INFRA_AUDIT_CACHE_FORCE "false"
set_default_env INFRA_AUDIT_CACHE_TTL_SECONDS "21600"
set_default_env INFRA_AUDIT_CACHE_FILE "${XDG_CACHE_HOME:-$HOME/.cache}/stackit-platform-blueprint/infra_audit_version.cache"

INFRA_AUDIT_CACHE_ENABLED="$(normalize_bool "$INFRA_AUDIT_CACHE_ENABLED")"
INFRA_AUDIT_CACHE_FORCE="$(normalize_bool "$INFRA_AUDIT_CACHE_FORCE")"

fingerprint_files=(
  "scripts/bin/infra/audit_version.sh"
  "scripts/lib/infra/versions.sh"
  "scripts/lib/infra/versions.baseline.sh"
  "scripts/lib/semver.sh"
)

audit_cache_run \
  "infra-audit-version" \
  "$ROOT_DIR/scripts/bin/infra/audit_version.sh" \
  "$INFRA_AUDIT_CACHE_FILE" \
  "$INFRA_AUDIT_CACHE_TTL_SECONDS" \
  "$INFRA_AUDIT_CACHE_ENABLED" \
  "$INFRA_AUDIT_CACHE_FORCE" \
  "${fingerprint_files[@]}"
