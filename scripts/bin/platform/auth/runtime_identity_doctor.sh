#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "platform_auth_runtime_identity_doctor"

usage() {
  cat <<'USAGE'
Usage: runtime_identity_doctor.sh

Runs consolidated runtime identity diagnostics across:
- runtime identity orchestrator reconciliation state,
- ESO runtime target-secret verification diagnostics,
- ArgoCD repository credentials reconciliation state,
- runtime identity contract coverage (enabled ESO contracts + Keycloak realms).

Contract knobs:
- RUNTIME_IDENTITY_DOCTOR_REFRESH (default: true; when true, runs runtime identity reconcile before diagnostics)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
runtime_identity_reconcile_script="$ROOT_DIR/scripts/bin/platform/auth/reconcile_runtime_identity.sh"
runtime_identity_contract_cli="$ROOT_DIR/scripts/lib/infra/runtime_identity_contract.py"
runtime_identity_doctor_helpers="$ROOT_DIR/scripts/lib/platform/auth/runtime_identity_doctor_json.py"

set_default_env RUNTIME_IDENTITY_DOCTOR_REFRESH "true"
runtime_identity_doctor_refresh_normalized="$(normalize_bool "$RUNTIME_IDENTITY_DOCTOR_REFRESH")"

refresh_status="skipped"
if [[ "$runtime_identity_doctor_refresh_normalized" == "true" ]]; then
  if run_cmd "$runtime_identity_reconcile_script"; then
    refresh_status="success"
  else
    refresh_status="failed"
  fi
fi

runtime_identity_state_path="none"
if state_file_exists runtime_identity_reconcile; then
  runtime_identity_state_path="$(state_file_path runtime_identity_reconcile)"
fi

runtime_credentials_state_path="none"
if state_file_exists runtime_credentials_eso_reconcile; then
  runtime_credentials_state_path="$(state_file_path runtime_credentials_eso_reconcile)"
fi

argocd_repo_state_path="none"
if state_file_exists argocd_repo_credentials_reconcile; then
  argocd_repo_state_path="$(state_file_path argocd_repo_credentials_reconcile)"
fi

target_secret_report_path="$ROOT_DIR/artifacts/infra/runtime_credentials_eso_target_secret_checks.json"
if [[ ! -f "$target_secret_report_path" ]]; then
  target_secret_report_path="none"
fi

contract_eso_expected_count=0
contract_eso_enabled_count=0
declare -a contract_eso_enabled_contracts=()

while IFS=$'\t' read -r contract_id contract_module _namespace _external_secret _target_secret _target_keys; do
  [[ -n "$contract_id" ]] || continue
  contract_eso_expected_count=$((contract_eso_expected_count + 1))
  if [[ -n "$contract_module" ]] && ! is_module_enabled "$contract_module"; then
    continue
  fi
  contract_eso_enabled_count=$((contract_eso_enabled_count + 1))
  contract_eso_enabled_contracts+=("$contract_id")
done < <(python3 "$runtime_identity_contract_cli" eso-contracts)

contract_keycloak_expected_count=0
contract_keycloak_enabled_count=0
declare -a contract_keycloak_enabled_realms=()

while IFS=$'\t' read -r realm_id module_id _realm_env _default_realm _resolved_realm _display _client_id _client_secret _admin_user _admin_password; do
  [[ -n "$realm_id" ]] || continue
  contract_keycloak_expected_count=$((contract_keycloak_expected_count + 1))
  if [[ -n "$module_id" ]] && ! is_module_enabled "$module_id"; then
    continue
  fi
  contract_keycloak_enabled_count=$((contract_keycloak_enabled_count + 1))
  contract_keycloak_enabled_realms+=("$realm_id")
done < <(python3 "$runtime_identity_contract_cli" keycloak-realms)

contract_eso_enabled_contracts_csv="none"
if (( ${#contract_eso_enabled_contracts[@]} > 0 )); then
  contract_eso_enabled_contracts_csv="$(IFS=,; printf '%s' "${contract_eso_enabled_contracts[*]}")"
fi

contract_keycloak_enabled_realms_csv="none"
if (( ${#contract_keycloak_enabled_realms[@]} > 0 )); then
  contract_keycloak_enabled_realms_csv="$(IFS=,; printf '%s' "${contract_keycloak_enabled_realms[*]}")"
fi

doctor_report_path="$ROOT_DIR/artifacts/infra/runtime_identity_doctor_report.json"
doctor_summary="$(
  python3 "$runtime_identity_doctor_helpers" render-report \
    --output "$doctor_report_path" \
    --profile "$BLUEPRINT_PROFILE" \
    --stack "$(active_stack)" \
    --tooling-mode "$(tooling_execution_mode)" \
    --refresh-status "$refresh_status" \
    --runtime-identity-state "$runtime_identity_state_path" \
    --runtime-credentials-state "$runtime_credentials_state_path" \
    --argocd-state "$argocd_repo_state_path" \
    --target-secret-report "$target_secret_report_path" \
    --contract-eso-expected "$contract_eso_expected_count" \
    --contract-eso-enabled "$contract_eso_enabled_count" \
    --contract-keycloak-expected "$contract_keycloak_expected_count" \
    --contract-keycloak-enabled "$contract_keycloak_enabled_count" \
    --contract-eso-enabled-contracts "$contract_eso_enabled_contracts_csv" \
    --contract-keycloak-enabled-realms "$contract_keycloak_enabled_realms_csv"
)"

IFS=$'\t' read -r \
  doctor_status \
  doctor_issue_count \
  doctor_failure_count \
  doctor_warning_count \
  doctor_target_total \
  doctor_target_ready \
  doctor_target_missing_secret \
  doctor_target_missing_keys \
  doctor_target_verify_error <<<"$doctor_summary"

doctor_status="${doctor_status:-failed}"
doctor_issue_count="${doctor_issue_count:-0}"
doctor_failure_count="${doctor_failure_count:-0}"
doctor_warning_count="${doctor_warning_count:-0}"
doctor_target_total="${doctor_target_total:-0}"
doctor_target_ready="${doctor_target_ready:-0}"
doctor_target_missing_secret="${doctor_target_missing_secret:-0}"
doctor_target_missing_keys="${doctor_target_missing_keys:-0}"
doctor_target_verify_error="${doctor_target_verify_error:-0}"

log_metric \
  "runtime_identity_doctor_total" \
  "1" \
  "profile=$BLUEPRINT_PROFILE mode=$(tooling_execution_mode) status=$doctor_status refresh=$refresh_status issue_count=$doctor_issue_count"

state_file="$(
  write_state_file "runtime_identity_doctor" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "refresh_requested=$runtime_identity_doctor_refresh_normalized" \
    "refresh_status=$refresh_status" \
    "status=$doctor_status" \
    "issue_count=$doctor_issue_count" \
    "failure_count=$doctor_failure_count" \
    "warning_count=$doctor_warning_count" \
    "runtime_identity_state=$runtime_identity_state_path" \
    "runtime_credentials_state=$runtime_credentials_state_path" \
    "argocd_repo_state=$argocd_repo_state_path" \
    "target_secret_report=$target_secret_report_path" \
    "target_secret_total=$doctor_target_total" \
    "target_secret_ready=$doctor_target_ready" \
    "target_secret_missing_secret=$doctor_target_missing_secret" \
    "target_secret_missing_keys=$doctor_target_missing_keys" \
    "target_secret_verify_error=$doctor_target_verify_error" \
    "contract_eso_expected_count=$contract_eso_expected_count" \
    "contract_eso_enabled_count=$contract_eso_enabled_count" \
    "contract_eso_enabled_contracts=$contract_eso_enabled_contracts_csv" \
    "contract_keycloak_expected_count=$contract_keycloak_expected_count" \
    "contract_keycloak_enabled_count=$contract_keycloak_enabled_count" \
    "contract_keycloak_enabled_realms=$contract_keycloak_enabled_realms_csv" \
    "report_path=$doctor_report_path" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "runtime identity doctor state written to $state_file"
log_info "runtime identity doctor report written to $doctor_report_path"

if [[ "$doctor_status" == "failed" ]]; then
  exit 1
fi

exit 0
