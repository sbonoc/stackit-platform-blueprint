#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/docs/site.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "docs_build"
set_state_namespace docs

require_command python3
run_cmd "$ROOT_DIR/scripts/lib/docs/generate_contract_docs.py" \
  --contract "blueprint/contract.yaml" \
  --modules-dir "blueprint/modules" \
  --output "docs/reference/generated/contract_metadata.generated.md"

docs_pnpm_build

state_file="$(
  write_state_file "docs_build" \
    "output=docs/reference/generated/contract_metadata.generated.md" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "docs build state written to $state_file"
log_info "docs build complete"
