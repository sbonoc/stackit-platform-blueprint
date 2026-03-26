#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_template_smoke"

usage() {
  cat <<'EOF'
Usage: template_smoke.sh

Runs an end-to-end smoke simulation of GitHub template consumption in a temporary copy.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command tar
require_command make
require_command python3
require_command git

set_default_env BLUEPRINT_REPO_NAME "acme-platform-blueprint"
set_default_env BLUEPRINT_GITHUB_ORG "acme-platform"
set_default_env BLUEPRINT_GITHUB_REPO "acme-platform-blueprint"
set_default_env BLUEPRINT_DEFAULT_BRANCH "main"
set_default_env BLUEPRINT_DOCS_TITLE "Acme Platform Blueprint"
set_default_env BLUEPRINT_DOCS_TAGLINE "Reusable local+STACKIT platform blueprint"

tmp_root="$(mktemp -d)"
tmp_repo="$tmp_root/repo"
cleanup() {
  rm -rf "$tmp_root"
}
trap cleanup EXIT

mkdir -p "$tmp_repo"
(
  cd "$ROOT_DIR"
  tar \
    --exclude=".git" \
    --exclude=".pytest_cache" \
    --exclude="artifacts" \
    --exclude="docs/build" \
    --exclude="docs/.docusaurus" \
    --exclude="docs/node_modules" \
    --exclude="__pycache__" \
    -cf - .
) | (cd "$tmp_repo" && tar -xf -)

log_info "template smoke workspace: $tmp_repo"

(
  cd "$tmp_repo"
  git init -q
  BLUEPRINT_REPO_NAME="$BLUEPRINT_REPO_NAME" \
    BLUEPRINT_GITHUB_ORG="$BLUEPRINT_GITHUB_ORG" \
    BLUEPRINT_GITHUB_REPO="$BLUEPRINT_GITHUB_REPO" \
    BLUEPRINT_DEFAULT_BRANCH="$BLUEPRINT_DEFAULT_BRANCH" \
    BLUEPRINT_DOCS_TITLE="$BLUEPRINT_DOCS_TITLE" \
    BLUEPRINT_DOCS_TAGLINE="$BLUEPRINT_DOCS_TAGLINE" \
    make blueprint-init-repo

  WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBSERVABILITY_ENABLED=false \
    make blueprint-bootstrap

  WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBSERVABILITY_ENABLED=false \
    make infra-bootstrap

  WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBSERVABILITY_ENABLED=false \
    make infra-validate

  BLUEPRINT_REPO_NAME="$BLUEPRINT_REPO_NAME" \
    BLUEPRINT_GITHUB_ORG="$BLUEPRINT_GITHUB_ORG" \
    BLUEPRINT_GITHUB_REPO="$BLUEPRINT_GITHUB_REPO" \
    BLUEPRINT_DEFAULT_BRANCH="$BLUEPRINT_DEFAULT_BRANCH" \
    make blueprint-check-placeholders

  WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBSERVABILITY_ENABLED=false \
    make apps-bootstrap

  WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBSERVABILITY_ENABLED=false \
    make infra-smoke

  if [[ -d dags ]]; then
    log_fatal "template smoke failed: dags/ exists with workflows disabled"
  fi
)

log_info "template smoke completed successfully"
