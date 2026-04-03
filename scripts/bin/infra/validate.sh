#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

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

Environment variables:
  BLUEPRINT_VALIDATE_RENDER_WITH_CONTRACT_DEFAULTS
    Default: true
    When true, module toggle env overrides are ignored while rendering
    make/blueprint.generated.mk so transient runtime flags do not mutate
    blueprint-managed tracked makefile state.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
set_default_env BLUEPRINT_VALIDATE_RENDER_WITH_CONTRACT_DEFAULTS "true"

render_with_contract_defaults="$(shell_normalize_bool_truefalse "${BLUEPRINT_VALIDATE_RENDER_WITH_CONTRACT_DEFAULTS:-true}")"
module_toggle_flags=(
  OBSERVABILITY_ENABLED
  WORKFLOWS_ENABLED
  LANGFUSE_ENABLED
  POSTGRES_ENABLED
  NEO4J_ENABLED
  OBJECT_STORAGE_ENABLED
  RABBITMQ_ENABLED
  DNS_ENABLED
  PUBLIC_ENDPOINTS_ENABLED
  SECRETS_MANAGER_ENABLED
  KMS_ENABLED
  IDENTITY_AWARE_PROXY_ENABLED
)

render_makefile_cmd=("$ROOT_DIR/scripts/bin/blueprint/render_makefile.sh")
validate_contract_cmd=(
  "$ROOT_DIR/scripts/bin/blueprint/validate_contract.py"
  "--contract-path"
  "$ROOT_DIR/blueprint/contract.yaml"
)
if [[ "$render_with_contract_defaults" == "true" ]]; then
  ignored_module_overrides=()
  render_makefile_cmd=(env)
  validate_contract_cmd=(env)
  for toggle_name in "${module_toggle_flags[@]}"; do
    if [[ -n "${!toggle_name+x}" ]]; then
      ignored_module_overrides+=("$toggle_name")
    fi
    render_makefile_cmd+=(-u "$toggle_name")
    validate_contract_cmd+=(-u "$toggle_name")
  done
  render_makefile_cmd+=("$ROOT_DIR/scripts/bin/blueprint/render_makefile.sh")
  validate_contract_cmd+=(
    "$ROOT_DIR/scripts/bin/blueprint/validate_contract.py"
    "--contract-path"
    "$ROOT_DIR/blueprint/contract.yaml"
  )
  if [[ "${#ignored_module_overrides[@]}" -gt 0 ]]; then
    log_info "infra validate ignored transient module toggle overrides while rendering makefile: ${ignored_module_overrides[*]}"
  fi
fi

run_cmd "${render_makefile_cmd[@]}"
run_cmd "${validate_contract_cmd[@]}"
log_info "infra validation passed"
