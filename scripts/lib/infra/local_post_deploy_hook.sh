#!/usr/bin/env bash
set -euo pipefail

local_post_deploy_hook_init_env() {
  set_default_env LOCAL_POST_DEPLOY_HOOK_ENABLED "false"
  set_default_env LOCAL_POST_DEPLOY_HOOK_REQUIRED "false"
  set_default_env LOCAL_POST_DEPLOY_HOOK_CMD 'make -C "$ROOT_DIR" infra-post-deploy-consumer'
}

local_post_deploy_hook_validate_state_contract() {
  local state_json_file="$1"
  local contract_cli schema_path
  contract_cli="$ROOT_DIR/scripts/lib/infra/state_artifact_contract.py"
  schema_path="$ROOT_DIR/scripts/lib/infra/schemas/local_post_deploy_hook_state.schema.json"

  if [[ ! -f "$schema_path" ]]; then
    log_fatal "local post-deploy hook schema missing: $schema_path"
  fi

  if python3 "$contract_cli" \
    --repo-root "$ROOT_DIR" \
    --schema "$schema_path" \
    validate \
    --json-file "$state_json_file"; then
    log_metric "local_post_deploy_hook_state_contract_validation_total" "1" "status=success"
    return 0
  fi

  log_metric "local_post_deploy_hook_state_contract_validation_total" "1" "status=failure"
  log_fatal "local post-deploy hook state artifact schema validation failed: $state_json_file"
}

local_post_deploy_hook_run() {
  local start_epoch status reason
  start_epoch="$(now_epoch_seconds)"
  local_post_deploy_hook_init_env

  local enabled required mode hook_command command_configured
  enabled="$(shell_normalize_bool_truefalse "${LOCAL_POST_DEPLOY_HOOK_ENABLED:-false}")"
  required="$(shell_normalize_bool_truefalse "${LOCAL_POST_DEPLOY_HOOK_REQUIRED:-false}")"
  mode="best-effort"
  if [[ "$required" == "true" ]]; then
    mode="strict"
  fi

  hook_command="${LOCAL_POST_DEPLOY_HOOK_CMD:-}"
  command_configured="false"
  if [[ -n "$hook_command" ]]; then
    command_configured="true"
  fi

  status="skipped"
  reason="disabled"
  if ! is_local_profile; then
    reason="non_local_profile"
  elif [[ "$enabled" != "true" ]]; then
    reason="disabled"
  elif [[ "$command_configured" != "true" ]]; then
    status="failure"
    reason="command_missing"
  else
    status="success"
    reason="executed"
    log_info "running local post-deploy hook mode=$mode profile=$BLUEPRINT_PROFILE"
    if ! run_cmd bash -lc "$hook_command"; then
      status="failure"
      reason="command_failed"
    fi
  fi

  local duration_seconds state_file state_json_file
  duration_seconds="$(( $(now_epoch_seconds) - start_epoch ))"
  log_metric \
    "local_post_deploy_hook_duration_seconds" \
    "$duration_seconds" \
    "status=$status reason=$reason mode=$mode profile=$BLUEPRINT_PROFILE enabled=$enabled command_configured=$command_configured"

  state_file="$(
    write_state_file "local_post_deploy_hook" \
      "profile=$BLUEPRINT_PROFILE" \
      "stack=$(active_stack)" \
      "enabled=$enabled" \
      "required=$required" \
      "mode=$mode" \
      "status=$status" \
      "reason=$reason" \
      "command_configured=$command_configured" \
      "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  )"
  state_json_file="$(state_json_file_path "local_post_deploy_hook" "infra")"
  local_post_deploy_hook_validate_state_contract "$state_json_file"
  log_info "local post-deploy hook state written to $state_file status=$status reason=$reason mode=$mode"

  if [[ "$status" != "failure" ]]; then
    return 0
  fi

  if [[ "$required" == "true" ]]; then
    log_fatal \
      "local post-deploy hook failed in strict mode (LOCAL_POST_DEPLOY_HOOK_REQUIRED=true); reason=$reason"
  fi

  log_warn \
    "local post-deploy hook failed in best-effort mode; continuing chain (reason=$reason LOCAL_POST_DEPLOY_HOOK_REQUIRED=false)"
  return 0
}
