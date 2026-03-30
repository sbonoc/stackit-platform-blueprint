#!/usr/bin/env bash
set -euo pipefail

SCRIPT_SHELL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${ROOT_DIR:-}" ]]; then
  ROOT_DIR="$(cd "$SCRIPT_SHELL_LIB_DIR/../.." && pwd)"
fi
export ROOT_DIR

source "$SCRIPT_SHELL_LIB_DIR/utils.sh"
source "$SCRIPT_SHELL_LIB_DIR/logging.sh"
source "$SCRIPT_SHELL_LIB_DIR/exec.sh"

require_command() {
  local cmd="$1"
  if ! shell_has_cmd "$cmd"; then
    log_fatal "required command not found: $cmd"
  fi
}

warn_if_missing_command() {
  local cmd="$1"
  if shell_has_cmd "$cmd"; then
    return 0
  fi
  log_warn "optional command not found: $cmd"
  return 1
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

load_env_file_defaults() {
  local env_file="$1"
  if [[ ! -f "$env_file" ]]; then
    return 0
  fi

  local -a existing_names=()
  local -a existing_values=()
  local var_name
  while IFS= read -r var_name; do
    [[ -n "$var_name" ]] || continue
    if [[ -n "${!var_name+x}" ]]; then
      existing_names+=("$var_name")
      existing_values+=("${!var_name}")
    fi
  done < <(sed -nE 's/^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=.*/\1/p' "$env_file")

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  local idx
  for idx in "${!existing_names[@]}"; do
    export "${existing_names[$idx]}=${existing_values[$idx]}"
  done
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
