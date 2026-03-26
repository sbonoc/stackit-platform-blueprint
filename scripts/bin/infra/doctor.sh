#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_doctor"

usage() {
  cat <<'USAGE'
Usage: doctor.sh

Checks local prerequisites for blueprint execution and profile routing:
- required commands (bash/git/make/python3)
- optional operator tooling (terraform/kubectl/helm/kustomize/jq/docker)
- canonical profile-specific path contracts.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

required_commands=(bash git make python3)
optional_commands=(terraform kubectl helm kustomize jq docker)

for cmd in "${required_commands[@]}"; do
  require_command "$cmd"
done

missing_optional=0
for cmd in "${optional_commands[@]}"; do
  if ! warn_if_missing_command "$cmd"; then
    missing_optional=$((missing_optional + 1))
  fi
done

profile_path=""
if is_stackit_profile; then
  profile_path="$(stackit_terraform_layer_dir foundation)"
  if ! terraform_dir_has_config "$profile_path"; then
    log_fatal "missing terraform configuration in STACKIT foundation path: $profile_path"
  fi
else
  profile_path="$(local_crossplane_kustomize_dir)"
  if ! kustomize_dir_has_config "$profile_path"; then
    log_fatal "missing kustomization in local provisioning path: $profile_path"
  fi
fi

current_context="unavailable"
if command -v kubectl >/dev/null 2>&1; then
  current_context="$(kubectl config current-context 2>/dev/null || true)"
  if [[ -z "$current_context" ]]; then
    current_context="unset"
  fi
fi

log_metric "infra_doctor_optional_missing_count" "$missing_optional" "profile=$BLUEPRINT_PROFILE"

state_file="$(
  write_state_file "infra_doctor" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "profile_path=$profile_path" \
    "kubectl_context=$current_context" \
    "optional_missing_count=$missing_optional" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra doctor passed profile=$BLUEPRINT_PROFILE profile_path=$profile_path"
log_info "infra doctor state written to $state_file"
