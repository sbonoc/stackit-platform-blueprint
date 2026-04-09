#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/local_post_deploy_hook.sh"

start_script_metric_trap "infra_provision_deploy"

usage() {
  cat <<'EOF'
Usage: provision_deploy.sh

Runs the canonical full wrapper chain:
1) infra-provision
2) infra-deploy
3) infra-smoke

For local profiles, an optional post-deploy hook contract runs after smoke:
- enable with LOCAL_POST_DEPLOY_HOOK_ENABLED=true
- strict failure mode with LOCAL_POST_DEPLOY_HOOK_REQUIRED=true
- hook command from LOCAL_POST_DEPLOY_HOOK_CMD
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

blueprint_load_env_defaults

run_cmd "$ROOT_DIR/scripts/bin/infra/provision.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/deploy.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/smoke.sh"
local_post_deploy_hook_run

log_info "infra provision-deploy chain complete"
