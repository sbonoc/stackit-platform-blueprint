#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

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
  BLUEPRINT_STACKIT_REGION
  BLUEPRINT_STACKIT_TENANT_SLUG
  BLUEPRINT_STACKIT_PLATFORM_SLUG
  BLUEPRINT_STACKIT_PROJECT_ID
  BLUEPRINT_STACKIT_TFSTATE_BUCKET
  BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX
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
  BLUEPRINT_DEFAULT_BRANCH \
  BLUEPRINT_STACKIT_REGION \
  BLUEPRINT_STACKIT_TENANT_SLUG \
  BLUEPRINT_STACKIT_PLATFORM_SLUG \
  BLUEPRINT_STACKIT_PROJECT_ID \
  BLUEPRINT_STACKIT_TFSTATE_BUCKET \
  BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX

contract_file="$ROOT_DIR/blueprint/contract.yaml"
docs_config="$ROOT_DIR/docs/docusaurus.config.js"
consumer_root_files=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/AGENTS.md"
  "$ROOT_DIR/AGENTS.backlog.md"
  "$ROOT_DIR/AGENTS.decisions.md"
  "$ROOT_DIR/docs/README.md"
  "$ROOT_DIR/.github/CODEOWNERS"
  "$ROOT_DIR/.github/ISSUE_TEMPLATE/bug_report.yml"
  "$ROOT_DIR/.github/ISSUE_TEMPLATE/feature_request.yml"
  "$ROOT_DIR/.github/ISSUE_TEMPLATE/config.yml"
  "$ROOT_DIR/.github/pull_request_template.md"
  "$ROOT_DIR/.github/workflows/ci.yml"
)
argocd_files=(
  "$ROOT_DIR/infra/gitops/argocd/root/applicationset-platform-environments.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/dev/applicationset-platform-environments.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/stage/applicationset-platform-environments.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/prod/applicationset-platform-environments.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/dev/appproject.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/stage/appproject.yaml"
  "$ROOT_DIR/infra/gitops/argocd/overlays/prod/appproject.yaml"
)
stackit_bootstrap_tfvars_files=(
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars"
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env/stage.tfvars"
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env/prod.tfvars"
)
stackit_foundation_tfvars_files=(
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env/dev.tfvars"
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env/stage.tfvars"
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env/prod.tfvars"
)
stackit_bootstrap_backend_files=(
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl"
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend/stage.hcl"
  "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend/prod.hcl"
)
stackit_foundation_backend_files=(
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl"
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend/stage.hcl"
  "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend/prod.hcl"
)

extract_quoted_assignment() {
  local file="$1"
  local key="$2"
  sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]*)\".*/\\1/p" "$file" | head -n 1
}

assert_quoted_assignment_equals() {
  local file="$1"
  local key="$2"
  local expected="$3"
  local label="$4"
  local actual
  actual="$(extract_quoted_assignment "$file" "$key")"
  if [[ -z "$actual" ]]; then
    log_fatal "missing quoted assignment '$key' in $file ($label)"
  fi
  if [[ "$actual" != "$expected" ]]; then
    log_fatal "$label mismatch in $file (expected '$expected', got '$actual')"
  fi
}

if [[ ! -f "$contract_file" ]]; then
  log_fatal "missing contract file: $contract_file"
fi
if [[ ! -f "$docs_config" ]]; then
  log_fatal "missing docs config file: $docs_config"
fi

expected_edit_url="https://github.com/${BLUEPRINT_GITHUB_ORG}/${BLUEPRINT_GITHUB_REPO}/edit/${BLUEPRINT_DEFAULT_BRANCH}/docs/"
expected_repo_url="https://github.com/${BLUEPRINT_GITHUB_ORG}/${BLUEPRINT_GITHUB_REPO}.git"

grep -qE "^  name: ${BLUEPRINT_REPO_NAME}$" "$contract_file" || \
  log_fatal "contract metadata.name does not match BLUEPRINT_REPO_NAME"
grep -qE "^    repo_mode: generated-consumer$" "$contract_file" || \
  log_fatal "contract repository.repo_mode must be generated-consumer after initialization"
grep -qE "^    default_branch: ${BLUEPRINT_DEFAULT_BRANCH}$" "$contract_file" || \
  log_fatal "contract repository.default_branch does not match BLUEPRINT_DEFAULT_BRANCH"
grep -qF "organizationName: \"${BLUEPRINT_GITHUB_ORG}\"" "$docs_config" || \
  log_fatal "docs organizationName does not match BLUEPRINT_GITHUB_ORG"
grep -qF "projectName: \"${BLUEPRINT_GITHUB_REPO}\"" "$docs_config" || \
  log_fatal "docs projectName does not match BLUEPRINT_GITHUB_REPO"
grep -qF "editUrl: \"${expected_edit_url}\"" "$docs_config" || \
  log_fatal "docs editUrl does not match expected GitHub location"
for argocd_file in "${argocd_files[@]}"; do
  [[ -f "$argocd_file" ]] || log_fatal "missing ArgoCD file: $argocd_file"
  grep -qF "${expected_repo_url}" "$argocd_file" || \
    log_fatal "ArgoCD repository URL does not match expected GitHub location in $argocd_file"
done

for tfvars_file in "${stackit_bootstrap_tfvars_files[@]}"; do
  [[ -f "$tfvars_file" ]] || log_fatal "missing STACKIT bootstrap tfvars file: $tfvars_file"
  assert_quoted_assignment_equals "$tfvars_file" "stackit_region" "$BLUEPRINT_STACKIT_REGION" "stackit_region"
  assert_quoted_assignment_equals "$tfvars_file" "tenant_slug" "$BLUEPRINT_STACKIT_TENANT_SLUG" "tenant_slug"
  assert_quoted_assignment_equals "$tfvars_file" "platform_slug" "$BLUEPRINT_STACKIT_PLATFORM_SLUG" "platform_slug"
  assert_quoted_assignment_equals "$tfvars_file" "state_key_prefix" "$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX" "state_key_prefix"
done

for tfvars_file in "${stackit_foundation_tfvars_files[@]}"; do
  [[ -f "$tfvars_file" ]] || log_fatal "missing STACKIT foundation tfvars file: $tfvars_file"
  assert_quoted_assignment_equals "$tfvars_file" "stackit_region" "$BLUEPRINT_STACKIT_REGION" "stackit_region"
  assert_quoted_assignment_equals "$tfvars_file" "tenant_slug" "$BLUEPRINT_STACKIT_TENANT_SLUG" "tenant_slug"
  assert_quoted_assignment_equals "$tfvars_file" "platform_slug" "$BLUEPRINT_STACKIT_PLATFORM_SLUG" "platform_slug"
  assert_quoted_assignment_equals "$tfvars_file" "stackit_project_id" "$BLUEPRINT_STACKIT_PROJECT_ID" "stackit_project_id"
done

for env in dev stage prod; do
  bootstrap_backend="$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend/$env.hcl"
  foundation_backend="$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend/$env.hcl"
  [[ -f "$bootstrap_backend" ]] || log_fatal "missing STACKIT bootstrap backend file: $bootstrap_backend"
  [[ -f "$foundation_backend" ]] || log_fatal "missing STACKIT foundation backend file: $foundation_backend"

  assert_quoted_assignment_equals "$bootstrap_backend" "bucket" "$BLUEPRINT_STACKIT_TFSTATE_BUCKET" "tfstate bucket"
  assert_quoted_assignment_equals "$bootstrap_backend" "region" "$BLUEPRINT_STACKIT_REGION" "backend region"
  assert_quoted_assignment_equals \
    "$bootstrap_backend" \
    "key" \
    "$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX/$env/bootstrap.tfstate" \
    "bootstrap backend key"
  assert_quoted_assignment_equals \
    "$bootstrap_backend" \
    "s3" \
    "https://object.storage.$BLUEPRINT_STACKIT_REGION.onstackit.cloud" \
    "bootstrap backend s3 endpoint"

  assert_quoted_assignment_equals "$foundation_backend" "bucket" "$BLUEPRINT_STACKIT_TFSTATE_BUCKET" "tfstate bucket"
  assert_quoted_assignment_equals "$foundation_backend" "region" "$BLUEPRINT_STACKIT_REGION" "backend region"
  assert_quoted_assignment_equals \
    "$foundation_backend" \
    "key" \
    "$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX/$env/foundation.tfstate" \
    "foundation backend key"
  assert_quoted_assignment_equals \
    "$foundation_backend" \
    "s3" \
    "https://object.storage.$BLUEPRINT_STACKIT_REGION.onstackit.cloud" \
    "foundation backend s3 endpoint"
done

placeholder_tokens=(
  "your-platform-blueprint"
  "your-github-org"
  "your-tenant-slug"
  "your-platform-slug"
  "your-stackit-project-id"
  "your-stackit-tfstate-bucket"
  "{{STACKIT_REGION}}"
  "{{STACKIT_TENANT_SLUG}}"
  "{{STACKIT_PLATFORM_SLUG}}"
  "{{STACKIT_PROJECT_ID}}"
  "{{STACKIT_TFSTATE_BUCKET}}"
  "{{STACKIT_TFSTATE_KEY_PREFIX}}"
  "__REPLACE_ME__"
)
scan_files=(
  "$contract_file"
  "$docs_config"
  "${stackit_bootstrap_tfvars_files[@]}"
  "${stackit_foundation_tfvars_files[@]}"
  "${stackit_bootstrap_backend_files[@]}"
  "${stackit_foundation_backend_files[@]}"
  "${argocd_files[@]}"
)

for token in "${placeholder_tokens[@]}"; do
  for file in "${scan_files[@]}"; do
    if grep -qF "$token" "$file"; then
      log_fatal "unresolved placeholder token '$token' found in $file"
    fi
  done
done

for file in "${consumer_root_files[@]}"; do
  [[ -f "$file" ]] || log_fatal "missing consumer-owned initialized file: $file"
  for token in "{{REPO_NAME}}" "{{DOCS_TITLE}}" "{{DOCS_TAGLINE}}" "{{DEFAULT_BRANCH}}" "{{TEMPLATE_VERSION}}"; do
    if grep -qF "$token" "$file"; then
      log_fatal "unresolved consumer template token '$token' found in $file"
    fi
  done
done

log_info "generated repository placeholder checks passed"
