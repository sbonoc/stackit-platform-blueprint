#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "blueprint_check_placeholders"

usage() {
  cat <<'EOF'
Usage: check_placeholders.sh

Validates that generated-repository identity placeholders are resolved.

Required environment variables:
  BLUEPRINT_REPO_NAME
  BLUEPRINT_GITHUB_ORG
  BLUEPRINT_GITHUB_REPO
  BLUEPRINT_DEFAULT_BRANCH
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_env_vars \
  BLUEPRINT_REPO_NAME \
  BLUEPRINT_GITHUB_ORG \
  BLUEPRINT_GITHUB_REPO \
  BLUEPRINT_DEFAULT_BRANCH

contract_file="$ROOT_DIR/blueprint/contract.yaml"
docs_config="$ROOT_DIR/docs/docusaurus.config.js"

if [[ ! -f "$contract_file" ]]; then
  log_fatal "missing contract file: $contract_file"
fi
if [[ ! -f "$docs_config" ]]; then
  log_fatal "missing docs config file: $docs_config"
fi

expected_edit_url="https://github.com/${BLUEPRINT_GITHUB_ORG}/${BLUEPRINT_GITHUB_REPO}/edit/${BLUEPRINT_DEFAULT_BRANCH}/docs/"

grep -qE "^  name: ${BLUEPRINT_REPO_NAME}$" "$contract_file" || \
  log_fatal "contract metadata.name does not match BLUEPRINT_REPO_NAME"
grep -qE "^    default_branch: ${BLUEPRINT_DEFAULT_BRANCH}$" "$contract_file" || \
  log_fatal "contract repository.default_branch does not match BLUEPRINT_DEFAULT_BRANCH"
grep -qF "organizationName: \"${BLUEPRINT_GITHUB_ORG}\"" "$docs_config" || \
  log_fatal "docs organizationName does not match BLUEPRINT_GITHUB_ORG"
grep -qF "projectName: \"${BLUEPRINT_GITHUB_REPO}\"" "$docs_config" || \
  log_fatal "docs projectName does not match BLUEPRINT_GITHUB_REPO"
grep -qF "editUrl: \"${expected_edit_url}\"" "$docs_config" || \
  log_fatal "docs editUrl does not match expected GitHub location"

placeholder_tokens=(
  "your-platform-blueprint"
  "your-github-org"
  "__REPLACE_ME__"
)
scan_files=(
  "$contract_file"
  "$docs_config"
)

for token in "${placeholder_tokens[@]}"; do
  for file in "${scan_files[@]}"; do
    if grep -qF "$token" "$file"; then
      log_fatal "unresolved placeholder token '$token' found in $file"
    fi
  done
done

log_info "generated repository placeholder checks passed"
