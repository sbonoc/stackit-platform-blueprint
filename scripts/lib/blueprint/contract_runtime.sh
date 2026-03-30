#!/usr/bin/env bash
set -euo pipefail

BLUEPRINT_CONTRACT_RUNTIME_LOADED="${BLUEPRINT_CONTRACT_RUNTIME_LOADED:-false}"
BLUEPRINT_CONTRACT_RUNTIME_LINES="${BLUEPRINT_CONTRACT_RUNTIME_LINES:-}"

_blueprint_contract_runtime_set_default_lines() {
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'repo_mode=template-source\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'mode_from=template-source\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'mode_to=generated-consumer\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'defaults_env_file=blueprint/repo.init.env\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'secrets_example_env_file=blueprint/repo.init.secrets.example.env\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'secrets_env_file=blueprint/repo.init.secrets.env\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'force_env_var=BLUEPRINT_INIT_FORCE\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_REPO_NAME\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_GITHUB_ORG\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_GITHUB_REPO\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_DEFAULT_BRANCH\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_REGION\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_TENANT_SLUG\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_PLATFORM_SLUG\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_PROJECT_ID\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_TFSTATE_BUCKET\n'
  BLUEPRINT_CONTRACT_RUNTIME_LINES+=$'required_input=BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX\n'
}

load_blueprint_contract_runtime() {
  if [[ "$BLUEPRINT_CONTRACT_RUNTIME_LOADED" == "true" ]]; then
    return 0
  fi
  BLUEPRINT_CONTRACT_RUNTIME_LOADED="true"

  local contract_path="$ROOT_DIR/blueprint/contract.yaml"
  if [[ ! -f "$contract_path" ]]; then
    if [[ "${BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS:-false}" == "true" ]]; then
      _blueprint_contract_runtime_set_default_lines
      return 0
    fi
    log_fatal "missing blueprint contract: $contract_path"
  fi
  require_command python3
  local runtime_helper="$ROOT_DIR/scripts/lib/blueprint/contract_runtime_cli.py"
  if [[ ! -f "$runtime_helper" ]]; then
    log_fatal "missing runtime helper: $runtime_helper"
  fi

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    BLUEPRINT_CONTRACT_RUNTIME_LINES+="${line}"$'\n'
  done < <(
    python3 "$runtime_helper" runtime-lines --contract-path "$contract_path"
  )
}

_blueprint_contract_runtime_value() {
  local key="$1"
  load_blueprint_contract_runtime

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    if [[ "${line%%=*}" == "$key" ]]; then
      printf '%s\n' "${line#*=}"
      return 0
    fi
  done <<<"$BLUEPRINT_CONTRACT_RUNTIME_LINES"
  return 1
}

_blueprint_contract_runtime_has_value() {
  local key="$1"
  local expected="$2"
  load_blueprint_contract_runtime

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    if [[ "${line%%=*}" == "$key" && "${line#*=}" == "$expected" ]]; then
      return 0
    fi
  done <<<"$BLUEPRINT_CONTRACT_RUNTIME_LINES"
  return 1
}

_blueprint_contract_runtime_values() {
  local key="$1"
  load_blueprint_contract_runtime

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    if [[ "${line%%=*}" == "$key" ]]; then
      printf '%s\n' "${line#*=}"
    fi
  done <<<"$BLUEPRINT_CONTRACT_RUNTIME_LINES"
}

blueprint_repo_mode() {
  _blueprint_contract_runtime_value "repo_mode"
}

blueprint_repo_mode_from() {
  _blueprint_contract_runtime_value "mode_from"
}

blueprint_repo_mode_to() {
  _blueprint_contract_runtime_value "mode_to"
}

blueprint_repo_is_generated_consumer() {
  [[ "$(blueprint_repo_mode)" == "$(blueprint_repo_mode_to)" ]]
}

blueprint_defaults_env_file() {
  printf '%s/%s\n' "$ROOT_DIR" "$(_blueprint_contract_runtime_value "defaults_env_file")"
}

blueprint_secrets_example_env_file() {
  printf '%s/%s\n' "$ROOT_DIR" "$(_blueprint_contract_runtime_value "secrets_example_env_file")"
}

blueprint_secrets_env_file() {
  printf '%s/%s\n' "$ROOT_DIR" "$(_blueprint_contract_runtime_value "secrets_env_file")"
}

blueprint_load_env_defaults() {
  load_env_file_defaults "$(blueprint_defaults_env_file)"
  load_env_file_defaults "$(blueprint_secrets_env_file)"
}

_blueprint_unset_placeholder_env_if_equal() {
  local env_name="$1"
  local placeholder="$2"
  if [[ "${!env_name:-}" == "$placeholder" ]]; then
    unset "$env_name"
    return 0
  fi
  return 1
}

blueprint_sanitize_init_placeholder_defaults() {
  if blueprint_repo_is_generated_consumer; then
    return 0
  fi

  local -a placeholder_specs=(
    "BLUEPRINT_REPO_NAME:your-platform-blueprint"
    "BLUEPRINT_GITHUB_ORG:your-github-org"
    "BLUEPRINT_GITHUB_REPO:your-platform-blueprint"
    "BLUEPRINT_DOCS_TITLE:Your Platform Blueprint"
    "BLUEPRINT_STACKIT_TENANT_SLUG:your-tenant-slug"
    "BLUEPRINT_STACKIT_PLATFORM_SLUG:your-platform-slug"
    "BLUEPRINT_STACKIT_PROJECT_ID:your-stackit-project-id"
    "BLUEPRINT_STACKIT_TFSTATE_BUCKET:your-stackit-tfstate-bucket"
  )

  local cleared_count=0
  local spec env_name placeholder
  for spec in "${placeholder_specs[@]}"; do
    env_name="${spec%%:*}"
    placeholder="${spec#*:}"
    if _blueprint_unset_placeholder_env_if_equal "$env_name" "$placeholder"; then
      cleared_count=$((cleared_count + 1))
    fi
  done

  if ((cleared_count > 0)); then
    log_metric "blueprint_init_placeholder_defaults_cleared_total" "$cleared_count"
  fi
}

blueprint_load_env_defaults_for_init() {
  blueprint_load_env_defaults
  blueprint_sanitize_init_placeholder_defaults
}

blueprint_init_force_env_var() {
  _blueprint_contract_runtime_value "force_env_var"
}

blueprint_required_inputs() {
  _blueprint_contract_runtime_values "required_input"
}

blueprint_required_env_vars() {
  local contract_path="$ROOT_DIR/blueprint/contract.yaml"
  if [[ ! -f "$contract_path" ]]; then
    blueprint_required_inputs
    return 0
  fi

  require_command python3
  local runtime_helper="$ROOT_DIR/scripts/lib/blueprint/contract_runtime_cli.py"
  if [[ ! -f "$runtime_helper" ]]; then
    log_fatal "missing runtime helper: $runtime_helper"
  fi
  python3 "$runtime_helper" required-env-vars --contract-path "$contract_path"
}

blueprint_require_runtime_env() {
  local -a required_vars=()
  local required_var
  while IFS= read -r required_var; do
    [[ -n "$required_var" ]] || continue
    required_vars+=("$required_var")
  done < <(blueprint_required_env_vars)
  if ((${#required_vars[@]} == 0)); then
    return 0
  fi
  log_metric "blueprint_required_env_var_count" "${#required_vars[@]}"
  require_env_vars "${required_vars[@]}"
}

blueprint_path_is_consumer_seeded() {
  local relative_path="$1"
  _blueprint_contract_runtime_has_value "consumer_seeded" "$relative_path"
}

blueprint_path_is_init_managed() {
  local relative_path="$1"
  _blueprint_contract_runtime_has_value "init_managed" "$relative_path"
}
