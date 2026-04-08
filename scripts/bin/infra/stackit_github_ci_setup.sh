#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_stackit_ci_github_setup"

usage() {
  cat <<'USAGE'
Usage: stackit_github_ci_setup.sh

Creates GitHub deployment environments and repository secrets required for STACKIT CI delivery.

Environment variables:
  STACKIT_GITHUB_CI_REPO            GitHub repo slug owner/name (auto-derived from remote if unset)
  STACKIT_GITHUB_CI_ENVIRONMENTS    Comma-separated environments (default from contract: dev,stage,prod)
  STACKIT_GITHUB_CI_DRY_RUN         true|false (default: true)
  STACKIT_GITHUB_CI_CONTRACT_PATH   Path to contract JSON with defaults

In dry-run mode, missing secret values are reported but do not fail execution.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

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

derive_repo_slug_from_origin() {
  local remote_url
  remote_url="$(git -C "$ROOT_DIR" config --get remote.origin.url 2>/dev/null || true)"
  if [[ -z "$remote_url" ]]; then
    return 0
  fi

  case "$remote_url" in
  git@github.com:*)
    remote_url="${remote_url#git@github.com:}"
    ;;
  https://github.com/*)
    remote_url="${remote_url#https://github.com/}"
    ;;
  http://github.com/*)
    remote_url="${remote_url#http://github.com/}"
    ;;
  *)
    return 0
    ;;
  esac

  remote_url="${remote_url%.git}"
  remote_url="${remote_url%/}"
  printf '%s' "${remote_url%%/*}/${remote_url#*/}"
}

join_csv_from_lines() {
  awk 'NF {printf "%s%s", (count++ ? "," : ""), $0}'
}

set_default_env STACKIT_GITHUB_CI_CONTRACT_PATH "$ROOT_DIR/scripts/lib/infra/stackit_github_ci_contract.json"
set_default_env STACKIT_GITHUB_CI_DRY_RUN "true"
STACKIT_GITHUB_CI_DRY_RUN="$(normalize_bool "$STACKIT_GITHUB_CI_DRY_RUN")"

require_command gh
require_command python3

if [[ ! -f "$STACKIT_GITHUB_CI_CONTRACT_PATH" ]]; then
  log_fatal "STACKIT GitHub CI contract not found: $STACKIT_GITHUB_CI_CONTRACT_PATH"
fi

if [[ -z "${STACKIT_GITHUB_CI_REPO:-}" ]]; then
  # Prefer template-init variables when available; fall back to remote origin autodetection.
  if [[ -n "${BLUEPRINT_GITHUB_ORG:-}" && -n "${BLUEPRINT_GITHUB_REPO:-}" ]]; then
    STACKIT_GITHUB_CI_REPO="${BLUEPRINT_GITHUB_ORG}/${BLUEPRINT_GITHUB_REPO}"
  else
    STACKIT_GITHUB_CI_REPO="$(derive_repo_slug_from_origin)"
  fi
fi

if [[ -z "${STACKIT_GITHUB_CI_REPO:-}" ]]; then
  log_fatal "unable to resolve repository slug; set STACKIT_GITHUB_CI_REPO=owner/name"
fi

default_envs="$(
  python3 "$ROOT_DIR/scripts/lib/infra/stackit_github_ci_contract.py" \
    "$STACKIT_GITHUB_CI_CONTRACT_PATH" \
    default_environments
)"

required_secrets="$(
  python3 "$ROOT_DIR/scripts/lib/infra/stackit_github_ci_contract.py" \
    "$STACKIT_GITHUB_CI_CONTRACT_PATH" \
    required_repository_secrets
)"

if [[ -z "${STACKIT_GITHUB_CI_ENVIRONMENTS:-}" ]]; then
  STACKIT_GITHUB_CI_ENVIRONMENTS="$(printf '%s\n' "$default_envs" | join_csv_from_lines)"
fi

if [[ -z "$STACKIT_GITHUB_CI_ENVIRONMENTS" ]]; then
  log_fatal "no environments configured for STACKIT GitHub CI setup"
fi

run_cmd gh auth status >/dev/null

IFS=',' read -r -a environments <<<"$STACKIT_GITHUB_CI_ENVIRONMENTS"
secret_lines=()
while IFS= read -r secret_name; do
  [[ -n "$secret_name" ]] || continue
  secret_lines+=("$secret_name")
done <<<"$required_secrets"

if [[ "${#secret_lines[@]}" -eq 0 ]]; then
  log_fatal "no required repository secrets defined in $STACKIT_GITHUB_CI_CONTRACT_PATH"
fi

configured_envs=0
for raw_env in "${environments[@]}"; do
  env_name="$(echo "$raw_env" | xargs)"
  [[ -n "$env_name" ]] || continue

  if [[ "$STACKIT_GITHUB_CI_DRY_RUN" == "true" ]]; then
    log_info "[dry-run] would ensure GitHub environment: $STACKIT_GITHUB_CI_REPO:$env_name"
  else
    run_cmd gh api --method PUT "repos/$STACKIT_GITHUB_CI_REPO/environments/$env_name" >/dev/null
    log_info "ensured GitHub environment: $STACKIT_GITHUB_CI_REPO:$env_name"
  fi
  configured_envs=$((configured_envs + 1))
done

configured_secrets=0
missing_secret_values=()
for secret_name in "${secret_lines[@]}"; do
  secret_value="${!secret_name:-}"
  if [[ -z "$secret_value" ]]; then
    if [[ "$STACKIT_GITHUB_CI_DRY_RUN" == "true" ]]; then
      log_warn "[dry-run] required secret value missing from environment: $secret_name"
      missing_secret_values+=("$secret_name")
      continue
    fi
    log_fatal "required secret value missing from environment: $secret_name"
  fi

  if [[ "$STACKIT_GITHUB_CI_DRY_RUN" == "true" ]]; then
    log_info "[dry-run] would set repository secret: $STACKIT_GITHUB_CI_REPO:$secret_name"
  else
    printf '%s' "$secret_value" | run_cmd gh secret set "$secret_name" --repo "$STACKIT_GITHUB_CI_REPO" --body -
    log_info "set repository secret: $STACKIT_GITHUB_CI_REPO:$secret_name"
  fi
  configured_secrets=$((configured_secrets + 1))
done

log_metric "stackit_ci_github_setup_environment_count" "$configured_envs"
log_metric "stackit_ci_github_setup_secret_count" "$configured_secrets"
log_metric "stackit_ci_github_setup_missing_secret_count" "${#missing_secret_values[@]}"

state_file="$(
  write_state_file "stackit_ci_github_setup" \
    "repository=$STACKIT_GITHUB_CI_REPO" \
    "dry_run=$STACKIT_GITHUB_CI_DRY_RUN" \
    "environments=$STACKIT_GITHUB_CI_ENVIRONMENTS" \
    "configured_environment_count=$configured_envs" \
    "required_secret_count=${#secret_lines[@]}" \
    "configured_secret_count=$configured_secrets" \
    "missing_secret_count=${#missing_secret_values[@]}" \
    "missing_secrets=$(IFS=,; echo "${missing_secret_values[*]-}")" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

if [[ "${#missing_secret_values[@]}" -gt 0 ]]; then
  log_warn "missing secret values skipped in dry-run: $(IFS=,; echo "${missing_secret_values[*]-}")"
fi
log_info "stackit ci github setup state written to $state_file"
log_info "STACKIT GitHub CI setup completed repo=$STACKIT_GITHUB_CI_REPO dry_run=$STACKIT_GITHUB_CI_DRY_RUN"
