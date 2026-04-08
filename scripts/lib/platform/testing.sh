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

_discover_pnpm_script_project_entries() {
  local root_path="$1"
  shift

  if [[ ! -d "$root_path" ]]; then
    return 0
  fi

  if [[ "$#" -eq 0 ]]; then
    log_fatal "_discover_pnpm_script_project_entries requires at least one script name candidate"
  fi

  require_command python3
  python3 "$ROOT_DIR/scripts/lib/platform/pnpm_script_discovery.py" "$root_path" "$@"
}

_run_touchpoints_pnpm_script() {
  local package_dir="$1"
  local selected_script="$2"
  run_cmd env -u NO_COLOR pnpm --dir "$package_dir" run "$selected_script"
}

run_touchpoints_pnpm_lane() {
  if [[ "$#" -lt 4 ]]; then
    log_fatal "run_touchpoints_pnpm_lane requires lane, runner, root path, and at least one script name candidate"
  fi

  local lane="$1"
  local runner="$2"
  local touchpoints_root="$3"
  shift 3

  local lane_start_epoch
  lane_start_epoch="$(now_epoch_seconds)"
  local lane_slug
  lane_slug="${lane// /_}"
  local no_color_sanitized="false"
  if [[ -n "${NO_COLOR+x}" ]]; then
    no_color_sanitized="true"
    log_info "touchpoints ${lane_slug} lane unsetting NO_COLOR for pnpm child process execution"
  fi

  if [[ ! -d "$touchpoints_root" ]]; then
    log_info "touchpoints root not found; skipping ${lane} lane path=$touchpoints_root"
    log_metric "pnpm_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} runner=${runner} status=skipped discovered_packages=0 script=none no_color_sanitized=${no_color_sanitized}"
    return 0
  fi

  local discovered=()
  local discovered_entry
  local package_dir
  local selected_script
  while IFS=$'\t' read -r package_dir selected_script; do
    [[ -n "$package_dir" ]] || continue
    [[ -n "$selected_script" ]] || continue
    discovered+=("${package_dir}"$'\t'"${selected_script}")
  done < <(_discover_pnpm_script_project_entries "$touchpoints_root" "$@")

  if [[ "${#discovered[@]}" -eq 0 ]]; then
    log_info "no touchpoints pnpm script discovered for ${lane}; skipping"
    log_metric "pnpm_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} runner=${runner} status=skipped discovered_packages=0 script=none no_color_sanitized=${no_color_sanitized}"
    return 0
  fi

  require_command pnpm
  log_info "running ${lane} ${runner} lane with per-package script discovery for ${#discovered[@]} package(s)"

  for discovered_entry in "${discovered[@]}"; do
    package_dir="${discovered_entry%%$'\t'*}"
    selected_script="${discovered_entry#*$'\t'}"
    if ! _run_touchpoints_pnpm_script "$package_dir" "$selected_script"; then
      log_metric "pnpm_lane_duration_seconds" \
        "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
        "lane=${lane_slug} runner=${runner} status=failure discovered_packages=${#discovered[@]} script_mode=per_package no_color_sanitized=${no_color_sanitized}"
      return 1
    fi
  done

  log_metric "pnpm_lane_duration_seconds" \
    "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
    "lane=${lane_slug} runner=${runner} status=success discovered_packages=${#discovered[@]} script_mode=per_package no_color_sanitized=${no_color_sanitized}"
}
