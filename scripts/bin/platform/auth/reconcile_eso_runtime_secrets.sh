#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

start_script_metric_trap "platform_auth_reconcile_eso_runtime_secrets"

usage() {
  cat <<'USAGE'
Usage: reconcile_eso_runtime_secrets.sh

Reconciles the canonical ESO runtime credentials contract:
- optional source secret seeding from env literals,
- apply blueprint-owned security manifests,
- wait for ESO CRDs and ExternalSecret readiness,
- verify required target secrets and key contracts.

Contract knobs:
- RUNTIME_CREDENTIALS_SOURCE_NAMESPACE (default: security)
- RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME (default: runtime-credentials-source)
- RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS (default: empty, format: key=value\nkey2=value2, newline-separated only)
- RUNTIME_CREDENTIALS_TARGET_NAMESPACE (default: apps)
- RUNTIME_CREDENTIALS_TARGET_SECRET_NAME (default: runtime-credentials)
- RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS (default: username,password)
- RUNTIME_CREDENTIALS_ESO_STORE_KIND (default: ClusterSecretStore)
- RUNTIME_CREDENTIALS_ESO_STORE_NAME (default: runtime-credentials-source-store)
- RUNTIME_CREDENTIALS_ESO_EXTERNAL_SECRET_NAME (default: runtime-credentials)
- RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT (default: 180)
- RUNTIME_CREDENTIALS_REQUIRED (default: false)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
runtime_identity_contract_cli="$ROOT_DIR/scripts/lib/infra/runtime_identity_contract.py"
runtime_secret_json_helpers="$ROOT_DIR/scripts/lib/platform/auth/runtime_secret_keys_json.py"

while IFS=$'\t' read -r env_name env_default; do
  [[ -n "$env_name" ]] || continue
  set_default_env "$env_name" "$env_default"
done < <(python3 "$runtime_identity_contract_cli" runtime-env-defaults)

set_default_env RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME "runtime-credentials-source"
set_default_env RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS ""
set_default_env RUNTIME_CREDENTIALS_TARGET_SECRET_NAME "runtime-credentials"
set_default_env RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS "username,password"
set_default_env RUNTIME_CREDENTIALS_ESO_STORE_KIND "ClusterSecretStore"
set_default_env RUNTIME_CREDENTIALS_ESO_STORE_NAME "runtime-credentials-source-store"
set_default_env RUNTIME_CREDENTIALS_ESO_EXTERNAL_SECRET_NAME "runtime-credentials"

RUNTIME_CREDENTIALS_REQUIRED_NORMALIZED="$(normalize_bool "$RUNTIME_CREDENTIALS_REQUIRED")"

runtime_wait_timeout="$RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT"
if ! [[ "$runtime_wait_timeout" =~ ^[0-9]+$ ]] || (( runtime_wait_timeout <= 0 )); then
  log_warn "invalid RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT=$RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT; using 180"
  runtime_wait_timeout=180
fi

trim_whitespace() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

wait_for_crd_established() {
  local crd_name="$1"
  local timeout_seconds="$2"
  local started_at now elapsed conditions

  started_at="$(date +%s)"
  while true; do
    conditions="$(kubectl get "crd/$crd_name" -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' 2>/dev/null || true)"
    if printf '%s\n' "$conditions" | grep -qx 'Established=True'; then
      return 0
    fi
    now="$(date +%s)"
    elapsed="$((now - started_at))"
    if (( elapsed >= timeout_seconds )); then
      return 1
    fi
    sleep 2
  done
}

wait_for_external_secret_ready() {
  local namespace="$1"
  local name="$2"
  local timeout_seconds="$3"
  local started_at now elapsed conditions

  started_at="$(date +%s)"
  while true; do
    if kubectl -n "$namespace" get externalsecret "$name" >/dev/null 2>&1; then
      conditions="$(kubectl -n "$namespace" get externalsecret "$name" -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' 2>/dev/null || true)"
      if printf '%s\n' "$conditions" | grep -qx 'Ready=True'; then
        return 0
      fi
    fi
    now="$(date +%s)"
    elapsed="$((now - started_at))"
    if (( elapsed >= timeout_seconds )); then
      return 1
    fi
    sleep 2
  done
}

sanitize_diagnostics_token() {
  local value="$1"
  printf '%s' "${value//[^a-zA-Z0-9_.-]/_}"
}

target_secret_check_diagnostics_path() {
  local namespace="$1"
  local secret_name="$2"
  local namespace_token secret_token
  namespace_token="$(sanitize_diagnostics_token "$namespace")"
  secret_token="$(sanitize_diagnostics_token "$secret_name")"
  printf '%s/%s__%s.json' "$target_secret_diagnostics_dir" "$namespace_token" "$secret_token"
}

verify_target_secret_keys() {
  local namespace="$1"
  local secret_name="$2"
  local keys_csv="$3"
  local diagnostics_output_path="$4"
  local secret_json checker_output checker_status
  local check_status check_missing_keys check_reason

  set +e
  if run_kubectl_with_active_access -n "$namespace" get secret "$secret_name" >/dev/null 2>&1; then
    secret_json="$(run_kubectl_capture_stdout_with_active_access -n "$namespace" get secret "$secret_name" -o json 2>/dev/null || true)"
    checker_output="$(
      printf '%s' "$secret_json" | \
        python3 "$runtime_secret_json_helpers" check-target-secret \
          --namespace "$namespace" \
          --secret-name "$secret_name" \
          --required-keys "$keys_csv" \
          --summary \
          --output-json "$diagnostics_output_path" 2>/dev/null
    )"
    checker_status=$?
  else
    checker_output="$(
      python3 "$runtime_secret_json_helpers" check-target-secret \
        --namespace "$namespace" \
        --secret-name "$secret_name" \
        --required-keys "$keys_csv" \
        --secret-present false \
        --summary \
        --output-json "$diagnostics_output_path" 2>/dev/null
    )"
    checker_status=$?
  fi
  set -e

  if [[ -z "$checker_output" ]]; then
    printf '__verify_error__:target-secret-checker-empty-output\n'
    return 1
  fi

  IFS=$'\t' read -r check_status check_missing_keys check_reason <<<"$checker_output"
  check_status="${check_status:-verify-error}"
  check_missing_keys="${check_missing_keys:-none}"
  check_reason="${check_reason:-unknown-checker-error}"

  case "$check_status" in
    ready)
      printf 'ok\n'
      return 0
      ;;
    missing-secret)
      printf '__missing_secret__\n'
      return 1
      ;;
    missing-keys)
      if [[ "$check_missing_keys" == "none" ]]; then
        printf '__verify_error__:missing-keys-without-list\n'
        return 1
      fi
      printf '%s\n' "${check_missing_keys//,/ }"
      return 1
      ;;
    verify-error)
      printf '__verify_error__:%s\n' "$check_reason"
      return 1
      ;;
    *)
      printf '__verify_error__:unexpected-checker-status:%s\n' "$check_status"
      if (( checker_status != 0 )); then
        return "$checker_status"
      fi
      return 1
      ;;
  esac
}

local_lite_postgres_runtime_ready() {
  if [[ "${BLUEPRINT_PROFILE:-}" != "local-lite" ]]; then
    return 1
  fi
  if ! is_module_enabled postgres; then
    return 1
  fi
  if ! state_file_exists postgres_runtime; then
    return 1
  fi
  local runtime_state_file
  runtime_state_file="$(state_file_path postgres_runtime)"
  # Guard against stale cross-profile artifacts: only trust local-lite/local state ownership.
  if ! grep -q '^profile=local-lite$' "$runtime_state_file" 2>/dev/null; then
    return 1
  fi
  if ! grep -q '^stack=local$' "$runtime_state_file" 2>/dev/null; then
    return 1
  fi
  if ! grep -q '^dsn=postgresql://' "$runtime_state_file" 2>/dev/null; then
    return 1
  fi
  return 0
}

should_skip_eso_contract_check() {
  local contract_id="$1"
  local contract_module="$2"

  if [[ "$contract_id" == "postgres-runtime-credentials" && "$contract_module" == "postgres" ]]; then
    if local_lite_postgres_runtime_ready; then
      return 0
    fi
  fi
  return 1
}

parse_literal_pairs() {
  local literals="$1"
  local pair key value
  [[ -n "$literals" ]] || return 0

  # Guard: detect likely old comma-separated format on single-line input.
  # When comma-split produces >1 element AND any element beyond the first
  # looks like <identifier>=<non-empty-value>, the input is the deprecated
  # comma-separated format. Base64-padded values end with "=" but have an
  # empty value portion, so they are not flagged as false positives.
  if [[ "$literals" != *$'\n'* ]]; then
    local -a _csv_parts
    IFS=',' read -r -a _csv_parts <<< "$literals"
    if (( ${#_csv_parts[@]} > 1 )); then
      local _cp _cp_key _cp_val _detected_csv=false
      for _cp in "${_csv_parts[@]:1}"; do
        _cp="$(trim_whitespace "$_cp")"
        _cp_key="${_cp%%=*}"
        _cp_val="${_cp#*=}"
        if [[ "$_cp" == *=* && -n "$_cp_val" && "$_cp_key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
          _detected_csv=true
          break
        fi
      done
      if [[ "$_detected_csv" == "true" ]]; then
        log_warn "parse_literal_pairs: input looks like comma-separated format (no longer supported)"
        log_warn "parse_literal_pairs: use newline-separated key=value pairs (one per line)"
        return 1
      fi
    fi
  fi

  while IFS= read -r pair; do
    pair="$(trim_whitespace "$pair")"
    [[ -n "$pair" ]] || continue
    if [[ "$pair" != *=* ]]; then
      log_warn "parse_literal_pairs: invalid pair (missing '='): $pair"
      log_warn "parse_literal_pairs: expected format: key=value (one per line)"
      return 1
    fi
    key="$(trim_whitespace "${pair%%=*}")"
    value="${pair#*=}"
    if [[ -z "$key" || -z "$value" ]]; then
      log_warn "parse_literal_pairs: empty key or value in pair: $pair"
      return 1
    fi
    printf '%s\n' "$key=$value"
  done <<< "$literals"
}

record_reconcile_issue() {
  local message="$1"
  if [[ "$RUNTIME_CREDENTIALS_REQUIRED_NORMALIZED" == "true" ]]; then
    log_error "$message"
  else
    log_warn "$message"
  fi
  RUNTIME_RECONCILE_ISSUES+=("$message")
}

register_eso_secret_contract() {
  local namespace="$1"
  local external_secret="$2"
  local target_secret="$3"
  local target_keys="$4"
  ESO_SECRET_CONTRACTS+=("${namespace}|${external_secret}|${target_secret}|${target_keys}")
}

eso_secret_contract_count() {
  if ! declare -p ESO_SECRET_CONTRACTS >/dev/null 2>&1; then
    printf '0'
    return 0
  fi
  printf '%s' "${#ESO_SECRET_CONTRACTS[@]}"
}

RUNTIME_RECONCILE_ISSUES=()
source_seed_mode="not-requested"
apply_mode="kustomize-dry-run"
crd_status="skipped"
external_secret_status="skipped"
target_secret_status="skipped"
target_missing_keys=""
source_secret_present="unknown"
external_secret_checked=""
target_secret_checked=""
target_secret_diagnostics_dir="$ROOT_DIR/artifacts/infra/runtime_credentials_eso_target_secret_checks"
target_secret_diagnostics_report="$ROOT_DIR/artifacts/infra/runtime_credentials_eso_target_secret_checks.json"
target_secret_diagnostics_count="0"
declare -a ESO_SECRET_CONTRACTS=()
declare -a ESO_SECRET_CONTRACTS_SKIPPED=()
declare -a TARGET_SECRET_CHECK_DIAGNOSTIC_FILES=()
skipped_contract_count="0"
skipped_contracts="none"

mkdir -p "$target_secret_diagnostics_dir"
rm -f "$target_secret_diagnostics_dir"/*.json "$target_secret_diagnostics_report"

while IFS='|' read -r contract_id contract_module contract_namespace contract_external_secret contract_target_secret contract_target_keys; do
  [[ -n "$contract_id" ]] || continue

  if [[ -n "$contract_module" ]] && ! is_module_enabled "$contract_module"; then
    continue
  fi

  if should_skip_eso_contract_check "$contract_id" "$contract_module"; then
    ESO_SECRET_CONTRACTS_SKIPPED+=("${contract_namespace}/${contract_target_secret}:local-lite-postgres-runtime")
    log_metric \
      "runtime_credentials_eso_contract_skip_total" \
      "1" \
      "contract_id=$contract_id module=$contract_module profile=${BLUEPRINT_PROFILE:-unset} reason=local-lite-postgres-runtime"
    log_info \
      "runtime credentials contract check skipped contract_id=$contract_id module=$contract_module reason=local-lite-postgres-runtime"
    continue
  fi

  register_eso_secret_contract \
    "$contract_namespace" \
    "$contract_external_secret" \
    "$contract_target_secret" \
    "$contract_target_keys"
done < <(python3 "$runtime_identity_contract_cli" eso-contracts | tr $'\t' '|')

if (( ${#ESO_SECRET_CONTRACTS_SKIPPED[@]} > 0 )); then
  skipped_contract_count="${#ESO_SECRET_CONTRACTS_SKIPPED[@]}"
  skipped_contracts="$(IFS=,; printf '%s' "${ESO_SECRET_CONTRACTS_SKIPPED[*]}")"
fi

eso_contract_count="$(eso_secret_contract_count)"
status="success"
if (( eso_contract_count == 0 )); then
  status="noop-empty-contract-set"
  apply_mode="skipped-empty-contract-set"
  source_seed_mode="skipped-empty-contract-set"
  source_secret_present="not-applicable"
  crd_status="not-applicable"
  external_secret_status="not-applicable"
  target_secret_status="not-applicable"
  target_missing_keys="none"
  external_secret_checked="none"
  target_secret_checked="none"
  log_info "runtime credential contract set empty; skipping source secret checks"
else
  if tooling_is_execution_enabled; then
    apply_mode="kubectl-apply-kustomize"
  fi
  # Guard with 'if !' so set -e cannot abort before the state file is written.
  # On failure with RUNTIME_CREDENTIALS_REQUIRED=false the issue is captured as a
  # warning; with RUNTIME_CREDENTIALS_REQUIRED=true the end-of-script log_fatal fires.
  if ! run_kustomize_apply "$ROOT_DIR/infra/gitops/platform/base/security"; then
    apply_mode="kubectl-apply-kustomize-failed"
    record_reconcile_issue \
      "security manifest apply failed; target namespaces may not exist yet (infra/gitops/platform/base/security)"
  fi

  source_literals=()
  if literal_output="$(parse_literal_pairs "$RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS")"; then
    if [[ -n "$literal_output" ]]; then
      while IFS= read -r literal_pair; do
        [[ -n "$literal_pair" ]] || continue
        source_literals+=("$literal_pair")
      done <<<"$literal_output"
    fi
  else
    record_reconcile_issue "invalid RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS format; expected key=value (one per line, newline-separated)"
  fi

  if (( ${#source_literals[@]} > 0 )); then
    source_seed_mode="manifest-rendered"
    if tooling_is_execution_enabled; then
      source_seed_mode="kubectl-apply"
    fi
    apply_optional_module_secret_from_literals \
      "$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE" \
      "$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME" \
      "${source_literals[@]}"
  elif tooling_is_execution_enabled; then
    if kubectl -n "$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE" get secret "$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME" >/dev/null 2>&1; then
      source_seed_mode="existing-source-secret"
      source_secret_present="true"
    else
      source_seed_mode="missing-source-secret"
      source_secret_present="false"
      record_reconcile_issue \
        "source secret ${RUNTIME_CREDENTIALS_SOURCE_NAMESPACE}/${RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME} missing and no literals provided"
    fi
  fi

  if tooling_is_execution_enabled; then
    require_command kubectl

    if wait_for_crd_established "clustersecretstores.external-secrets.io" "$runtime_wait_timeout" \
      && wait_for_crd_established "externalsecrets.external-secrets.io" "$runtime_wait_timeout"; then
      crd_status="ready"
    else
      crd_status="timeout"
      record_reconcile_issue "ESO CRDs did not report Established=True within ${runtime_wait_timeout}s"
    fi

    external_secret_status="ready"
    target_secret_status="ready"
    target_missing_keys="none"
    external_secret_checked="none"
    target_secret_checked="none"
    for contract_entry in "${ESO_SECRET_CONTRACTS[@]-}"; do
      IFS='|' read -r contract_namespace contract_external_secret contract_target_secret contract_target_keys <<<"$contract_entry"

      if wait_for_external_secret_ready \
        "$contract_namespace" \
        "$contract_external_secret" \
        "$runtime_wait_timeout"; then
        if [[ "$external_secret_checked" == "none" ]]; then
          external_secret_checked="${contract_namespace}/${contract_external_secret}"
        else
          external_secret_checked+=",${contract_namespace}/${contract_external_secret}"
        fi
      else
        external_secret_status="timeout"
        record_reconcile_issue \
          "ExternalSecret ${contract_namespace}/${contract_external_secret} not Ready within ${runtime_wait_timeout}s"
      fi

      target_secret_check_diagnostics_file="$(target_secret_check_diagnostics_path "$contract_namespace" "$contract_target_secret")"
      target_check_output="$(verify_target_secret_keys \
        "$contract_namespace" \
        "$contract_target_secret" \
        "$contract_target_keys" \
        "$target_secret_check_diagnostics_file" || true)"
      if [[ -f "$target_secret_check_diagnostics_file" ]]; then
        TARGET_SECRET_CHECK_DIAGNOSTIC_FILES+=("$target_secret_check_diagnostics_file")
      fi
      if [[ "$target_check_output" == "ok" ]]; then
        if [[ "$target_secret_checked" == "none" ]]; then
          target_secret_checked="${contract_namespace}/${contract_target_secret}"
        else
          target_secret_checked+=",${contract_namespace}/${contract_target_secret}"
        fi
        continue
      fi

      if [[ "$target_check_output" == "__missing_secret__" ]]; then
        target_secret_status="missing"
        if [[ "$target_missing_keys" == "none" ]]; then
          target_missing_keys="${contract_namespace}/${contract_target_secret}:missing"
        else
          target_missing_keys+=",${contract_namespace}/${contract_target_secret}:missing"
        fi
        record_reconcile_issue \
          "target secret ${contract_namespace}/${contract_target_secret} is missing"
        continue
      fi

      if [[ "$target_check_output" == "__verify_error__:"* ]]; then
        target_secret_status="verify-error"
        if [[ "$target_missing_keys" == "none" ]]; then
          target_missing_keys="${contract_namespace}/${contract_target_secret}:verify-error"
        else
          target_missing_keys+=",${contract_namespace}/${contract_target_secret}:verify-error"
        fi
        record_reconcile_issue \
          "target secret ${contract_namespace}/${contract_target_secret} verification error: ${target_check_output#__verify_error__:}"
        continue
      fi

      target_secret_status="missing-keys"
      if [[ "$target_missing_keys" == "none" ]]; then
        target_missing_keys="${contract_namespace}/${contract_target_secret}:${target_check_output}"
      else
        target_missing_keys+=",${contract_namespace}/${contract_target_secret}:${target_check_output}"
      fi
      record_reconcile_issue \
        "target secret ${contract_namespace}/${contract_target_secret} missing key(s): $target_check_output"
    done
  fi

fi

target_secret_diagnostics_count="${#TARGET_SECRET_CHECK_DIAGNOSTIC_FILES[@]}"
if (( target_secret_diagnostics_count > 0 )); then
  if ! python3 "$runtime_secret_json_helpers" render-check-report \
    --output "$target_secret_diagnostics_report" \
    "${TARGET_SECRET_CHECK_DIAGNOSTIC_FILES[@]}" >/dev/null; then
    target_secret_status="verify-error"
    record_reconcile_issue "failed to render runtime target-secret diagnostics report at $target_secret_diagnostics_report"
  fi
else
  if ! python3 "$runtime_secret_json_helpers" render-check-report \
    --output "$target_secret_diagnostics_report" >/dev/null; then
    target_secret_status="verify-error"
    record_reconcile_issue "failed to render runtime target-secret diagnostics report at $target_secret_diagnostics_report"
  fi
fi

if (( ${#RUNTIME_RECONCILE_ISSUES[@]} > 0 )); then
  if [[ "$RUNTIME_CREDENTIALS_REQUIRED_NORMALIZED" == "true" ]]; then
    status="failed-required"
  else
    status="warn-and-skip"
  fi
elif (( eso_contract_count == 0 )); then
  status="noop-empty-contract-set"
else
  status="success"
fi

log_metric \
  "runtime_credentials_eso_reconcile_total" \
  "1" \
  "profile=$BLUEPRINT_PROFILE mode=$(tooling_execution_mode) status=$status required=$RUNTIME_CREDENTIALS_REQUIRED_NORMALIZED issue_count=${#RUNTIME_RECONCILE_ISSUES[@]} contracts=$eso_contract_count"

state_file="$(
  write_state_file "runtime_credentials_eso_reconcile" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "enabled=true" \
    "required=$RUNTIME_CREDENTIALS_REQUIRED_NORMALIZED" \
    "source_namespace=$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE" \
    "source_secret_name=$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME" \
    "source_secret_seed_mode=$source_seed_mode" \
    "source_secret_present=$source_secret_present" \
    "target_namespace=$RUNTIME_CREDENTIALS_TARGET_NAMESPACE" \
    "target_secret_name=$RUNTIME_CREDENTIALS_TARGET_SECRET_NAME" \
    "target_secret_keys=$RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS" \
    "store_kind=$RUNTIME_CREDENTIALS_ESO_STORE_KIND" \
    "store_name=$RUNTIME_CREDENTIALS_ESO_STORE_NAME" \
    "externalsecret_name=$RUNTIME_CREDENTIALS_ESO_EXTERNAL_SECRET_NAME" \
    "externalsecret_checked=$external_secret_checked" \
    "target_secret_checked=$target_secret_checked" \
    "skipped_contract_count=$skipped_contract_count" \
    "skipped_contracts=$skipped_contracts" \
    "wait_timeout_seconds=$runtime_wait_timeout" \
    "apply_mode=$apply_mode" \
    "crd_status=$crd_status" \
    "externalsecret_status=$external_secret_status" \
    "target_secret_status=$target_secret_status" \
    "target_secret_missing_keys=$target_missing_keys" \
    "target_secret_diagnostics_dir=$target_secret_diagnostics_dir" \
    "target_secret_diagnostics_report=$target_secret_diagnostics_report" \
    "target_secret_diagnostics_count=$target_secret_diagnostics_count" \
    "issue_count=${#RUNTIME_RECONCILE_ISSUES[@]}" \
    "status=$status" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

if [[ "$status" == "failed-required" ]]; then
  log_error "runtime credentials ESO reconciliation failed; state written to $state_file"
  log_fatal "RUNTIME_CREDENTIALS_REQUIRED=true and reconciliation checks did not pass"
fi

if [[ "$status" == "warn-and-skip" ]]; then
  log_warn "runtime credentials ESO reconciliation completed with warnings; state written to $state_file"
else
  log_info "runtime credentials ESO reconciliation complete; state written to $state_file"
fi
