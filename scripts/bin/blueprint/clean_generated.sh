#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_clean_generated"

usage() {
  cat <<'USAGE'
Usage: clean_generated.sh

Removes generated runtime/build/cache artifacts without touching tracked source files:
- artifacts/* state snapshots
- Python test caches (__pycache__, .pytest_cache)
- Docusaurus build/runtime caches (docs/build, docs/.docusaurus, docs/node_modules)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

removed_count=0

remove_path_if_exists() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    return 0
  fi
  if [[ -d "$path" ]]; then
    run_cmd rm -rf "$path"
  else
    run_cmd rm -f "$path"
  fi
  removed_count=$((removed_count + 1))
}

remove_path_if_exists "$ROOT_DIR/artifacts"
remove_path_if_exists "$ROOT_DIR/.pytest_cache"
remove_path_if_exists "$ROOT_DIR/docs/build"
remove_path_if_exists "$ROOT_DIR/docs/.docusaurus"
remove_path_if_exists "$ROOT_DIR/docs/node_modules"

while IFS= read -r cache_dir; do
  remove_path_if_exists "$cache_dir"
done < <(find "$ROOT_DIR/tests" -type d -name '__pycache__' | sort)

log_metric "blueprint_clean_generated_removed_path_count" "$removed_count"
log_info "blueprint clean-generated complete removed_paths=$removed_count"
