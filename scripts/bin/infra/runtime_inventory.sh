#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"

start_script_metric_trap "infra_runtime_inventory"

usage() {
  cat <<'USAGE'
Usage: runtime_inventory.sh

Profile-aware runtime inventory entrypoint:
- local-* profiles => infra-local-runtime-inventory
- stackit-* profiles => infra-stackit-runtime-inventory
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if is_stackit_profile; then
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_runtime_inventory.sh"
  exit 0
fi

if is_local_profile; then
  run_cmd "$ROOT_DIR/scripts/bin/infra/local_runtime_inventory.sh"
  exit 0
fi

log_fatal "unsupported BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset} for infra-runtime-inventory"
