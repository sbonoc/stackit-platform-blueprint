#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

start_script_metric_trap "infra_provision_deploy"

usage() {
  cat <<'EOF'
Usage: provision_deploy.sh

Runs the canonical full wrapper chain:
1) infra-provision
2) infra-deploy
3) infra-smoke
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/provision.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/deploy.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/smoke.sh"

log_info "infra provision-deploy chain complete"
