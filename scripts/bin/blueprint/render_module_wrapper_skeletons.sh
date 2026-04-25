#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_render_module_wrapper_skeletons"

usage() {
  cat <<'USAGE'
Usage: render_module_wrapper_skeletons.sh

Renders optional-module wrapper skeleton templates from blueprint module contracts into:
scripts/templates/infra/module_wrappers/<module>/*.sh.tmpl

This script reads blueprint/modules/*/module.contract.yaml, which is a source-only
path pruned by blueprint-init-repo in generated-consumer repos.  The script is a
no-op in generated-consumer mode; the pre-rendered templates committed to the
template-source repo are consumed directly by generated consumers without regeneration.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# blueprint/modules/ is declared source_only in blueprint/contract.yaml and is
# removed by blueprint-init-repo when converting a template-source repo to a
# generated-consumer repo.  Attempting to render wrapper skeletons without the
# module contracts would fail with "no module contracts found".  The output
# templates (scripts/templates/infra/module_wrappers/) are already committed to
# the template-source repo and are available to generated consumers unchanged.
if blueprint_repo_is_generated_consumer; then
  log_metric "blueprint_render_module_wrapper_skeletons_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping render_module_wrapper_skeletons in generated-consumer repo (blueprint/modules is source-only)"
  exit 0
fi

require_command python3
run_cmd "$ROOT_DIR/scripts/lib/blueprint/generate_module_wrapper_skeletons.py" \
  --modules-dir "blueprint/modules" \
  --output-root "scripts/templates/infra/module_wrappers"

log_metric "blueprint_render_module_wrapper_skeletons_total" "1" "status=success repo_mode=template-source"
log_info "optional-module wrapper skeleton templates rendered"
