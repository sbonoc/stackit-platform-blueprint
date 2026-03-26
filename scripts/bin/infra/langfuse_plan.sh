#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/langfuse.sh"

start_script_metric_trap "infra_langfuse_plan"

if ! is_module_enabled langfuse; then
  log_info "LANGFUSE_ENABLED=false; skipping langfuse plan"
  exit 0
fi

langfuse_init_env
resolve_optional_module_execution "langfuse" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_optional_manifest)
  optional_module_require_manifest_present "langfuse" "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "langfuse" "plan"
  ;;
esac

state_file="$(write_state_file "langfuse_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "public_domain=$LANGFUSE_PUBLIC_DOMAIN" \
  "public_url=$(langfuse_public_url)" \
  "oidc_issuer_url=$LANGFUSE_OIDC_ISSUER_URL" \
  "oidc_client_id=$LANGFUSE_OIDC_CLIENT_ID" \
  "database_url=$LANGFUSE_DATABASE_URL" \
  "retention_days=${LANGFUSE_RETENTION_DAYS:-30}" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "langfuse plan state written to $state_file"
