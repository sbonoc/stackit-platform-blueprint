#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_render_module_wrapper_skeletons"

usage() {
  cat <<'USAGE'
Usage: render_module_wrapper_skeletons.sh

Renders optional-module wrapper skeleton templates from blueprint module contracts into:
scripts/templates/infra/module_wrappers/<module>/*.sh.tmpl
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
run_cmd "$ROOT_DIR/scripts/lib/blueprint/generate_module_wrapper_skeletons.py" \
  --modules-dir "blueprint/modules" \
  --output-root "scripts/templates/infra/module_wrappers"

log_info "optional-module wrapper skeleton templates rendered"
