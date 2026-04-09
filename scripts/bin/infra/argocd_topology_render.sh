#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_argocd_topology_render"

usage() {
  cat <<'USAGE'
Usage: argocd_topology_render.sh

Renders ArgoCD base and environment overlays to artifacts/infra snapshots.
If kustomize is not installed, it falls back to deterministic path summaries.
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

render_dir="$ROOT_DIR/artifacts/infra"
ensure_dir "$render_dir"

environment_name="$(profile_environment)"
base_output="$render_dir/argocd_topology_base_${environment_name}.yaml"
overlay_output="$render_dir/argocd_topology_overlay_${environment_name}.yaml"
render_mode="summary"

if command -v kustomize >/dev/null 2>&1; then
  run_cmd_capture kustomize build "$base_dir" >"$base_output"
  run_cmd_capture kustomize build "$overlay_dir" >"$overlay_output"
  render_mode="kustomize"
else
  {
    echo "# kustomize not installed; summary fallback"
    echo "# base_dir=$base_dir"
    find "$base_dir" -type f | sort
  } >"$base_output"
  {
    echo "# kustomize not installed; summary fallback"
    echo "# overlay_dir=$overlay_dir"
    find "$overlay_dir" -type f | sort
  } >"$overlay_output"
  log_warn "kustomize not found; rendered path summaries instead of manifests"
fi

base_kind_count="$(grep -c '^kind:' "$base_output" || true)"
overlay_kind_count="$(grep -c '^kind:' "$overlay_output" || true)"

state_file="$(
  write_state_file "argocd_topology_render" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$environment_name" \
    "render_mode=$render_mode" \
    "base_dir=$base_dir" \
    "overlay_dir=$overlay_dir" \
    "base_output=$base_output" \
    "overlay_output=$overlay_output" \
    "base_kind_count=$base_kind_count" \
    "overlay_kind_count=$overlay_kind_count" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "argocd topology render mode=$render_mode environment=$environment_name"
log_info "argocd topology render state written to $state_file"
