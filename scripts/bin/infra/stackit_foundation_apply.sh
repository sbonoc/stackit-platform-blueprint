#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_foundation_apply"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_apply.sh

Runs terraform apply for the STACKIT foundation layer.

Environment variables:
  STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS         Max bounded retries for transient provider races (default: 3)
  STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS  Delay between retry attempts in seconds (default: 30)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS "3"
set_default_env STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS "30"

stackit_foundation_apply_is_transient_postgres_notfound() {
  local output_file="$1"
  grep -Fq 'stackit_postgresflex_instance.foundation[0]' "$output_file" &&
    grep -Fq 'Requested instance with ID:' "$output_file" &&
    grep -Fq 'cannot be found' "$output_file"
}

stackit_foundation_apply_clear_transient_postgres_taint() {
  local terraform_dir="$1"
  local untaint_status=0

  set +e
  run_cmd terraform -chdir="$terraform_dir" untaint "stackit_postgresflex_instance.foundation[0]"
  untaint_status="$?"
  set -e

  if [[ "$untaint_status" -eq 0 ]]; then
    log_metric "stackit_foundation_apply_untaint_total" "1" "status=success reason=postgresflex_notfound"
    return 0
  fi

  log_warn "failed to clear transient PostgreSQL Flex taint before retry status=$untaint_status"
  log_metric "stackit_foundation_apply_untaint_total" "1" "status=failure reason=postgresflex_notfound"
  return "$untaint_status"
}

run_stackit_foundation_apply_with_retry() {
  local terraform_dir="$1"
  local backend_file="$2"
  local var_file="$3"
  shift 3 || true
  local extra_args=("$@")
  local max_attempts="$STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS"
  local retry_delay_seconds="$STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS"
  local attempt=1
  local apply_status=0
  local retry_reason="none"
  local output_file
  output_file="$(mktemp)"

  while ((attempt <= max_attempts)); do
    : >"$output_file"
    set +e
    run_terraform_action_with_backend apply "$terraform_dir" "$backend_file" "$var_file" "${extra_args[@]}" 2>&1 | tee "$output_file"
    apply_status=${PIPESTATUS[0]}
    set -e

    if [[ "$apply_status" -eq 0 ]]; then
      log_metric "stackit_foundation_apply_attempt_total" "1" "status=success attempt=$attempt retries=$((attempt - 1)) reason=$retry_reason"
      rm -f "$output_file"
      return 0
    fi

    retry_reason="non_retryable"
    if stackit_foundation_apply_is_transient_postgres_notfound "$output_file"; then
      retry_reason="postgresflex_notfound"
    fi

    if [[ "$retry_reason" != "postgresflex_notfound" || "$attempt" -ge "$max_attempts" ]]; then
      log_metric "stackit_foundation_apply_attempt_total" "1" "status=failure attempt=$attempt retries=$((attempt - 1)) reason=$retry_reason"
      rm -f "$output_file"
      return "$apply_status"
    fi

    log_warn \
      "transient STACKIT PostgresFlex create/read race detected; retrying foundation apply attempt=$attempt/$max_attempts delay=${retry_delay_seconds}s"
    log_metric "stackit_foundation_apply_retry_total" "1" "cause=$retry_reason attempt=$attempt delay_seconds=$retry_delay_seconds"
    stackit_foundation_apply_clear_transient_postgres_taint "$terraform_dir" || true
    sleep "$retry_delay_seconds"
    attempt=$((attempt + 1))
  done

  rm -f "$output_file"
  return "$apply_status"
}

stackit_layer_preflight "foundation"
foundation_dir="$(stackit_layer_dir "foundation")"
backend_file="$(stackit_layer_backend_file "foundation")"
var_file="$(stackit_layer_var_file "foundation")"
tf_var_args=()
while IFS= read -r arg; do
  [[ -n "$arg" ]] || continue
  tf_var_args+=("$arg")
done < <(stackit_layer_var_args "foundation")
run_stackit_foundation_apply_with_retry "$foundation_dir" "$backend_file" "$var_file" "${tf_var_args[@]}"

# Downstream STACKIT module/runtime actions consume the concrete kubeconfig
# artifact, not just the Terraform output stored in state. Materialize it
# immediately after foundation apply so provision-time modules can target the
# new cluster without requiring a separate manual fetch step.
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh"

kubeconfig_state="none"
if state_file_exists stackit_foundation_kubeconfig; then
  kubeconfig_state="$ROOT_DIR/artifacts/infra/stackit_foundation_kubeconfig.env"
fi

state_file="$(
  write_state_file "stackit_foundation_apply" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$foundation_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "apply_max_attempts=$STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS" \
    "apply_retry_delay_seconds=$STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS" \
    "kubeconfig_state=$kubeconfig_state" \
    "action=apply" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation apply state written to $state_file"
