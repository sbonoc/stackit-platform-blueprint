#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_init_repo_interactive"

usage() {
  cat <<'EOF'
Usage: init_repo_interactive.sh [--dry-run]

Interactive repository identity wizard for GitHub-template consumers.
Prompts for repository/docs identity values, validates them, shows a summary,
and then calls blueprint-init-repo with resolved values.

Environment variables:
  BLUEPRINT_INIT_DRY_RUN=true to preview file changes without writing them.

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

default_repo_name="$(basename "$ROOT_DIR")"
default_org="example-org"
default_repo="$default_repo_name"

if inferred_org="$(infer_github_org_from_remote)"; then
  default_org="$inferred_org"
fi

if inferred_repo="$(infer_github_repo_from_remote)"; then
  default_repo="$inferred_repo"
fi

printf '\nBlueprint Init Wizard\n'
printf 'Repository root: %s\n\n' "$ROOT_DIR"

blueprint_repo_name="$(prompt_with_default "Repository slug" "$default_repo_name" validate_repo_slug)"
blueprint_github_org="$(prompt_with_default "GitHub org/user" "$default_org" validate_github_name)"
blueprint_github_repo="$(prompt_with_default "GitHub repository" "$default_repo" validate_github_name)"
blueprint_default_branch="$(prompt_with_default "Default branch" "main" validate_branch_name)"
blueprint_docs_title="$(prompt_with_default "Docs title" "$blueprint_repo_name" validate_non_empty)"
blueprint_docs_tagline="$(prompt_with_default "Docs tagline" "Reusable local+STACKIT platform blueprint" validate_non_empty)"

printf '\nResolved values\n'
printf '  BLUEPRINT_REPO_NAME=%s\n' "$blueprint_repo_name"
printf '  BLUEPRINT_GITHUB_ORG=%s\n' "$blueprint_github_org"
printf '  BLUEPRINT_GITHUB_REPO=%s\n' "$blueprint_github_repo"
printf '  BLUEPRINT_DEFAULT_BRANCH=%s\n' "$blueprint_default_branch"
printf '  BLUEPRINT_DOCS_TITLE=%s\n' "$blueprint_docs_title"
printf '  BLUEPRINT_DOCS_TAGLINE=%s\n' "$blueprint_docs_tagline"
if [[ "$dry_run" == "true" ]]; then
  printf '  BLUEPRINT_INIT_DRY_RUN=true\n'
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
  BLUEPRINT_INIT_DRY_RUN="$dry_run" \
  "$ROOT_DIR/scripts/bin/blueprint/init_repo.sh"

if [[ "$dry_run" == "true" ]]; then
  log_info "dry-run complete; no files were modified"
else
  log_info "interactive init complete"
  log_info "next suggested commands: make blueprint-check-placeholders && make blueprint-bootstrap && make infra-bootstrap && make infra-validate"
fi
