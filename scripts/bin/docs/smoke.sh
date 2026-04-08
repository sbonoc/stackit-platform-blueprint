#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "docs_smoke"
set_state_namespace docs

generated_doc="$ROOT_DIR/docs/reference/generated/contract_metadata.generated.md"
if [[ ! -f "$generated_doc" ]]; then
  log_fatal "missing generated docs file: $generated_doc"
fi

required_markers=(
  "# Contract Metadata (Generated)"
  "## Supported Profiles"
  "## Required Make Targets"
  "## Optional Modules"
  "## Module: \`observability\`"
  "## Module: \`workflows\`"
  "## Module: \`langfuse\`"
  "## Module: \`postgres\`"
  "## Module: \`neo4j\`"
)

for marker in "${required_markers[@]}"; do
  if ! grep -qF "$marker" "$generated_doc"; then
    log_fatal "generated docs marker missing: $marker"
  fi
done

if ! grep -qF "## Contract Summary" "$ROOT_DIR/docs/platform/modules/postgres/README.md"; then
  log_fatal "module contract summary block missing in docs/platform/modules/postgres/README.md"
fi

docs_build_index="$ROOT_DIR/docs/build/index.html"
if [[ ! -f "$docs_build_index" ]]; then
  log_fatal "missing docs static build artifact: $docs_build_index (run make docs-build first)"
fi

state_file="$(
  write_state_file "docs_smoke" \
    "status=passed" \
    "output=docs/reference/generated/contract_metadata.generated.md" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "docs smoke state written to $state_file"
