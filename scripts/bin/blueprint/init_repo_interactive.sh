#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
export BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS="true"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
unset BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS

start_script_metric_trap "blueprint_init_repo_interactive"

usage() {
  cat <<EOF
Usage: init_repo_interactive.sh [--dry-run]

Interactive repository identity wizard for GitHub-template consumers.
Prompts for repository/docs identity values, validates them, shows a summary,
and then calls blueprint-init-repo with resolved values.

Environment variables:
  BLUEPRINT_INIT_DRY_RUN=true to preview file changes without writing them.
  $(blueprint_init_force_env_var)=true to re-apply init after first initialization.
  $(blueprint_defaults_env_file) and $(blueprint_secrets_env_file) are auto-loaded when present.

Options:
  --dry-run    Preview file changes without writing them.
EOF
}

infer_github_org_from_remote() {
  local remote_url
  remote_url="$(git -C "$ROOT_DIR" config --get remote.origin.url || true)"
  if [[ "$remote_url" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

infer_github_repo_from_remote() {
  local remote_url
  remote_url="$(git -C "$ROOT_DIR" config --get remote.origin.url || true)"
  if [[ "$remote_url" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    printf '%s\n' "${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

validate_repo_slug() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
}

validate_github_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
}

validate_branch_name() {
  local value="$1"
  [[ "$value" =~ ^[A-Za-z0-9._/-]+$ ]] || return 1
  [[ "$value" != */ ]] || return 1
  [[ "$value" != /* ]]
}

validate_non_empty() {
  local value="$1"
  [[ -n "$value" ]]
}

validate_stackit_region() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9-]+$ ]]
}

validate_stackit_slug() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9][a-z0-9-]*$ ]]
}

validate_stackit_key_prefix() {
  local value="$1"
  [[ "$value" =~ ^[a-zA-Z0-9._/-]+$ ]] || return 1
  [[ "$value" != /* ]] || return 1
  [[ "$value" != */ ]]
}

validate_stackit_bucket() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]]
}

normalize_slug_component() {
  local raw="$1"
  local normalized
  normalized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g')"
  if [[ -z "$normalized" ]]; then
    normalized="blueprint"
  fi
  printf '%s\n' "$normalized"
}

normalize_bucket_name() {
  local raw="$1"
  local normalized
  normalized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9.-]+/-/g; s/^-+//; s/-+$//; s/-+/-/g')"
  if [[ -z "$normalized" ]]; then
    normalized="stackit-tf-state"
  fi
  if [[ "${#normalized}" -gt 63 ]]; then
    normalized="${normalized:0:63}"
    normalized="${normalized%-}"
  fi
  printf '%s\n' "$normalized"
}

prompt_with_default() {
  local prompt="$1"
  local default_value="$2"
  local validator="$3"
  local entered value
  while true; do
    read -r -p "$prompt [$default_value]: " entered
    value="${entered:-$default_value}"
    if "$validator" "$value"; then
      printf '%s\n' "$value"
      return 0
    fi
    printf 'Invalid value. Please try again.\n'
  done
}

set_default_env BLUEPRINT_INIT_DRY_RUN "false"
dry_run="${BLUEPRINT_INIT_DRY_RUN}"
if [[ "$dry_run" != "true" && "$dry_run" != "false" ]]; then
  log_fatal "BLUEPRINT_INIT_DRY_RUN must be true or false (got: $dry_run)"
fi

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --help)
    usage
    exit 0
    ;;
  --dry-run)
    dry_run="true"
    shift
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
done

if [[ ! -t 0 ]]; then
  log_fatal "interactive init requires a TTY stdin"
fi

require_command bash
require_command git
require_command python3

blueprint_load_env_defaults_for_init
blueprint_init_force_var_name="$(blueprint_init_force_env_var)"

default_repo_name="${BLUEPRINT_REPO_NAME:-$(basename "$ROOT_DIR")}"
default_org="${BLUEPRINT_GITHUB_ORG:-example-org}"
default_repo="${BLUEPRINT_GITHUB_REPO:-$default_repo_name}"
default_default_branch="${BLUEPRINT_DEFAULT_BRANCH:-main}"
default_docs_title="${BLUEPRINT_DOCS_TITLE:-$default_repo_name}"
default_docs_tagline="${BLUEPRINT_DOCS_TAGLINE:-Reusable local+STACKIT platform blueprint}"
default_stackit_region="${BLUEPRINT_STACKIT_REGION:-eu01}"

if inferred_org="$(infer_github_org_from_remote)"; then
  if [[ -z "${BLUEPRINT_GITHUB_ORG:-}" ]]; then
    default_org="$inferred_org"
  fi
fi

if inferred_repo="$(infer_github_repo_from_remote)"; then
  if [[ -z "${BLUEPRINT_GITHUB_REPO:-}" ]]; then
    default_repo="$inferred_repo"
  fi
fi

printf '\nBlueprint Init Wizard\n'
printf 'Repository root: %s\n\n' "$ROOT_DIR"

blueprint_repo_name="$(prompt_with_default "Repository slug" "$default_repo_name" validate_repo_slug)"
blueprint_github_org="$(prompt_with_default "GitHub org/user" "$default_org" validate_github_name)"
blueprint_github_repo="$(prompt_with_default "GitHub repository" "$default_repo" validate_github_name)"
blueprint_default_branch="$(prompt_with_default "Default branch" "$default_default_branch" validate_branch_name)"
blueprint_docs_title="$(prompt_with_default "Docs title" "$default_docs_title" validate_non_empty)"
blueprint_docs_tagline="$(prompt_with_default "Docs tagline" "$default_docs_tagline" validate_non_empty)"

default_stackit_tenant="${BLUEPRINT_STACKIT_TENANT_SLUG:-$(normalize_slug_component "$blueprint_github_org")}"
default_stackit_platform="${BLUEPRINT_STACKIT_PLATFORM_SLUG:-$(normalize_slug_component "${blueprint_repo_name%-blueprint}")}"
if [[ "$default_stackit_platform" == "blueprint" ]]; then
  default_stackit_platform="$(normalize_slug_component "$blueprint_repo_name")"
fi
default_stackit_project_id="${BLUEPRINT_STACKIT_PROJECT_ID:-${default_stackit_tenant}-${default_stackit_platform}}"
default_stackit_bucket="${BLUEPRINT_STACKIT_TFSTATE_BUCKET:-$(normalize_bucket_name "${default_stackit_tenant}-${default_stackit_platform}-tf-state")}"
default_stackit_key_prefix="${BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX:-terraform/state}"

blueprint_stackit_region="$(prompt_with_default "STACKIT region" "$default_stackit_region" validate_stackit_region)"
blueprint_stackit_tenant_slug="$(prompt_with_default "STACKIT tenant slug" "$default_stackit_tenant" validate_stackit_slug)"
blueprint_stackit_platform_slug="$(prompt_with_default "STACKIT platform slug" "$default_stackit_platform" validate_stackit_slug)"
blueprint_stackit_project_id="$(prompt_with_default "STACKIT project id" "$default_stackit_project_id" validate_non_empty)"
blueprint_stackit_tfstate_bucket="$(prompt_with_default "STACKIT TF state bucket" "$default_stackit_bucket" validate_stackit_bucket)"
blueprint_stackit_tfstate_key_prefix="$(prompt_with_default "STACKIT TF state key prefix" "$default_stackit_key_prefix" validate_stackit_key_prefix)"

printf '\nResolved values\n'
printf '  BLUEPRINT_REPO_NAME=%s\n' "$blueprint_repo_name"
printf '  BLUEPRINT_GITHUB_ORG=%s\n' "$blueprint_github_org"
printf '  BLUEPRINT_GITHUB_REPO=%s\n' "$blueprint_github_repo"
printf '  BLUEPRINT_DEFAULT_BRANCH=%s\n' "$blueprint_default_branch"
printf '  BLUEPRINT_DOCS_TITLE=%s\n' "$blueprint_docs_title"
printf '  BLUEPRINT_DOCS_TAGLINE=%s\n' "$blueprint_docs_tagline"
printf '  BLUEPRINT_STACKIT_REGION=%s\n' "$blueprint_stackit_region"
printf '  BLUEPRINT_STACKIT_TENANT_SLUG=%s\n' "$blueprint_stackit_tenant_slug"
printf '  BLUEPRINT_STACKIT_PLATFORM_SLUG=%s\n' "$blueprint_stackit_platform_slug"
printf '  BLUEPRINT_STACKIT_PROJECT_ID=%s\n' "$blueprint_stackit_project_id"
printf '  BLUEPRINT_STACKIT_TFSTATE_BUCKET=%s\n' "$blueprint_stackit_tfstate_bucket"
printf '  BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX=%s\n' "$blueprint_stackit_tfstate_key_prefix"
if [[ "$dry_run" == "true" ]]; then
  printf '  BLUEPRINT_INIT_DRY_RUN=true\n'
fi
if [[ "${!blueprint_init_force_var_name:-false}" == "true" ]]; then
  printf '  %s=true\n' "$blueprint_init_force_var_name"
fi

confirm_default="Y"
read -r -p $'\nApply these values? [Y/n]: ' confirm_default
confirm="${confirm_default:-Y}"
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  log_info "interactive init aborted by user"
  exit 0
fi

run_cmd env \
  BLUEPRINT_REPO_NAME="$blueprint_repo_name" \
  BLUEPRINT_GITHUB_ORG="$blueprint_github_org" \
  BLUEPRINT_GITHUB_REPO="$blueprint_github_repo" \
  BLUEPRINT_DEFAULT_BRANCH="$blueprint_default_branch" \
  BLUEPRINT_DOCS_TITLE="$blueprint_docs_title" \
  BLUEPRINT_DOCS_TAGLINE="$blueprint_docs_tagline" \
  BLUEPRINT_STACKIT_REGION="$blueprint_stackit_region" \
  BLUEPRINT_STACKIT_TENANT_SLUG="$blueprint_stackit_tenant_slug" \
  BLUEPRINT_STACKIT_PLATFORM_SLUG="$blueprint_stackit_platform_slug" \
  BLUEPRINT_STACKIT_PROJECT_ID="$blueprint_stackit_project_id" \
  BLUEPRINT_STACKIT_TFSTATE_BUCKET="$blueprint_stackit_tfstate_bucket" \
  BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX="$blueprint_stackit_tfstate_key_prefix" \
  BLUEPRINT_INIT_DRY_RUN="$dry_run" \
  "$blueprint_init_force_var_name=${!blueprint_init_force_var_name:-false}" \
  "$ROOT_DIR/scripts/bin/blueprint/init_repo.sh"

if [[ "$dry_run" == "true" ]]; then
  log_info "dry-run complete; no files were modified"
else
  log_info "interactive init complete"
  log_info "next suggested commands: make blueprint-check-placeholders && make blueprint-bootstrap && make infra-bootstrap && make infra-validate"
fi
