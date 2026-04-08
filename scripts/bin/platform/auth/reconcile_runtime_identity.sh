#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "platform_auth_reconcile_runtime_identity"

usage() {
  cat <<'USAGE'
Usage: reconcile_runtime_identity.sh

Contract-driven runtime identity reconciliation orchestrator:
- runs canonical ESO source->target reconciliation,
- runs ArgoCD repository credential contract reconciliation,
- validates Keycloak realm/runtime identity contract coverage for enabled modules.

Contract knobs:
- RUNTIME_IDENTITY_RECONCILE_REQUIRED (default: auto; true when either RUNTIME_CREDENTIALS_REQUIRED or ARGOCD_REPO_CREDENTIALS_REQUIRED is true)
- KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED (default from runtime identity contract)
- RUNTIME_CREDENTIALS_REQUIRED (default from runtime identity contract)
- ARGOCD_REPO_CREDENTIALS_REQUIRED (default: false)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
runtime_identity_contract_cli="$ROOT_DIR/scripts/lib/infra/runtime_identity_contract.py"
reconcile_eso_script="$ROOT_DIR/scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh"
reconcile_argocd_script="$ROOT_DIR/scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh"

while IFS=$'\t' read -r env_name env_default; do
  [[ -n "$env_name" ]] || continue
  set_default_env "$env_name" "$env_default"
done < <(python3 "$runtime_identity_contract_cli" runtime-env-defaults)

set_default_env ARGOCD_REPO_CREDENTIALS_REQUIRED "false"
if [[ -z "${RUNTIME_IDENTITY_RECONCILE_REQUIRED+x}" ]]; then
  if [[ "$(normalize_bool "${RUNTIME_CREDENTIALS_REQUIRED:-false}")" == "true" ]] || \
    [[ "$(normalize_bool "${ARGOCD_REPO_CREDENTIALS_REQUIRED:-false}")" == "true" ]]; then
    RUNTIME_IDENTITY_RECONCILE_REQUIRED="true"
  else
    RUNTIME_IDENTITY_RECONCILE_REQUIRED="false"
  fi
fi

RUNTIME_IDENTITY_RECONCILE_REQUIRED_NORMALIZED="$(normalize_bool "$RUNTIME_IDENTITY_RECONCILE_REQUIRED")"
KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED_NORMALIZED="$(
  normalize_bool "${KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED:-true}"
)"

declare -a RUNTIME_IDENTITY_ISSUES=()
record_issue() {
  local message="$1"
  if [[ "$RUNTIME_IDENTITY_RECONCILE_REQUIRED_NORMALIZED" == "true" ]]; then
    log_error "$message"
  else
    log_warn "$message"
  fi
  RUNTIME_IDENTITY_ISSUES+=("$message")
}

plugin_eso_status="skipped"
plugin_argocd_repo_status="skipped"
plugin_keycloak_contract_status="skipped"
keycloak_checked_realms="none"
keycloak_realm_check_count=0
keycloak_contract_expected_count=0

if run_cmd "$reconcile_eso_script"; then
  plugin_eso_status="success"
else
  plugin_eso_status="failure"
  record_issue "eso runtime credential reconciliation failed"
fi

if RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE=true run_cmd "$reconcile_argocd_script"; then
  plugin_argocd_repo_status="success"
else
  plugin_argocd_repo_status="failure"
  record_issue "argocd repository credential reconciliation failed"
fi

if [[ "$KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED_NORMALIZED" == "false" ]]; then
  plugin_keycloak_contract_status="skipped-toggle-disabled"
else
  keycloak_issue_count_before="${#RUNTIME_IDENTITY_ISSUES[@]}"
  declare -a eso_contract_ids=()
  while IFS=$'\t' read -r contract_id _module_id _namespace _external_secret _target_secret _target_keys; do
    [[ -n "$contract_id" ]] || continue
    eso_contract_ids+=("$contract_id")
  done < <(python3 "$runtime_identity_contract_cli" eso-contracts)

  keycloak_checked_realms=""
  while IFS=$'\t' read -r realm_id module_id realm_env _default_realm resolved_realm _display client_id_env client_secret_env _admin_user_env _admin_password_env; do
    [[ -n "$realm_id" ]] || continue

    if [[ -n "$module_id" ]] && ! is_module_enabled "$module_id"; then
      continue
    fi

    keycloak_realm_check_count=$((keycloak_realm_check_count + 1))
    if [[ -z "$keycloak_checked_realms" ]]; then
      keycloak_checked_realms="$realm_id"
    else
      keycloak_checked_realms+=",${realm_id}"
    fi

    if [[ -z "$resolved_realm" ]]; then
      record_issue "keycloak realm contract unresolved realm name for realm_id=$realm_id (env=$realm_env)"
    fi
    if [[ -z "$client_id_env" || -z "$client_secret_env" ]]; then
      record_issue "keycloak realm contract missing client env refs for realm_id=$realm_id"
    fi

    expected_contract_id="${realm_id}-runtime-credentials"
    keycloak_contract_expected_count=$((keycloak_contract_expected_count + 1))
    found_contract="false"
    for contract_id in "${eso_contract_ids[@]-}"; do
      if [[ "$contract_id" == "$expected_contract_id" ]]; then
        found_contract="true"
        break
      fi
    done
    if [[ "$found_contract" != "true" ]]; then
      record_issue "missing ESO contract id=$expected_contract_id required by keycloak realm_id=$realm_id"
    fi
  done < <(python3 "$runtime_identity_contract_cli" keycloak-realms)

  if [[ -z "$keycloak_checked_realms" ]]; then
    keycloak_checked_realms="none"
    plugin_keycloak_contract_status="skipped-no-enabled-realm-contracts"
  elif (( ${#RUNTIME_IDENTITY_ISSUES[@]} > keycloak_issue_count_before )); then
    plugin_keycloak_contract_status="failure"
  else
    plugin_keycloak_contract_status="success"
  fi
fi

status="success"
if [[ "$plugin_eso_status" == "failure" || "$plugin_argocd_repo_status" == "failure" || "$plugin_keycloak_contract_status" == "failure" ]]; then
  status="failed-plugin"
elif (( ${#RUNTIME_IDENTITY_ISSUES[@]} > 0 )); then
  if [[ "$RUNTIME_IDENTITY_RECONCILE_REQUIRED_NORMALIZED" == "true" ]]; then
    status="failed-required"
  else
    status="success-with-warnings"
  fi
fi

runtime_credentials_state="none"
if state_file_exists runtime_credentials_eso_reconcile; then
  runtime_credentials_state="$(state_file_path runtime_credentials_eso_reconcile)"
fi

argocd_repo_state="none"
if state_file_exists argocd_repo_credentials_reconcile; then
  argocd_repo_state="$(state_file_path argocd_repo_credentials_reconcile)"
fi

log_metric \
  "runtime_identity_reconcile_total" \
  "1" \
  "profile=$BLUEPRINT_PROFILE mode=$(tooling_execution_mode) status=$status required=$RUNTIME_IDENTITY_RECONCILE_REQUIRED_NORMALIZED issue_count=${#RUNTIME_IDENTITY_ISSUES[@]}"

state_file="$(
  write_state_file "runtime_identity_reconcile" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "required=$RUNTIME_IDENTITY_RECONCILE_REQUIRED_NORMALIZED" \
    "status=$status" \
    "plugin_eso_status=$plugin_eso_status" \
    "plugin_argocd_repo_status=$plugin_argocd_repo_status" \
    "plugin_keycloak_contract_status=$plugin_keycloak_contract_status" \
    "keycloak_optional_module_toggle=$KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED_NORMALIZED" \
    "keycloak_checked_realms=$keycloak_checked_realms" \
    "keycloak_realm_check_count=$keycloak_realm_check_count" \
    "keycloak_expected_contract_count=$keycloak_contract_expected_count" \
    "runtime_credentials_state=$runtime_credentials_state" \
    "argocd_repo_state=$argocd_repo_state" \
    "issue_count=${#RUNTIME_IDENTITY_ISSUES[@]}" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "runtime identity reconcile state written to $state_file"

if (( ${#RUNTIME_IDENTITY_ISSUES[@]} > 0 )); then
  for issue in "${RUNTIME_IDENTITY_ISSUES[@]}"; do
    log_warn "runtime identity reconcile issue: $issue"
  done
fi

if [[ "$status" == failed-* ]]; then
  exit 1
fi

exit 0
