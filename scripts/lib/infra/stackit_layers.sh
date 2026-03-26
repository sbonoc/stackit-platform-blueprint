#!/usr/bin/env bash
set -euo pipefail

stackit_layer_label() {
  local layer="$1"
  case "$layer" in
  bootstrap)
    echo "bootstrap"
    ;;
  foundation)
    echo "foundation"
    ;;
  *)
    log_fatal "unsupported stackit layer: $layer"
    ;;
  esac
}

stackit_layer_dir() {
  local layer="$1"
  stackit_layer_label "$layer" >/dev/null

  case "$layer" in
  bootstrap)
    # Current blueprint keeps bootstrap/foundation in the same terraform environment tree.
    # A dedicated bootstrap path can be injected via STACKIT_BOOTSTRAP_TERRAFORM_DIR.
    set_default_env STACKIT_BOOTSTRAP_TERRAFORM_DIR "$(stackit_terraform_env_dir)"
    local configured_dir="$STACKIT_BOOTSTRAP_TERRAFORM_DIR"
    if [[ "$configured_dir" != /* ]]; then
      configured_dir="$ROOT_DIR/$configured_dir"
    fi
    echo "$configured_dir"
    ;;
  foundation)
    set_default_env STACKIT_FOUNDATION_TERRAFORM_DIR "$(stackit_terraform_env_dir)"
    local configured_dir="$STACKIT_FOUNDATION_TERRAFORM_DIR"
    if [[ "$configured_dir" != /* ]]; then
      configured_dir="$ROOT_DIR/$configured_dir"
    fi
    echo "$configured_dir"
    ;;
  esac
}

stackit_layer_preflight() {
  local layer="$1"
  local target_name="infra-stackit-$(stackit_layer_label "$layer")-preflight"

  if ! is_stackit_profile; then
    log_fatal "$target_name requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
  fi

  local layer_dir
  layer_dir="$(stackit_layer_dir "$layer")"

  if [[ ! -d "$layer_dir" ]]; then
    log_fatal "missing STACKIT terraform directory for layer=$layer: $layer_dir"
  fi

  if ! terraform_dir_has_config "$layer_dir"; then
    log_fatal "terraform configuration not found for layer=$layer in $layer_dir"
  fi

  echo "$layer_dir"
}
