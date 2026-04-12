#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

keycloak_reconciliation_enabled() {
  set_default_env KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED "true"
  [[ "$(normalize_bool "$KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED")" == "true" ]]
}

keycloak_identity_contract_load_realm() {
  local realm_id="$1"
  local cli="$ROOT_DIR/scripts/lib/infra/runtime_identity_contract.py"
  local key value

  require_command python3

  KEYCLOAK_IDENTITY_CONTRACT_REALM_ID=""
  KEYCLOAK_IDENTITY_CONTRACT_MODULE_ID=""
  KEYCLOAK_IDENTITY_CONTRACT_REALM_ENV=""
  KEYCLOAK_IDENTITY_CONTRACT_DEFAULT_REALM_NAME=""
  KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME=""
  KEYCLOAK_IDENTITY_CONTRACT_CLIENT_DISPLAY_NAME=""
  KEYCLOAK_IDENTITY_CONTRACT_CLIENT_ID_ENV=""
  KEYCLOAK_IDENTITY_CONTRACT_CLIENT_SECRET_ENV=""
  KEYCLOAK_IDENTITY_CONTRACT_ROLE_NAMES_CSV=""
  KEYCLOAK_IDENTITY_CONTRACT_ADMIN_USERNAME_ENV=""
  KEYCLOAK_IDENTITY_CONTRACT_ADMIN_PASSWORD_ENV=""
  KEYCLOAK_IDENTITY_CONTRACT_ADMIN_ROLE=""

  while IFS='=' read -r key value; do
    case "$key" in
    realm_id) KEYCLOAK_IDENTITY_CONTRACT_REALM_ID="$value" ;;
    module_id) KEYCLOAK_IDENTITY_CONTRACT_MODULE_ID="$value" ;;
    realm_env) KEYCLOAK_IDENTITY_CONTRACT_REALM_ENV="$value" ;;
    default_realm_name) KEYCLOAK_IDENTITY_CONTRACT_DEFAULT_REALM_NAME="$value" ;;
    resolved_realm_name) KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME="$value" ;;
    client_display_name) KEYCLOAK_IDENTITY_CONTRACT_CLIENT_DISPLAY_NAME="$value" ;;
    client_id_env) KEYCLOAK_IDENTITY_CONTRACT_CLIENT_ID_ENV="$value" ;;
    client_secret_env) KEYCLOAK_IDENTITY_CONTRACT_CLIENT_SECRET_ENV="$value" ;;
    role_names_csv) KEYCLOAK_IDENTITY_CONTRACT_ROLE_NAMES_CSV="$value" ;;
    admin_username_env) KEYCLOAK_IDENTITY_CONTRACT_ADMIN_USERNAME_ENV="$value" ;;
    admin_password_env) KEYCLOAK_IDENTITY_CONTRACT_ADMIN_PASSWORD_ENV="$value" ;;
    admin_role) KEYCLOAK_IDENTITY_CONTRACT_ADMIN_ROLE="$value" ;;
    esac
  done < <(python3 "$cli" keycloak-realm --realm-id "$realm_id")

  if [[ -z "$KEYCLOAK_IDENTITY_CONTRACT_REALM_ID" || -z "$KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME" ]]; then
    log_fatal "failed loading Keycloak realm contract for realm_id=$realm_id"
  fi
}

keycloak_find_runtime_pod() {
  local namespace="$1"
  local release_name="$2"

  run_kubectl_capture_with_active_access \
    -n "$namespace" \
    get pod \
    -l "app.kubernetes.io/instance=$release_name" \
    -o jsonpath='{range .items[?(@.status.phase=="Running")]}{.metadata.name}{"\n"}{end}' 2>/dev/null \
    | head -n 1
}

keycloak_reconcile_wait_defaults() {
  set_default_env KEYCLOAK_RUNTIME_WAIT_TIMEOUT_SECONDS "300"
  set_default_env KEYCLOAK_RUNTIME_WAIT_POLL_SECONDS "5"
}

keycloak_wait_for_runtime_pod() {
  local namespace="$1"
  local release_name="$2"
  local timeout_seconds="${3:-}"
  local poll_seconds="${4:-}"
  local started_at now elapsed pod_name

  keycloak_reconcile_wait_defaults
  if [[ -z "$timeout_seconds" ]]; then
    timeout_seconds="$KEYCLOAK_RUNTIME_WAIT_TIMEOUT_SECONDS"
  fi
  if [[ -z "$poll_seconds" ]]; then
    poll_seconds="$KEYCLOAK_RUNTIME_WAIT_POLL_SECONDS"
  fi
  if ! [[ "$timeout_seconds" =~ ^[0-9]+$ ]] || [[ "$timeout_seconds" == "0" ]]; then
    timeout_seconds="300"
  fi
  if ! [[ "$poll_seconds" =~ ^[0-9]+$ ]] || [[ "$poll_seconds" == "0" ]]; then
    poll_seconds="5"
  fi

  started_at="$(date +%s)"
  while true; do
    pod_name="$(keycloak_find_runtime_pod "$namespace" "$release_name")"
    if [[ -n "$pod_name" ]]; then
      elapsed=$(( $(date +%s) - started_at ))
      # This helper is consumed via command substitution, so metrics must not
      # pollute stdout payload (pod name).
      log_metric "keycloak_runtime_pod_wait_seconds" "$elapsed" "namespace=$namespace release=$release_name status=ready" >&2
      printf '%s' "$pod_name"
      return 0
    fi

    now="$(date +%s)"
    elapsed=$((now - started_at))
    if (( elapsed >= timeout_seconds )); then
      log_metric \
        "keycloak_runtime_pod_wait_seconds" \
        "$elapsed" \
        "namespace=$namespace release=$release_name status=timeout" >&2
      return 1
    fi
    sleep "$poll_seconds"
  done
}

keycloak_read_secret_key() {
  local namespace="$1"
  local secret_name="$2"
  local key_name="$3"
  local encoded=""

  encoded="$(run_kubectl_capture_stdout_with_active_access -n "$namespace" get secret "$secret_name" -o "jsonpath={.data.${key_name}}" 2>/dev/null || true)"
  if [[ -z "$encoded" ]]; then
    return 1
  fi
  printf '%s' "$encoded" | base64 --decode
}

keycloak_reconcile_oidc_identity_contract() {
  local namespace="$1"
  local release_name="$2"
  local admin_secret_name="$3"
  local realm_name="$4"
  local client_id="$5"
  local client_secret="$6"
  local redirect_uris_csv="$7"
  local web_origins_csv="$8"
  local role_names_csv="$9"
  local admin_username="${10:-}"
  local admin_password="${11:-}"
  local admin_role="${12:-Admin}"
  local client_display_name="${13:-$client_id}"

  if ! keycloak_reconciliation_enabled; then
    log_metric \
      "keycloak_identity_contract_reconcile_total" \
      "1" \
      "namespace=$namespace realm=$realm_name client_id=$client_id status=disabled"
    log_info "runtime credentials reconciliation disabled; skipping Keycloak identity contract for realm=$realm_name client_id=$client_id"
    return 0
  fi

  if ! tooling_is_execution_enabled; then
    log_metric \
      "keycloak_identity_contract_reconcile_total" \
      "1" \
      "namespace=$namespace realm=$realm_name client_id=$client_id status=dry_run"
    log_info "dry-run Keycloak identity reconciliation realm=$realm_name client_id=$client_id"
    return 0
  fi

  require_command kubectl

  local pod_name=""
  pod_name="$(keycloak_wait_for_runtime_pod "$namespace" "$release_name" || true)"
  if [[ -z "$pod_name" ]]; then
    log_metric \
      "keycloak_identity_contract_reconcile_total" \
      "1" \
      "namespace=$namespace realm=$realm_name client_id=$client_id status=failed_no_runtime_pod"
    log_fatal "unable to locate running Keycloak pod in namespace=$namespace release=$release_name after ${KEYCLOAK_RUNTIME_WAIT_TIMEOUT_SECONDS}s"
  fi

  local keycloak_admin_password=""
  keycloak_admin_password="$(keycloak_read_secret_key "$namespace" "$admin_secret_name" "KEYCLOAK_ADMIN_PASSWORD" || true)"
  if [[ -z "$keycloak_admin_password" ]]; then
    log_metric \
      "keycloak_identity_contract_reconcile_total" \
      "1" \
      "namespace=$namespace realm=$realm_name client_id=$client_id status=failed_missing_admin_password"
    log_fatal "unable to resolve KEYCLOAK_ADMIN_PASSWORD from ${namespace}/${admin_secret_name}"
  fi

  if [[ -z "$client_secret" ]]; then
    log_metric \
      "keycloak_identity_contract_reconcile_total" \
      "1" \
      "namespace=$namespace realm=$realm_name client_id=$client_id status=failed_missing_client_secret"
    log_fatal "missing client secret for Keycloak identity reconciliation client_id=$client_id"
  fi

  # Reconcile directly inside the Keycloak runtime pod so identity bootstrap does
  # not depend on external ingress/DNS readiness.
  run_kubectl_with_active_access -n "$namespace" exec "$pod_name" -- env \
    KC_REALM_NAME="$realm_name" \
    KC_CLIENT_ID="$client_id" \
    KC_CLIENT_SECRET="$client_secret" \
    KC_REDIRECT_URIS_CSV="$redirect_uris_csv" \
    KC_WEB_ORIGINS_CSV="$web_origins_csv" \
    KC_ROLE_NAMES_CSV="$role_names_csv" \
    KC_ADMIN_USERNAME="$admin_username" \
    KC_ADMIN_PASSWORD="$admin_password" \
    KC_ADMIN_ROLE="$admin_role" \
    KC_CLIENT_DISPLAY_NAME="$client_display_name" \
    KEYCLOAK_ADMIN_PASSWORD="$keycloak_admin_password" \
    bash -euc '
      resolve_kcadm_bin() {
        if [[ -x "/opt/keycloak/bin/kcadm.sh" ]]; then
          printf "%s" "/opt/keycloak/bin/kcadm.sh"
          return 0
        fi
        command -v kcadm.sh >/dev/null 2>&1 && command -v kcadm.sh && return 0
        echo "unable to locate kcadm.sh in Keycloak container" >&2
        return 1
      }

      csv_first_column() {
        local line=""
        while IFS= read -r line; do
          line="${line%%$'"'\r'"'}"
          line="${line#${line%%[![:space:]]*}}"
          line="${line%${line##*[![:space:]]}}"
          if [[ -z "${line}" || "${line}" == "id" ]]; then
            continue
          fi
          printf "%s" "${line%%,*}"
          return 0
        done
        return 1
      }

      csv_to_json_array() {
        local csv="$1"
        local rendered="["
        local raw item escaped
        IFS="," read -r -a raw <<<"${csv}"
        for item in "${raw[@]}"; do
          item="${item#${item%%[![:space:]]*}}"
          item="${item%${item##*[![:space:]]}}"
          [[ -n "${item}" ]] || continue
          escaped="${item//\\/\\\\}"
          escaped="${escaped//\"/\\\"}"
          if [[ "${rendered}" != "[" ]]; then
            rendered+=","
          fi
          rendered+="\"${escaped}\""
        done
        rendered+="]"
        printf "%s" "${rendered}"
      }

      resolve_client_internal_id() {
        "${KCADM}" get clients \
          --config "${KCADM_CONFIG_FILE}" \
          -r "${KC_REALM_NAME}" \
          -q "clientId=${KC_CLIENT_ID}" \
          --fields id \
          --format csv \
          --noquotes 2>/dev/null \
          | csv_first_column || true
      }

      resolve_user_internal_id() {
        "${KCADM}" get users \
          --config "${KCADM_CONFIG_FILE}" \
          -r "${KC_REALM_NAME}" \
          -q "username=${KC_ADMIN_USERNAME}" \
          --fields id \
          --format csv \
          --noquotes 2>/dev/null \
          | csv_first_column || true
      }

      KCADM="$(resolve_kcadm_bin)"
      KCADM_CONFIG_FILE="/tmp/kcadm.config"
      "${KCADM}" config credentials \
        --config "${KCADM_CONFIG_FILE}" \
        --server "http://127.0.0.1:8080" \
        --realm "master" \
        --user "admin" \
        --password "${KEYCLOAK_ADMIN_PASSWORD}" >/dev/null

      if ! "${KCADM}" get "realms/${KC_REALM_NAME}" --config "${KCADM_CONFIG_FILE}" >/dev/null 2>&1; then
        "${KCADM}" create realms \
          --config "${KCADM_CONFIG_FILE}" \
          -s "realm=${KC_REALM_NAME}" \
          -s enabled=true \
          -s sslRequired=external \
          -s loginWithEmailAllowed=true \
          -s duplicateEmailsAllowed=false >/dev/null
      fi

      redirect_uris_json="$(csv_to_json_array "${KC_REDIRECT_URIS_CSV}")"
      web_origins_json="$(csv_to_json_array "${KC_WEB_ORIGINS_CSV}")"
      client_internal_id="$(resolve_client_internal_id)"

      if [[ -z "${client_internal_id}" ]]; then
        "${KCADM}" create clients \
          --config "${KCADM_CONFIG_FILE}" \
          -r "${KC_REALM_NAME}" \
          -s "clientId=${KC_CLIENT_ID}" \
          -s "name=${KC_CLIENT_DISPLAY_NAME}" \
          -s "enabled=true" \
          -s "protocol=openid-connect" \
          -s "publicClient=false" \
          -s "secret=${KC_CLIENT_SECRET}" \
          -s "standardFlowEnabled=true" \
          -s "directAccessGrantsEnabled=true" \
          -s "serviceAccountsEnabled=false" \
          -s "redirectUris=${redirect_uris_json}" \
          -s "webOrigins=${web_origins_json}" >/dev/null
      else
        "${KCADM}" update "clients/${client_internal_id}" \
          --config "${KCADM_CONFIG_FILE}" \
          -r "${KC_REALM_NAME}" \
          -s "enabled=true" \
          -s "secret=${KC_CLIENT_SECRET}" \
          -s "redirectUris=${redirect_uris_json}" \
          -s "webOrigins=${web_origins_json}" >/dev/null
      fi

      if [[ -n "${KC_ROLE_NAMES_CSV}" ]]; then
        IFS="," read -r -a roles <<<"${KC_ROLE_NAMES_CSV}"
        for role_name in "${roles[@]}"; do
          role_name="${role_name#${role_name%%[![:space:]]*}}"
          role_name="${role_name%${role_name##*[![:space:]]}}"
          [[ -n "${role_name}" ]] || continue
          if ! "${KCADM}" get "roles/${role_name}" --config "${KCADM_CONFIG_FILE}" -r "${KC_REALM_NAME}" >/dev/null 2>&1; then
            "${KCADM}" create roles \
              --config "${KCADM_CONFIG_FILE}" \
              -r "${KC_REALM_NAME}" \
              -s "name=${role_name}" >/dev/null
          fi
        done
      fi

      if [[ -n "${KC_ADMIN_USERNAME}" ]]; then
        admin_user_internal_id="$(resolve_user_internal_id)"
        if [[ -z "${admin_user_internal_id}" ]]; then
          "${KCADM}" create users \
            --config "${KCADM_CONFIG_FILE}" \
            -r "${KC_REALM_NAME}" \
            -s "username=${KC_ADMIN_USERNAME}" \
            -s enabled=true >/dev/null
          admin_user_internal_id="$(resolve_user_internal_id)"
        fi
        if [[ -n "${KC_ADMIN_PASSWORD}" ]]; then
          "${KCADM}" set-password \
            --config "${KCADM_CONFIG_FILE}" \
            -r "${KC_REALM_NAME}" \
            --username "${KC_ADMIN_USERNAME}" \
            --new-password "${KC_ADMIN_PASSWORD}" \
            --temporary=false >/dev/null
        fi
        if [[ -n "${KC_ADMIN_ROLE}" ]]; then
          "${KCADM}" add-roles \
            --config "${KCADM_CONFIG_FILE}" \
            -r "${KC_REALM_NAME}" \
            --uusername "${KC_ADMIN_USERNAME}" \
            --rolename "${KC_ADMIN_ROLE}" >/dev/null || true
        fi
      fi
    '

  log_metric \
    "keycloak_identity_contract_reconcile_total" \
    "1" \
    "namespace=$namespace realm=$realm_name client_id=$client_id status=reconciled"
  log_info "Keycloak identity contract reconciled realm=$realm_name client_id=$client_id"
}
