#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh"

start_script_metric_trap "infra_provision"

usage() {
  cat <<'EOF'
Usage: provision.sh

Contract-driven provisioning wrapper:
- validates repository contract,
- executes stack-specific provisioning path,
- optionally provisions enabled module resources,
- persists execution state under artifacts/infra.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "provision start profile=$BLUEPRINT_PROFILE stack=$(active_stack) observability=$OBSERVABILITY_ENABLED_NORMALIZED"
run_cmd "$ROOT_DIR/scripts/bin/infra/bootstrap.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

foundation_driver="none"
foundation_path="none"
if is_stackit_profile; then
  foundation_driver="terraform-layered"
  foundation_path="$(stackit_terraform_layer_dir foundation)"
  log_info "selected STACKIT provisioning path bootstrap+foundation dir=$foundation_path"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_bootstrap_preflight.sh"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_bootstrap_apply.sh"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
elif is_local_profile; then
  foundation_driver="crossplane-helm-bootstrap"
  foundation_path="$(local_crossplane_kustomize_dir)"
  log_info "selected local provisioning path dir=$foundation_path"
  run_cmd "$ROOT_DIR/scripts/bin/infra/local_crossplane_bootstrap.sh"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

run_enabled_modules_action plan \
  observability workflows langfuse postgres neo4j \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy
run_enabled_modules_action apply \
  observability workflows langfuse postgres neo4j \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy

local_crossplane_state="none"
if state_file_exists local_crossplane_bootstrap; then
  local_crossplane_state="$ROOT_DIR/artifacts/infra/local_crossplane_bootstrap.env"
fi

state_file="$(
  write_state_file "provision" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "foundation_driver=$foundation_driver" \
    "foundation_path=$foundation_path" \
    "local_crossplane_state=$local_crossplane_state" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "provision state written to $state_file"
log_info "infra provision complete"
