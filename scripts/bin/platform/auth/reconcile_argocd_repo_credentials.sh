#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "platform_auth_reconcile_argocd_repo_credentials"

usage() {
  cat <<'USAGE'
Usage: reconcile_argocd_repo_credentials.sh

Reconciles ArgoCD Git repository credentials through the runtime identity ESO contract:
- validates canonical HTTPS GitHub repo URL consistency in managed Argo manifests,
- validates PAT-only token policy for Argo repository access,
- updates source secret properties used by ESO (execute mode only),
- executes generic ESO runtime credentials reconciliation,
- validates live Argo repository secret contract in execute mode.

Contract knobs:
- ARGOCD_REPO_USERNAME (default: x-access-token)
- ARGOCD_REPO_TOKEN (default: empty; expected PAT prefix ghp_ or github_pat_)
- ARGOCD_REPO_CREDENTIALS_REQUIRED (default: false)
- RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE (default: false; set true when called by runtime identity orchestrator)
- RUNTIME_CREDENTIALS_SOURCE_NAMESPACE (default: security)
- RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME (default: runtime-credentials-source)
- RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT (default: 180)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
runtime_identity_contract_cli="$ROOT_DIR/scripts/lib/infra/runtime_identity_contract.py"
argocd_repo_contract_cli="$ROOT_DIR/scripts/lib/infra/argocd_repo_contract.py"
argocd_repo_json_helpers="$ROOT_DIR/scripts/lib/platform/auth/argocd_repo_credentials_json.py"
generic_reconcile_script="$ROOT_DIR/scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh"

while IFS=$'\t' read -r env_name env_default; do
  [[ -n "$env_name" ]] || continue
  set_default_env "$env_name" "$env_default"
done < <(python3 "$runtime_identity_contract_cli" runtime-env-defaults)

set_default_env RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME "runtime-credentials-source"
set_default_env ARGOCD_REPO_TYPE "git"
set_default_env ARGOCD_REPO_URL ""
set_default_env ARGOCD_REPO_USERNAME "x-access-token"
set_default_env ARGOCD_REPO_TOKEN ""
set_default_env ARGOCD_REPO_CREDENTIALS_REQUIRED "false"
set_default_env RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE "false"

ARGOCD_REPO_CREDENTIALS_REQUIRED_NORMALIZED="$(normalize_bool "$ARGOCD_REPO_CREDENTIALS_REQUIRED")"
RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE_NORMALIZED="$(normalize_bool "$RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE")"

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

declare -a ARGOCD_REPO_RECONCILE_ISSUES=()

record_reconcile_issue() {
  local message="$1"
  if [[ "$ARGOCD_REPO_CREDENTIALS_REQUIRED_NORMALIZED" == "true" ]]; then
    log_error "$message"
  else
    log_warn "$message"
  fi
  ARGOCD_REPO_RECONCILE_ISSUES+=("$message")
}

wait_for_secret_exists() {
  local namespace="$1"
  local name="$2"
  local timeout_seconds="$3"
  local started_at now elapsed

  started_at="$(date +%s)"
  while true; do
    if kubectl -n "$namespace" get secret "$name" >/dev/null 2>&1; then
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

seed_argocd_source_secret_properties() {
  local namespace="$1"
  local secret_name="$2"
  local source_env_file patch_file secret_manifest_file namespace_manifest_file
  SOURCE_SECRET_SYNC_MODE_RESULT=""
  source_env_file="$(mktemp)"
  patch_file="$(mktemp)"
  secret_manifest_file="$(mktemp)"
  namespace_manifest_file="$(mktemp)"
  trap 'rm -f "$source_env_file" "$patch_file" "$secret_manifest_file" "$namespace_manifest_file"' RETURN

  cat >"$source_env_file" <<EOF
ARGOCD_REPO_TYPE=$ARGOCD_REPO_TYPE
ARGOCD_REPO_URL=$ARGOCD_REPO_URL
ARGOCD_REPO_USERNAME=$ARGOCD_REPO_USERNAME
ARGOCD_REPO_TOKEN=$ARGOCD_REPO_TOKEN
EOF

  run_cmd_capture kubectl create namespace "$namespace" --dry-run=client -o yaml >"$namespace_manifest_file"
  run_cmd kubectl apply -f "$namespace_manifest_file"

  if kubectl -n "$namespace" get secret "$secret_name" >/dev/null 2>&1; then
    run_cmd python3 "$argocd_repo_json_helpers" render-source-patch \
      "$patch_file" \
      "$ARGOCD_REPO_TYPE" \
      "$ARGOCD_REPO_URL" \
      "$ARGOCD_REPO_USERNAME" \
      "$ARGOCD_REPO_TOKEN"
    run_cmd kubectl -n "$namespace" patch secret "$secret_name" --type merge --patch-file "$patch_file"
    SOURCE_SECRET_SYNC_MODE_RESULT="patched-existing-secret"
    return 0
  fi

  run_cmd_capture kubectl -n "$namespace" create secret generic "$secret_name" \
    --from-env-file="$source_env_file" \
    --dry-run=client -o yaml >"$secret_manifest_file"
  run_cmd kubectl apply -f "$secret_manifest_file"
  SOURCE_SECRET_SYNC_MODE_RESULT="created-source-secret"
}

validate_argocd_target_secret() {
  local namespace="$1"
  local secret_name="$2"
  local expected_url="$3"
  local validation_output
  if ! validation_output="$(
    kubectl -n "$namespace" get secret "$secret_name" -o json | \
      python3 "$argocd_repo_json_helpers" validate-target-secret "$expected_url" 2>&1
  )"; then
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      record_reconcile_issue "$line"
    done <<<"$validation_output"
    return 1
  fi
  return 0
}

canonical_repo_url=""
resolved_repo_url=""
runtime_reconcile_status="skipped"
source_secret_sync_mode="skipped"
target_secret_live_check_status="skipped"
SOURCE_SECRET_SYNC_MODE_RESULT=""

canonical_repo_output=""
# argparse global options must be placed before the subcommand; keep this order
# stable so contract resolution works in both local and CI execution.
if ! canonical_repo_output="$(python3 "$argocd_repo_contract_cli" --repo-root "$ROOT_DIR" canonical-url 2>&1)"; then
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    record_reconcile_issue "$line"
  done <<<"$canonical_repo_output"
else
  canonical_repo_url="$(trim_whitespace "$canonical_repo_output")"
fi

if [[ -n "$canonical_repo_url" && -z "$ARGOCD_REPO_URL" ]]; then
  ARGOCD_REPO_URL="$canonical_repo_url"
fi
resolved_repo_url="$ARGOCD_REPO_URL"

if [[ -z "$resolved_repo_url" ]]; then
  record_reconcile_issue "ARGOCD_REPO_URL unresolved; set ARGOCD_REPO_URL or fix Argo repoURL manifests"
elif ! [[ "$resolved_repo_url" =~ ^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$ ]]; then
  record_reconcile_issue "ARGOCD_REPO_URL must use HTTPS GitHub URL format (https://github.com/<org>/<repo>.git); found $resolved_repo_url"
fi

if [[ -n "$canonical_repo_url" && -n "$resolved_repo_url" && "$resolved_repo_url" != "$canonical_repo_url" ]]; then
  record_reconcile_issue \
    "ARGOCD_REPO_URL=$resolved_repo_url does not match canonical ArgoCD repo URL from managed manifests: $canonical_repo_url"
fi

if [[ -z "$ARGOCD_REPO_USERNAME" ]]; then
  record_reconcile_issue "ARGOCD_REPO_USERNAME must not be empty"
fi

if [[ -z "$ARGOCD_REPO_TOKEN" ]]; then
  record_reconcile_issue \
    "ARGOCD_REPO_TOKEN is empty; set a GitHub PAT (ghp_ or github_pat_) in blueprint/repo.init.secrets.env for private repositories"
elif [[ "$ARGOCD_REPO_TOKEN" == gho_* ]]; then
  record_reconcile_issue \
    "unsupported GitHub OAuth token prefix gho_ for Argo repository credentials; use a PAT (ghp_ or github_pat_)"
elif [[ "$ARGOCD_REPO_TOKEN" != ghp_* && "$ARGOCD_REPO_TOKEN" != github_pat_* ]]; then
  record_reconcile_issue \
    "ARGOCD_REPO_TOKEN must be a GitHub PAT (ghp_ or github_pat_); unsupported token format"
fi

if tooling_is_execution_enabled; then
  prepare_cluster_access
  require_command kubectl
  if [[ -n "$resolved_repo_url" && -n "$ARGOCD_REPO_USERNAME" && -n "$ARGOCD_REPO_TOKEN" ]]; then
    if seed_argocd_source_secret_properties \
      "$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE" \
      "$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME"; then
      source_secret_sync_mode="${SOURCE_SECRET_SYNC_MODE_RESULT:-unknown}"
      log_info \
        "argocd source secret properties synced namespace=$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE name=$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME mode=$source_secret_sync_mode"
    else
      source_secret_sync_mode="failed"
      record_reconcile_issue \
        "failed to sync source secret properties for ${RUNTIME_CREDENTIALS_SOURCE_NAMESPACE}/${RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME}"
    fi
  else
    source_secret_sync_mode="skipped-incomplete-env"
  fi
else
  source_secret_sync_mode="dry-run-no-cluster"
fi

if [[ "$RUNTIME_IDENTITY_SKIP_GENERIC_RECONCILE_NORMALIZED" == "true" ]]; then
  runtime_reconcile_status="skipped-by-runtime-identity-orchestrator"
else
  if run_cmd "$generic_reconcile_script"; then
    runtime_reconcile_status="success"
  else
    runtime_reconcile_status="failure"
    record_reconcile_issue \
      "generic runtime credentials reconciliation failed; check artifacts/infra/runtime_credentials_eso_reconcile.env"
  fi
fi

if tooling_is_execution_enabled && [[ "$runtime_reconcile_status" != "failure" ]]; then
  if wait_for_secret_exists "argocd" "argocd-gitops-repo" "$runtime_wait_timeout"; then
    if validate_argocd_target_secret "argocd" "argocd-gitops-repo" "$resolved_repo_url"; then
      target_secret_live_check_status="ready"
    else
      target_secret_live_check_status="invalid"
    fi
  else
    target_secret_live_check_status="timeout"
    record_reconcile_issue "target secret argocd/argocd-gitops-repo not found within ${runtime_wait_timeout}s"
  fi
fi

issue_count="${#ARGOCD_REPO_RECONCILE_ISSUES[@]}"
status="success"
if [[ "$runtime_reconcile_status" == "failure" ]]; then
  status="failed-runtime-reconcile"
elif (( issue_count > 0 )); then
  if [[ "$ARGOCD_REPO_CREDENTIALS_REQUIRED_NORMALIZED" == "true" ]]; then
    status="failed-required"
  else
    status="success-with-warnings"
  fi
fi

log_metric \
  "argocd_repo_credentials_reconcile_total" \
  "1" \
  "profile=$BLUEPRINT_PROFILE mode=$(tooling_execution_mode) status=$status required=$ARGOCD_REPO_CREDENTIALS_REQUIRED_NORMALIZED issue_count=$issue_count runtime_reconcile=$runtime_reconcile_status"

state_file="$(
  write_state_file "argocd_repo_credentials_reconcile" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "status=$status" \
    "required=$ARGOCD_REPO_CREDENTIALS_REQUIRED_NORMALIZED" \
    "canonical_repo_url=$canonical_repo_url" \
    "resolved_repo_url=$resolved_repo_url" \
    "source_namespace=$RUNTIME_CREDENTIALS_SOURCE_NAMESPACE" \
    "source_secret_name=$RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME" \
    "source_secret_sync_mode=$source_secret_sync_mode" \
    "runtime_reconcile_status=$runtime_reconcile_status" \
    "target_secret_live_check_status=$target_secret_live_check_status" \
    "issue_count=$issue_count" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "argocd repo credentials reconcile state written to $state_file"

if (( issue_count > 0 )); then
  for issue in "${ARGOCD_REPO_RECONCILE_ISSUES[@]}"; do
    log_warn "argocd repo reconcile issue: $issue"
  done
fi

if [[ "$status" == failed-* ]]; then
  exit 1
fi

exit 0
