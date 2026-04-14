#!/usr/bin/env bash
set -euo pipefail

BLUEPRINT_PROFILE="${BLUEPRINT_PROFILE:-local-full}"
PROFILE_SH_ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
MODULE_ENABLEMENT_CONTRACT_LOADED="false"
MODULE_ENABLEMENT_CONTRACT_LINES="${MODULE_ENABLEMENT_CONTRACT_LINES:-}"

normalize_bool() {
  local value="${1:-false}"
  case "$value" in
  1 | true | TRUE | True | yes | YES | on | ON)
    echo "true"
    ;;
  *)
    echo "false"
    ;;
  esac
}

OBSERVABILITY_ENABLED_NORMALIZED="$(normalize_bool "${OBSERVABILITY_ENABLED:-false}")"

load_module_enablement_contract_defaults() {
  if [[ "$MODULE_ENABLEMENT_CONTRACT_LOADED" == "true" ]]; then
    return 0
  fi
  MODULE_ENABLEMENT_CONTRACT_LOADED="true"

  # Generated repos persist their selected module set in blueprint/contract.yaml
  # during blueprint-init-repo. Shell env flags still win when operators need an override.
  local contract_path="$PROFILE_SH_ROOT_DIR/blueprint/contract.yaml"
  if [[ ! -f "$contract_path" ]] || ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  local runtime_helper="$PROFILE_SH_ROOT_DIR/scripts/lib/blueprint/contract_runtime_cli.py"
  if [[ ! -f "$runtime_helper" ]]; then
    return 0
  fi

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    MODULE_ENABLEMENT_CONTRACT_LINES+="${line}"$'\n'
  done < <(
    python3 "$runtime_helper" module-defaults --contract-path "$contract_path"
  )
}

module_contract_default_enabled() {
  local module="$1"
  load_module_enablement_contract_defaults

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    if [[ "${line%%=*}" == "$module" ]]; then
      normalize_bool "${line#*=}"
      return 0
    fi
  done <<<"$MODULE_ENABLEMENT_CONTRACT_LINES"

  echo "false"
}

is_local_profile() {
  [[ "$BLUEPRINT_PROFILE" == local-* ]]
}

is_stackit_profile() {
  [[ "$BLUEPRINT_PROFILE" == stackit-* ]]
}

profile_environment() {
  case "$BLUEPRINT_PROFILE" in
  stackit-dev)
    echo "dev"
    ;;
  stackit-stage)
    echo "stage"
    ;;
  stackit-prod)
    echo "prod"
    ;;
  local-full | local-lite)
    echo "local"
    ;;
  *)
    echo "unknown"
    ;;
  esac
}

active_stack() {
  if is_local_profile; then
    echo "local"
    return 0
  fi
  if is_stackit_profile; then
    echo "stackit"
    return 0
  fi
  echo "unknown"
}

is_observability_enabled() {
  is_module_enabled observability
}

module_flag_name() {
  local module="$1"
  case "$module" in
  observability)
    echo "OBSERVABILITY_ENABLED"
    ;;
  workflows)
    echo "WORKFLOWS_ENABLED"
    ;;
  langfuse)
    echo "LANGFUSE_ENABLED"
    ;;
  postgres)
    echo "POSTGRES_ENABLED"
    ;;
  neo4j)
    echo "NEO4J_ENABLED"
    ;;
  object-storage)
    echo "OBJECT_STORAGE_ENABLED"
    ;;
  rabbitmq)
    echo "RABBITMQ_ENABLED"
    ;;
  opensearch)
    echo "OPENSEARCH_ENABLED"
    ;;
  dns)
    echo "DNS_ENABLED"
    ;;
  public-endpoints)
    echo "PUBLIC_ENDPOINTS_ENABLED"
    ;;
  secrets-manager)
    echo "SECRETS_MANAGER_ENABLED"
    ;;
  kms)
    echo "KMS_ENABLED"
    ;;
  identity-aware-proxy)
    echo "IDENTITY_AWARE_PROXY_ENABLED"
    ;;
  *)
    return 1
    ;;
  esac
}

is_module_enabled() {
  local module="$1"
  local var_name
  var_name="$(module_flag_name "$module")" || return 1
  local raw
  if [[ -n "${!var_name+x}" ]]; then
    raw="${!var_name}"
  else
    raw="$(module_contract_default_enabled "$module")"
  fi
  [[ "$(normalize_bool "$raw")" == "true" ]]
}

enabled_modules_csv() {
  local modules=(
    observability
    workflows
    langfuse
    postgres
    neo4j
    object-storage
    rabbitmq
    opensearch
    dns
    public-endpoints
    secrets-manager
    kms
    identity-aware-proxy
  )
  local out=""
  local module
  for module in "${modules[@]}"; do
    if is_module_enabled "$module"; then
      if [[ -n "$out" ]]; then
        out+=","
      fi
      out+="$module"
    fi
  done
  echo "$out"
}
