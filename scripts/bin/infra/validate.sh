#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "infra_validate"

usage() {
  cat <<'EOF'
Usage: validate.sh

Validates repository contract conformance for:
- module-conditional make/blueprint.generated.mk materialization from blueprint template,
- required files/paths and module contracts from blueprint/contract.yaml,
- executable script/shebang contract,
- docs architecture mermaid contract,
- Makefile target/namespace contract.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
run_cmd "$ROOT_DIR/scripts/bin/blueprint/render_makefile.sh"
run_cmd "$ROOT_DIR/scripts/bin/blueprint/validate_contract.py" \
  --contract-path "$ROOT_DIR/blueprint/contract.yaml"
log_info "infra validation passed"
