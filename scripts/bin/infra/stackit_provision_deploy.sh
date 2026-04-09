#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_stackit_provision_deploy"

usage() {
  cat <<'USAGE'
Usage: stackit_provision_deploy.sh

Runs the canonical STACKIT provision/deploy chain:
1) infra-bootstrap
2) infra-provision
3) stackit kubeconfig fetch/refresh (optional)
4) infra-stackit-runtime-prerequisites
5) infra-stackit-runtime-deploy
6) infra-stackit-smoke-foundation
7) infra-stackit-smoke-runtime

Optional environment variables:
  STACKIT_PROVISION_DEPLOY_KUBECONFIG_MODE  fetch|refresh|skip (default: fetch)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-provision-deploy requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

set_default_env STACKIT_PROVISION_DEPLOY_KUBECONFIG_MODE "fetch"
kubeconfig_mode="$STACKIT_PROVISION_DEPLOY_KUBECONFIG_MODE"
case "$kubeconfig_mode" in
fetch | refresh | skip)
  ;;
*)
  log_fatal "unsupported STACKIT_PROVISION_DEPLOY_KUBECONFIG_MODE=$kubeconfig_mode (expected fetch|refresh|skip)"
  ;;
esac

log_info "stackit provision-deploy start profile=$BLUEPRINT_PROFILE kubeconfig_mode=$kubeconfig_mode"

run_cmd "$ROOT_DIR/scripts/bin/infra/bootstrap.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/provision.sh"

case "$kubeconfig_mode" in
fetch)
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh"
  ;;
refresh)
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_refresh_kubeconfig.sh"
  ;;
skip)
  log_info "skipping stackit kubeconfig materialization (mode=skip)"
  ;;
esac

run_cmd env \
  STACKIT_RUNTIME_KUBECONFIG_MODE="$kubeconfig_mode" \
  "$ROOT_DIR/scripts/bin/infra/stackit_runtime_prerequisites.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_runtime_deploy.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_smoke_foundation.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_smoke_runtime.sh"

state_file="$(
  write_state_file "stackit_provision_deploy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "kubeconfig_mode=$kubeconfig_mode" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit provision-deploy state written to $state_file"
log_info "stackit provision-deploy complete"
