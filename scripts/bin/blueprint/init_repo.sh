#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_init_repo"

usage() {
  cat <<'EOF'
Usage: init_repo.sh [--dry-run]

Initializes repository identity after creating a new repository from the GitHub template.

Environment variables:
  BLUEPRINT_REPO_NAME        Repository slug used for blueprint contract metadata.
  BLUEPRINT_GITHUB_ORG       GitHub organization/user name used for docs edit links.
  BLUEPRINT_GITHUB_REPO      GitHub repository name used for docs edit links.
  BLUEPRINT_DEFAULT_BRANCH   Default branch name (default: main).
  BLUEPRINT_DOCS_TITLE       Docusaurus docs title (default: BLUEPRINT_REPO_NAME).
  BLUEPRINT_DOCS_TAGLINE     Docusaurus docs tagline.

Optional:
  BLUEPRINT_INIT_SKIP_VALIDATE=true to skip contract validation after initialization.
  BLUEPRINT_INIT_DRY_RUN=true       to preview identity changes without writing files.

Options:
  --dry-run                         same as BLUEPRINT_INIT_DRY_RUN=true.
EOF
}

cli_dry_run="false"
while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --help)
    usage
    exit 0
    ;;
  --dry-run)
    cli_dry_run="true"
    shift
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
done

require_command python3
require_command git

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

set_default_env BLUEPRINT_REPO_NAME "$(basename "$ROOT_DIR")"

if [[ -z "${BLUEPRINT_GITHUB_ORG:-}" ]]; then
  if inferred_org="$(infer_github_org_from_remote)"; then
    export BLUEPRINT_GITHUB_ORG="$inferred_org"
  else
    export BLUEPRINT_GITHUB_ORG="example-org"
  fi
fi

if [[ -z "${BLUEPRINT_GITHUB_REPO:-}" ]]; then
  if inferred_repo="$(infer_github_repo_from_remote)"; then
    export BLUEPRINT_GITHUB_REPO="$inferred_repo"
  else
    export BLUEPRINT_GITHUB_REPO="$BLUEPRINT_REPO_NAME"
  fi
fi

set_default_env BLUEPRINT_DEFAULT_BRANCH "main"
set_default_env BLUEPRINT_DOCS_TITLE "$BLUEPRINT_REPO_NAME"
set_default_env BLUEPRINT_DOCS_TAGLINE "Reusable local+STACKIT platform blueprint"
set_default_env BLUEPRINT_INIT_SKIP_VALIDATE "false"
set_default_env BLUEPRINT_INIT_DRY_RUN "false"

if [[ "$cli_dry_run" == "true" ]]; then
  export BLUEPRINT_INIT_DRY_RUN="true"
fi

init_repo_args=(
  --repo-root "$ROOT_DIR"
  --repo-name "$BLUEPRINT_REPO_NAME"
  --github-org "$BLUEPRINT_GITHUB_ORG"
  --github-repo "$BLUEPRINT_GITHUB_REPO"
  --default-branch "$BLUEPRINT_DEFAULT_BRANCH"
  --docs-title "$BLUEPRINT_DOCS_TITLE"
  --docs-tagline "$BLUEPRINT_DOCS_TAGLINE"
)

if [[ "${BLUEPRINT_INIT_DRY_RUN}" == "true" ]]; then
  init_repo_args+=(--dry-run)
fi

run_cmd "$ROOT_DIR/scripts/lib/blueprint/init_repo.py" "${init_repo_args[@]}"

if [[ "${BLUEPRINT_INIT_DRY_RUN}" == "true" ]]; then
  log_info "init dry-run mode enabled; skipping contract validation because files were not written"
elif [[ "${BLUEPRINT_INIT_SKIP_VALIDATE}" != "true" ]]; then
  run_cmd "$ROOT_DIR/scripts/bin/blueprint/validate_contract.py" \
    --contract-path "$ROOT_DIR/blueprint/contract.yaml"
fi

if [[ "${BLUEPRINT_INIT_DRY_RUN}" == "true" ]]; then
  log_info "blueprint repository initialization dry-run complete"
else
  log_info "blueprint repository initialization complete"
fi
