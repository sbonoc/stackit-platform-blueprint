#!/usr/bin/env bash
set -euo pipefail

SCRIPT_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_LIB_DIR/../.." && pwd)"
export ROOT_DIR

source "$SCRIPT_LIB_DIR/logging.sh"
source "$SCRIPT_LIB_DIR/runner.sh"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_fatal "required command not found: $cmd"
  fi
}

warn_if_missing_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_warn "optional command not found: $cmd"
    return 1
  fi
}

ensure_dir() {
  local dir="$1"
  mkdir -p "$dir"
}

ensure_file_with_content() {
  local path="$1"
  local content="$2"
  if [[ -f "$path" ]]; then
    return 0
  fi
  mkdir -p "$(dirname "$path")"
  printf '%s' "$content" >"$path"
  log_info "created $path"
}

set_default_env() {
  local var_name="$1"
  local default_value="$2"
  if [[ -z "${!var_name:-}" ]]; then
    export "$var_name=$default_value"
  fi
}

require_env_vars() {
  local missing=0
  local var_name
  for var_name in "$@"; do
    if [[ -z "${!var_name:-}" ]]; then
      log_error "required env var is missing: $var_name"
      missing=$((missing + 1))
    fi
  done
  if [[ "$missing" -gt 0 ]]; then
    log_fatal "$missing required environment variable(s) missing"
  fi
}
