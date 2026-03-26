#!/usr/bin/env bash
set -euo pipefail

BLUEPRINT_PROFILE="${BLUEPRINT_PROFILE:-local-full}"

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
  *)
    return 1
    ;;
  esac
}

is_module_enabled() {
  local module="$1"
  local var_name
  var_name="$(module_flag_name "$module")" || return 1
  local raw="${!var_name:-false}"
  [[ "$(normalize_bool "$raw")" == "true" ]]
}

enabled_modules_csv() {
  local modules=(observability workflows langfuse postgres neo4j)
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
