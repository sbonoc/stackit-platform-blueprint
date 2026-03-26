#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_argocd_topology_validate"

usage() {
  cat <<'USAGE'
Usage: argocd_topology_validate.sh

Validates ArgoCD base and environment overlays.
If kustomize is available, validates by rendering; otherwise checks kustomization files.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

base_dir="$(argocd_base_dir)"
overlay_dir="$(argocd_overlay_dir)"
if is_local_profile; then
  overlay_dir="$(local_argocd_overlay_dir)"
fi

if [[ ! -d "$base_dir" ]]; then
  log_fatal "missing ArgoCD base directory: $base_dir"
fi
if [[ ! -d "$overlay_dir" ]]; then
  log_fatal "missing ArgoCD overlay directory: $overlay_dir"
fi

validation_mode="kustomization-file"
if command -v kustomize >/dev/null 2>&1; then
  run_cmd_capture kustomize build "$base_dir" >/dev/null
  run_cmd_capture kustomize build "$overlay_dir" >/dev/null
  validation_mode="kustomize-build"
else
  if ! kustomize_dir_has_config "$base_dir"; then
    log_fatal "kustomization file missing in ArgoCD base directory: $base_dir"
  fi
  if ! kustomize_dir_has_config "$overlay_dir"; then
    log_fatal "kustomization file missing in ArgoCD overlay directory: $overlay_dir"
  fi
  log_warn "kustomize not found; validated only kustomization files"
fi

state_file="$(
  write_state_file "argocd_topology_validate" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "validation_mode=$validation_mode" \
    "base_dir=$base_dir" \
    "overlay_dir=$overlay_dir" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "argocd topology validation mode=$validation_mode"
log_info "argocd topology validation state written to $state_file"
