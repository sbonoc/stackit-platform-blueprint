#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/docs/site.sh"

start_script_metric_trap "docs_run"

log_info "building docs before starting local docs server"
run_cmd make -C "$ROOT_DIR" docs-build
docs_pnpm_start
