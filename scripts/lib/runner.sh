#!/usr/bin/env bash
set -euo pipefail

run_cmd() {
  printf '+ %s\n' "$*"
  "$@"
}

run_cmd_capture() {
  local output
  output="$("$@" 2>&1)" || {
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
