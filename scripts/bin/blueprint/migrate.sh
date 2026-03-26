#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_migrate"

usage() {
  cat <<'EOF'
Usage: migrate.sh

Applies repository migrations required by the current blueprint template version.

Optional environment variables:
  BLUEPRINT_MIGRATE_SKIP_VALIDATE=true  Skip post-migration contract validation.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3

set_default_env BLUEPRINT_MIGRATE_SKIP_VALIDATE "false"

run_cmd "$ROOT_DIR/scripts/lib/blueprint/migrate_repo.py" \
  --repo-root "$ROOT_DIR"

if [[ "$BLUEPRINT_MIGRATE_SKIP_VALIDATE" != "true" ]]; then
  run_cmd "$ROOT_DIR/scripts/bin/blueprint/validate_contract.py" \
    --contract-path "$ROOT_DIR/blueprint/contract.yaml"
fi

log_info "blueprint migration complete"
