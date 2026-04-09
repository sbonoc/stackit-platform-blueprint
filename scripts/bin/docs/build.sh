#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/docs/site.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "docs_build"
set_state_namespace docs

require_command python3
run_cmd python3 "$ROOT_DIR/scripts/bin/quality/render_core_targets_doc.py"
run_cmd python3 "$ROOT_DIR/scripts/lib/docs/generate_contract_docs.py" \
  --contract "blueprint/contract.yaml" \
  --modules-dir "blueprint/modules" \
  --output "docs/reference/generated/contract_metadata.generated.md"
run_cmd python3 "$ROOT_DIR/scripts/lib/docs/sync_module_contract_summaries.py"

docs_pnpm_build

state_file="$(
  write_state_file "docs_build" \
    "output_core_targets=docs/reference/generated/core_targets.generated.md" \
    "output_contract_metadata=docs/reference/generated/contract_metadata.generated.md" \
    "output_module_contract_summaries=docs/platform/modules/*/README.md" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "docs build state written to $state_file"
log_info "docs build complete"
