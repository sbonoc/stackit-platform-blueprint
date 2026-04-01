#!/usr/bin/env bash
set -euo pipefail

ASYNC_PACT_FEATURE_TOGGLE_ENV_VAR="ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED"
ASYNC_PACT_PRODUCER_VERIFY_ENV_VAR="ASYNC_PACT_PRODUCER_VERIFY_CMD"
ASYNC_PACT_CONSUMER_VERIFY_ENV_VAR="ASYNC_PACT_CONSUMER_VERIFY_CMD"
ASYNC_PACT_BROKER_PUBLISH_ENV_VAR="ASYNC_PACT_BROKER_PUBLISH_CMD"
ASYNC_PACT_CAN_I_DEPLOY_ENV_VAR="ASYNC_PACT_CAN_I_DEPLOY_CMD"

async_message_contracts_feature_enabled() {
  shell_normalize_bool_truefalse "${ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED:-false}"
}

async_message_contracts_default_artifact_dir() {
  local role="$1"
  local dir
  case "$role" in
  producer)
    dir="${ASYNC_PACT_PRODUCER_ARTIFACT_DIR:-artifacts/contracts/async/pact/producer}"
    ;;
  consumer)
    dir="${ASYNC_PACT_CONSUMER_ARTIFACT_DIR:-artifacts/contracts/async/pact/consumer}"
    ;;
  *)
    log_fatal "unsupported async pact role: $role"
    ;;
  esac

  # Normalize relative artifact paths against repository root for deterministic outputs.
  if [[ "$dir" != /* ]]; then
    dir="$ROOT_DIR/$dir"
  fi

  printf '%s' "$dir"
}

async_message_contracts_contract_dir() {
  local role="$1"
  printf '%s' "$ROOT_DIR/contracts/async/pact/messages/$role"
}

async_message_contracts_contract_file_count() {
  local contracts_dir="$1"
  if [[ ! -d "$contracts_dir" ]]; then
    printf '0'
    return 0
  fi

  local count
  count="$(find "$contracts_dir" -type f ! -name '.gitkeep' ! -name 'README.md' ! -name 'verify.sh' | wc -l | tr -d '[:space:]')"
  printf '%s' "${count:-0}"
}

_async_message_contract_verify_env_var() {
  local role="$1"
  case "$role" in
  producer)
    printf '%s' "$ASYNC_PACT_PRODUCER_VERIFY_ENV_VAR"
    ;;
  consumer)
    printf '%s' "$ASYNC_PACT_CONSUMER_VERIFY_ENV_VAR"
    ;;
  *)
    log_fatal "unsupported async pact role: $role"
    ;;
  esac
}

async_message_contracts_run_optional_hook() {
  local hook_name="$1"
  local hook_command="${2:-}"
  local artifact_dir="${3:-$ROOT_DIR/artifacts/contracts/async/pact}"
  local hook_start_epoch
  hook_start_epoch="$(now_epoch_seconds)"

  if [[ -z "$hook_command" ]]; then
    log_metric "async_pact_optional_hook_duration_seconds" \
      "$(( $(now_epoch_seconds) - hook_start_epoch ))" \
      "hook=$hook_name status=skipped reason=not_configured"
    return 0
  fi

  log_info "running async pact optional hook hook=$hook_name"
  if ! (
    export ASYNC_PACT_PROVIDER="pact"
    export ASYNC_PACT_ARTIFACT_DIR="$artifact_dir"
    run_cmd bash -lc "$hook_command"
  ); then
    log_metric "async_pact_optional_hook_duration_seconds" \
      "$(( $(now_epoch_seconds) - hook_start_epoch ))" \
      "hook=$hook_name status=failure"
    return 1
  fi

  log_metric "async_pact_optional_hook_duration_seconds" \
    "$(( $(now_epoch_seconds) - hook_start_epoch ))" \
    "hook=$hook_name status=success"
}

async_message_contracts_run_lane() {
  local role="$1"
  local lane_start_epoch
  lane_start_epoch="$(now_epoch_seconds)"

  if [[ "$(async_message_contracts_feature_enabled)" != "true" ]]; then
    log_info "async pact message-contract lane skipped; feature toggle disabled role=$role env=$ASYNC_PACT_FEATURE_TOGGLE_ENV_VAR"
    log_metric "async_pact_message_contract_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "role=$role status=skipped reason=feature_disabled"
    return 0
  fi

  local contracts_dir
  contracts_dir="$(async_message_contracts_contract_dir "$role")"
  local artifact_dir
  artifact_dir="$(async_message_contracts_default_artifact_dir "$role")"
  local contract_file_count
  contract_file_count="$(async_message_contracts_contract_file_count "$contracts_dir")"

  ensure_dir "$artifact_dir"

  local verify_env_var
  verify_env_var="$(_async_message_contract_verify_env_var "$role")"
  local verify_command="${!verify_env_var:-}"
  local fallback_verify_script="$contracts_dir/verify.sh"

  log_info "running async pact message-contract lane role=$role contracts_dir=$contracts_dir artifact_dir=$artifact_dir contract_files=$contract_file_count"

  if [[ -n "$verify_command" ]]; then
    if ! (
      export ASYNC_PACT_PROVIDER="pact"
      export ASYNC_PACT_MESSAGE_ROLE="$role"
      export ASYNC_PACT_CONTRACTS_DIR="$contracts_dir"
      export ASYNC_PACT_ARTIFACT_DIR="$artifact_dir"
      run_cmd bash -lc "$verify_command"
    ); then
      log_metric "async_pact_message_contract_lane_duration_seconds" \
        "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
        "role=$role status=failure reason=verify_command_failed contracts=$contract_file_count"
      return 1
    fi
  elif [[ -f "$fallback_verify_script" ]]; then
    if ! (
      export ASYNC_PACT_PROVIDER="pact"
      export ASYNC_PACT_MESSAGE_ROLE="$role"
      export ASYNC_PACT_CONTRACTS_DIR="$contracts_dir"
      export ASYNC_PACT_ARTIFACT_DIR="$artifact_dir"
      run_cmd bash "$fallback_verify_script"
    ); then
      log_metric "async_pact_message_contract_lane_duration_seconds" \
        "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
        "role=$role status=failure reason=verify_script_failed contracts=$contract_file_count"
      return 1
    fi
  else
    log_error "async pact message-contract lane enabled but verification entrypoint is missing role=$role env=$verify_env_var fallback=$fallback_verify_script"
    log_metric "async_pact_message_contract_lane_duration_seconds" \
      "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
      "role=$role status=failure reason=verify_entrypoint_missing contracts=$contract_file_count"
    return 1
  fi

  if [[ "$role" == "producer" ]]; then
    if ! async_message_contracts_run_optional_hook \
      "producer_publish" \
      "${ASYNC_PACT_BROKER_PUBLISH_CMD:-}" \
      "$artifact_dir"; then
      log_metric "async_pact_message_contract_lane_duration_seconds" \
        "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
        "role=$role status=failure reason=producer_publish_failed contracts=$contract_file_count"
      return 1
    fi
  fi

  log_metric "async_pact_message_contract_lane_duration_seconds" \
    "$(( $(now_epoch_seconds) - lane_start_epoch ))" \
    "role=$role status=success contracts=$contract_file_count"
}

async_message_contracts_run_can_i_deploy_hook() {
  if [[ "$(async_message_contracts_feature_enabled)" != "true" ]]; then
    return 0
  fi
  local artifact_dir
  artifact_dir="$(async_message_contracts_default_artifact_dir consumer)"
  async_message_contracts_run_optional_hook \
    "can_i_deploy" \
    "${ASYNC_PACT_CAN_I_DEPLOY_CMD:-}" \
    "$artifact_dir"
}
