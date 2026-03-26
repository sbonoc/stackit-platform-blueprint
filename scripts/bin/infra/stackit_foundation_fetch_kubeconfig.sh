#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_stackit_foundation_fetch_kubeconfig"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_fetch_kubeconfig.sh

Fetches STACKIT foundation kubeconfig into a local file path.

Optional environment variables:
  STACKIT_FOUNDATION_KUBECONFIG_OUTPUT  Output path (absolute or repository-relative)
  STACKIT_KUBECONFIG_CONTENT_BASE64     Base64 kubeconfig payload (optional)
  STACKIT_FOUNDATION_TERRAFORM_DIR      Terraform env dir (default: stackit profile env dir)
  STACKIT_PROJECT_ID                    Recorded in inventory/state metadata
  STACKIT_REGION                        Recorded in inventory/state metadata
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-foundation-fetch-kubeconfig requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

if tooling_is_execution_enabled; then
  require_env_vars STACKIT_PROJECT_ID STACKIT_REGION
else
  set_default_env STACKIT_PROJECT_ID "project-placeholder"
  set_default_env STACKIT_REGION "eu01"
fi
set_default_env STACKIT_FOUNDATION_KUBECONFIG_OUTPUT "${HOME}/.kube/stackit-${BLUEPRINT_PROFILE}.yaml"

kubeconfig_output="$STACKIT_FOUNDATION_KUBECONFIG_OUTPUT"
if [[ "$kubeconfig_output" != /* ]]; then
  kubeconfig_output="$ROOT_DIR/$kubeconfig_output"
fi

ensure_dir "$(dirname "$kubeconfig_output")"

content_source="generated_dry_run"
if [[ -n "${STACKIT_KUBECONFIG_CONTENT_BASE64:-}" ]]; then
  require_command base64
  if ! printf '%s' "$STACKIT_KUBECONFIG_CONTENT_BASE64" | base64 --decode >"$kubeconfig_output" 2>/dev/null; then
    log_fatal "invalid STACKIT_KUBECONFIG_CONTENT_BASE64 payload; cannot decode kubeconfig"
  fi
  content_source="provided_base64"
elif tooling_is_execution_enabled; then
  set_default_env STACKIT_FOUNDATION_TERRAFORM_DIR "$(stackit_terraform_env_dir)"
  terraform_dir="$STACKIT_FOUNDATION_TERRAFORM_DIR"
  if [[ "$terraform_dir" != /* ]]; then
    terraform_dir="$ROOT_DIR/$terraform_dir"
  fi

  if ! terraform_dir_has_config "$terraform_dir"; then
    log_fatal "missing terraform configuration in $terraform_dir; cannot fetch kubeconfig output"
  fi

  require_command terraform
  run_cmd terraform -chdir="$terraform_dir" init -input=false -no-color
  if ! run_cmd_capture terraform -chdir="$terraform_dir" output -raw ske_kubeconfig >"$kubeconfig_output"; then
    log_fatal "unable to fetch terraform output ske_kubeconfig from $terraform_dir"
  fi
  if [[ ! -s "$kubeconfig_output" ]]; then
    log_fatal "terraform output ske_kubeconfig is empty in $terraform_dir"
  fi
  content_source="terraform_output"
else
  cat >"$kubeconfig_output" <<KUBECONFIG
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://api.${STACKIT_REGION}.stackit.cloud
    insecure-skip-tls-verify: true
  name: stackit-${BLUEPRINT_PROFILE}
contexts:
- context:
    cluster: stackit-${BLUEPRINT_PROFILE}
    user: stackit-${BLUEPRINT_PROFILE}
  name: stackit-${BLUEPRINT_PROFILE}
current-context: stackit-${BLUEPRINT_PROFILE}
users:
- name: stackit-${BLUEPRINT_PROFILE}
  user:
    token: stackit-placeholder-token-dry-run
KUBECONFIG
fi

chmod 600 "$kubeconfig_output"

kubeconfig_bytes="$(wc -c <"$kubeconfig_output" | tr -d ' ')"
log_metric "stackit_kubeconfig_bytes" "$kubeconfig_bytes" "source=$content_source"

state_file="$(
  write_state_file "stackit_foundation_kubeconfig" \
    "profile=$BLUEPRINT_PROFILE" \
    "project_id=$STACKIT_PROJECT_ID" \
    "region=$STACKIT_REGION" \
    "kubeconfig_output=$kubeconfig_output" \
    "source=$content_source" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "STACKIT foundation kubeconfig written to $kubeconfig_output"
log_info "stackit foundation kubeconfig state written to $state_file"
