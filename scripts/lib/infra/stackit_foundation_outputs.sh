#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

STACKIT_FOUNDATION_OUTPUTS_JSON="${STACKIT_FOUNDATION_OUTPUTS_JSON:-}"
STACKIT_FOUNDATION_OUTPUTS_LOADED="${STACKIT_FOUNDATION_OUTPUTS_LOADED:-false}"

stackit_foundation_outputs_reset() {
  STACKIT_FOUNDATION_OUTPUTS_JSON=""
  STACKIT_FOUNDATION_OUTPUTS_LOADED="false"
}

stackit_foundation_outputs_load() {
  if [[ "$STACKIT_FOUNDATION_OUTPUTS_LOADED" == "true" ]]; then
    [[ -n "$STACKIT_FOUNDATION_OUTPUTS_JSON" ]]
    return "$?"
  fi

  STACKIT_FOUNDATION_OUTPUTS_LOADED="true"
  STACKIT_FOUNDATION_OUTPUTS_JSON=""

  if ! is_stackit_profile || ! tooling_is_execution_enabled || ! state_file_exists stackit_foundation_apply; then
    return 1
  fi
  if ! shell_has_cmd terraform || ! shell_has_cmd python3; then
    return 1
  fi

  local foundation_dir backend_file
  foundation_dir="$(stackit_layer_dir "foundation")"
  backend_file="$(stackit_layer_backend_file "foundation")"

  if ! terraform_backend_init "$foundation_dir" "$backend_file" >&2; then
    log_metric "stackit_foundation_output_fetch_total" "1" "status=failure stage=init" >&2
    return 1
  fi

  if ! STACKIT_FOUNDATION_OUTPUTS_JSON="$(terraform -chdir="$foundation_dir" output -json 2>&2)"; then
    log_metric "stackit_foundation_output_fetch_total" "1" "status=failure stage=output" >&2
    return 1
  fi

  log_metric "stackit_foundation_output_fetch_total" "1" "status=success stage=output" >&2
}

stackit_foundation_output_value() {
  local output_name="$1"
  if ! stackit_foundation_outputs_load; then
    return 1
  fi

  STACKIT_FOUNDATION_OUTPUTS_JSON="$STACKIT_FOUNDATION_OUTPUTS_JSON" \
    python3 "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs_json.py" value "$output_name"
}

stackit_foundation_output_map_value() {
  local output_name="$1"
  local map_key="$2"
  if ! stackit_foundation_outputs_load; then
    return 1
  fi

  STACKIT_FOUNDATION_OUTPUTS_JSON="$STACKIT_FOUNDATION_OUTPUTS_JSON" \
    python3 "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs_json.py" map-value "$output_name" "$map_key"
}

stackit_foundation_output_value_or_default() {
  local output_name="$1"
  local fallback_value="$2"
  local value=""

  if value="$(stackit_foundation_output_value "$output_name")"; then
    log_metric "stackit_foundation_output_resolve_total" "1" "output=$output_name status=resolved" >&2
    printf '%s' "$value"
    return 0
  fi

  if is_stackit_profile && tooling_is_execution_enabled && state_file_exists stackit_foundation_apply; then
    log_warn "using deterministic placeholder for STACKIT foundation output '$output_name'"
  fi

  log_metric "stackit_foundation_output_resolve_total" "1" "output=$output_name status=fallback" >&2
  printf '%s' "$fallback_value"
}

stackit_foundation_output_map_value_or_default() {
  local output_name="$1"
  local map_key="$2"
  local fallback_value="$3"
  local value=""

  if value="$(stackit_foundation_output_map_value "$output_name" "$map_key")"; then
    log_metric "stackit_foundation_output_resolve_total" "1" "output=$output_name status=resolved kind=map" >&2
    printf '%s' "$value"
    return 0
  fi

  if is_stackit_profile && tooling_is_execution_enabled && state_file_exists stackit_foundation_apply; then
    log_warn "using deterministic placeholder for STACKIT foundation map output '$output_name' key='$map_key'"
  fi

  log_metric "stackit_foundation_output_resolve_total" "1" "output=$output_name status=fallback kind=map" >&2
  printf '%s' "$fallback_value"
}
