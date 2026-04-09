#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/docs/site.sh"

start_script_metric_trap "docs_install"

require_command python3
chmod +x "$ROOT_DIR/scripts/lib/docs/generate_contract_docs.py"
docs_pnpm_install

log_info "docs install complete"
