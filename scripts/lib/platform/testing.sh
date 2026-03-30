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

_discover_pnpm_script_projects() {
  local root_path="$1"
  local script_name="$2"

  if [[ ! -d "$root_path" ]]; then
    return 0
  fi

  require_command python3
  python3 - "$root_path" "$script_name" <<'PY'
import json
import pathlib
import sys

root_path = pathlib.Path(sys.argv[1])
script_name = sys.argv[2]

for package_json in sorted(root_path.rglob("package.json")):
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception:
        continue
    scripts = payload.get("scripts")
    if isinstance(scripts, dict) and isinstance(scripts.get(script_name), str):
        print(str(package_json.parent))
PY
}

run_touchpoints_pnpm_lane() {
  local lane="$1"
  local runner="$2"
  local touchpoints_root="$3"
  shift 3 || true

  local lane_start_epoch
  lane_start_epoch="$(now_epoch_seconds)"
  local lane_slug
  lane_slug="${lane// /_}"

  if [[ "$#" -eq 0 ]]; then
    log_fatal "run_touchpoints_pnpm_lane requires at least one script name candidate"
  fi

  if [[ ! -d "$touchpoints_root" ]]; then
    log_info "touchpoints root not found; skipping ${lane} lane path=$touchpoints_root"
    log_metric "pnpm_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} runner=${runner} status=skipped discovered_packages=0 script=none"
    return 0
  fi

  local selected_script=""
  local discovered=()
  local script_candidate
  local package_dir
  for script_candidate in "$@"; do
    discovered=()
    while IFS= read -r package_dir; do
      [[ -n "$package_dir" ]] || continue
      discovered+=("$package_dir")
    done < <(_discover_pnpm_script_projects "$touchpoints_root" "$script_candidate")

    if [[ "${#discovered[@]}" -gt 0 ]]; then
      selected_script="$script_candidate"
      break
    fi
  done

  if [[ -z "$selected_script" ]]; then
    log_info "no touchpoints pnpm script discovered for ${lane}; skipping"
    log_metric "pnpm_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "lane=${lane_slug} runner=${runner} status=skipped discovered_packages=0 script=none"
    return 0
  fi

  require_command pnpm
  log_info "running ${lane} ${runner} lane via script '$selected_script' for ${#discovered[@]} package(s)"

  for package_dir in "${discovered[@]}"; do
    if ! run_cmd pnpm --dir "$package_dir" run "$selected_script"; then
      log_metric "pnpm_lane_duration_seconds" \
        "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
        "lane=${lane_slug} runner=${runner} status=failure discovered_packages=${#discovered[@]} script=$selected_script"
      return 1
    fi
  done

  log_metric "pnpm_lane_duration_seconds" \
    "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
    "lane=${lane_slug} runner=${runner} status=success discovered_packages=${#discovered[@]} script=$selected_script"
}
