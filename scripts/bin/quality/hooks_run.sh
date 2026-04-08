#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "quality_hooks_run"

usage() {
  cat <<'EOF'
Usage: hooks_run.sh

Runs the full quality gate by composing:
- `hooks_fast.sh`
- `hooks_strict.sh`
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "quality hooks run start"
run_cmd "$ROOT_DIR/scripts/bin/quality/hooks_fast.sh"
run_cmd "$ROOT_DIR/scripts/bin/quality/hooks_strict.sh"
log_info "quality hooks run completed"
