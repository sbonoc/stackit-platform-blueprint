#!/usr/bin/env bash
set -euo pipefail

_discover_python_tests_in_path() {
  local path="$1"
  if [[ -f "$path" ]]; then
    case "$(basename "$path")" in
    test_*.py | *_test.py)
      printf '%s\n' "$path"
      ;;
    esac
    return 0
  fi

  if [[ -d "$path" ]]; then
    find "$path" -type f \( -name 'test_*.py' -o -name '*_test.py' \) | sort
  fi
}

run_python_pytest_lane() {
  local lane="$1"
  shift || true
  local lane_start_epoch
  lane_start_epoch="$(now_epoch_seconds)"
  local lane_slug
  lane_slug="${lane// /_}"

  if [[ "$#" -eq 0 ]]; then
    log_fatal "run_python_pytest_lane requires at least one path"
  fi

  local discovered=()
  local path
  local candidate
  for path in "$@"; do
    while IFS= read -r candidate; do
      [[ -n "$candidate" ]] || continue
      discovered+=("$candidate")
    done < <(_discover_python_tests_in_path "$path")
  done

  if [[ "${#discovered[@]}" -eq 0 ]]; then
    log_info "no ${lane} pytest files discovered; skipping"
    log_metric "pytest_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} status=skipped discovered_tests=0"
    return 0
  fi

  log_info "running ${lane} pytest lane with ${#discovered[@]} discovered test file(s)"
  require_command python3
  if ! run_cmd python3 -m pytest -q "${discovered[@]}"; then
    log_metric "pytest_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} status=failure discovered_tests=${#discovered[@]}"
    return 1
  fi
  log_metric "pytest_lane_duration_seconds" \
    "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
    "lane=${lane_slug} status=success discovered_tests=${#discovered[@]}"
}
