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

start_script_metric_trap "infra_deploy"

usage() {
  cat <<'EOF'
Usage: deploy.sh

Contract-driven deployment wrapper:
- validates repository contract,
- executes stack-specific deployment path,
- deploys enabled optional modules,
- persists deployment state under artifacts/infra.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "deploy start profile=$BLUEPRINT_PROFILE stack=$(active_stack) observability=$OBSERVABILITY_ENABLED_NORMALIZED"
run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

if ! state_file_exists provision; then
  log_warn "provision state not found; deployment will continue"
fi

deploy_driver="none"
overlay_path="none"
if is_stackit_profile; then
  deploy_driver="argocd-kustomize"
  overlay_path="$(argocd_overlay_dir)"
  log_info "selected STACKIT deployment path overlay=$overlay_path"
  run_kustomize_apply "$(argocd_base_dir)"
  run_kustomize_apply "$overlay_path"
elif is_local_profile; then
  deploy_driver="argocd-kustomize"
  overlay_path="$(local_argocd_overlay_dir)"
  log_info "selected local deployment path overlay=$overlay_path"
  run_kustomize_apply "$(argocd_base_dir)"
  run_kustomize_apply "$overlay_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

run_enabled_modules_action deploy observability

run_cmd "$ROOT_DIR/scripts/bin/platform/apps/bootstrap.sh"

run_enabled_modules_action deploy \
  workflows langfuse neo4j postgres \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy

state_file="$(
  write_state_file "deploy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "deploy_driver=$deploy_driver" \
    "argocd_overlay_path=$overlay_path" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "deploy state written to $state_file"
log_info "infra deploy complete"
