#!/usr/bin/env bash
set -euo pipefail

SCRIPT_SHELL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_SHELL_LIB_DIR/logging.sh"
source "$SCRIPT_SHELL_LIB_DIR/utils.sh"

run_cmd() {
  printf '+ %s\n' "$*"
  "$@"
}

# run_cmd_capture: captures stdout only. stderr from the subprocess passes
# through to the shell's stderr unmodified and is directly visible to the
# caller. Safe for output-parsing and file-redirect call sites.
run_cmd_capture() {
  local output
  output="$("$@")" || {
    printf '%s\n' "$output" >&2
    return 1
  }
  printf '%s\n' "$output"
}

now_epoch_seconds() {
  date +%s
}

emit_script_duration_metric() {
  local script_name="$1"
  local start_epoch="$2"
  local exit_code="${3:-0}"
  local end_epoch duration_seconds status
  end_epoch="$(now_epoch_seconds)"
  duration_seconds=$((end_epoch - start_epoch))
  if [[ "$exit_code" -eq 0 ]]; then
    status="success"
  else
    status="failure"
  fi
  log_metric "script_duration_seconds" "$duration_seconds" "script=${script_name} status=${status}"
}

start_script_metric_trap() {
  local script_name="$1"
  local script_start_epoch
  script_start_epoch="$(now_epoch_seconds)"
  trap "rc=\$?; emit_script_duration_metric \"$script_name\" \"$script_start_epoch\" \"\$rc\"" EXIT
}

shell_has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

shell_require_cmd() {
  local cmd="$1"
  if shell_has_cmd "$cmd"; then
    return 0
  fi
  log_error "required command not found: $cmd"
  return 1
}

shell_require_cmds() {
  local cmd
  for cmd in "$@"; do
    shell_require_cmd "$cmd" || return 1
  done
}

shell_run_make_target() {
  local make_bin="$1"
  local target="$2"
  shift 2 || true
  if (($#)); then
    env "$@" "$make_bin" --no-print-directory "$target"
    return 0
  fi
  "$make_bin" --no-print-directory "$target"
}
