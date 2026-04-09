#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "quality_hooks_strict"

usage() {
  cat <<'EOF'
Usage: hooks_strict.sh

Runs the slower audit-focused quality gate:
- infra version audit
- apps version audit
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "quality hooks strict gate start"
run_cmd make -C "$ROOT_DIR" infra-audit-version
run_cmd make -C "$ROOT_DIR" apps-audit-versions
log_info "quality hooks strict gate completed"
