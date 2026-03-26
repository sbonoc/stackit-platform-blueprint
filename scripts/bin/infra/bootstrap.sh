#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"

start_script_metric_trap "infra_bootstrap"

usage() {
  cat <<'USAGE'
Usage: bootstrap.sh

Bootstraps infra-scoped scaffolding only:
- required infra directories and baseline manifests,
- stack-specific Terraform and ArgoCD overlay scaffolding,
- optional-module infra scaffolding when enabled,
- stale optional-module infra scaffolding pruning when disabled.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command bash
require_command git
require_command make
require_command python3

bootstrap_infra_directories() {
  ensure_dir "$ROOT_DIR/tests/infra/modules"
  ensure_dir "$ROOT_DIR/tests/infra/modules/observability"
  ensure_dir "$ROOT_DIR/scripts/lib/infra"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/dev"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/stage"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/prod"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/modules/observability"
  ensure_dir "$ROOT_DIR/infra/local/crossplane"
  ensure_dir "$ROOT_DIR/infra/local/helm/observability"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/base"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/local"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/prod"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/local"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/prod"
}

bootstrap_infra_static_templates() {
  ensure_file_from_template "$ROOT_DIR/tests/infra/modules/observability/README.md" "infra" "tests/infra/modules/observability/README.md"
  ensure_file_from_template "$ROOT_DIR/infra/local/crossplane/kustomization.yaml" "infra" "infra/local/crossplane/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/crossplane/namespace.yaml" "infra" "infra/local/crossplane/namespace.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/observability/grafana.values.yaml" "infra" "infra/local/helm/observability/grafana.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/observability/otel-collector.values.yaml" "infra" "infra/local/helm/observability/otel-collector.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/base/kustomization.yaml" "infra" "infra/gitops/argocd/base/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/base/namespace.yaml" "infra" "infra/gitops/argocd/base/namespace.yaml"
}

bootstrap_stackit_terraform_scaffolding() {
  local env
  for env in dev stage prod; do
    ensure_file_from_template \
      "$ROOT_DIR/infra/cloud/stackit/terraform/environments/$env/main.tf" \
      "infra" \
      "infra/cloud/stackit/terraform/main.tf"
  done

  ensure_file_from_template \
    "$ROOT_DIR/infra/cloud/stackit/terraform/modules/observability/main.tf" \
    "infra" \
    "infra/cloud/stackit/terraform/main.tf"
}

bootstrap_module_scaffold() {
  local module="$1"
  local include_helm_values="$2"
  local include_workflows_dags="$3"

  ensure_dir "$ROOT_DIR/tests/infra/modules/$module"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/modules/$module"
  ensure_file_from_template "$ROOT_DIR/tests/infra/modules/$module/README.md" "infra" "tests/infra/modules/$module/README.md"
  ensure_file_from_template \
    "$ROOT_DIR/infra/cloud/stackit/terraform/modules/$module/main.tf" \
    "infra" \
    "infra/cloud/stackit/terraform/main.tf"

  if [[ "$include_helm_values" == "true" ]]; then
    ensure_dir "$ROOT_DIR/infra/local/helm/$module"
    ensure_file_from_template \
      "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
      "infra" \
      "infra/local/helm/$module/values.yaml"
  fi

  if [[ "$include_workflows_dags" == "true" ]]; then
    ensure_dir "$ROOT_DIR/dags"
    ensure_file_from_template "$ROOT_DIR/dags/.airflowignore" "infra" "dags/.airflowignore"
    ensure_file_from_template "$ROOT_DIR/dags/_bootstrap.py" "infra" "dags/_bootstrap.py"
  fi
}

bootstrap_optional_module_scaffolding() {
  local scaffolded_modules=()

  if is_module_enabled workflows; then
    bootstrap_module_scaffold workflows false true
    scaffolded_modules+=("workflows")
  fi

  if is_module_enabled langfuse; then
    bootstrap_module_scaffold langfuse true false
    scaffolded_modules+=("langfuse")
  fi

  if is_module_enabled postgres; then
    bootstrap_module_scaffold postgres true false
    scaffolded_modules+=("postgres")
  fi

  if is_module_enabled neo4j; then
    bootstrap_module_scaffold neo4j true false
    scaffolded_modules+=("neo4j")
  fi

  if is_module_enabled object-storage; then
    bootstrap_module_scaffold object-storage true false
    scaffolded_modules+=("object-storage")
  fi

  if is_module_enabled rabbitmq; then
    bootstrap_module_scaffold rabbitmq true false
    scaffolded_modules+=("rabbitmq")
  fi

  if is_module_enabled dns; then
    bootstrap_module_scaffold dns false false
    scaffolded_modules+=("dns")
  fi

  if is_module_enabled public-endpoints; then
    bootstrap_module_scaffold public-endpoints true false
    scaffolded_modules+=("public-endpoints")
  fi

  if is_module_enabled secrets-manager; then
    bootstrap_module_scaffold secrets-manager false false
    scaffolded_modules+=("secrets-manager")
  fi

  if is_module_enabled kms; then
    bootstrap_module_scaffold kms false false
    scaffolded_modules+=("kms")
  fi

  if is_module_enabled identity-aware-proxy; then
    bootstrap_module_scaffold identity-aware-proxy true false
    scaffolded_modules+=("identity-aware-proxy")
  fi

  log_metric "optional_module_scaffold_count" "${#scaffolded_modules[@]}"
  if [[ "${#scaffolded_modules[@]}" -gt 0 ]]; then
    log_info "optional module infra scaffolding materialized: ${scaffolded_modules[*]}"
  else
    log_info "optional module infra scaffolding skipped; no optional modules enabled"
  fi
}

bootstrap_argocd_overlay_scaffolding() {
  local env
  for env in local dev stage prod; do
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/gitops/argocd/overlays/$env/kustomization.yaml" \
      "infra" \
      "infra/gitops/argocd/overlays/kustomization.yaml.tmpl" \
      "ENV=$env"
  done
}

bootstrap_optional_manifest() {
  local module="$1"
  local env="$2"
  ensure_file_from_rendered_template \
    "$ROOT_DIR/infra/gitops/argocd/optional/$env/$module.yaml" \
    "infra" \
    "infra/gitops/argocd/optional/module.yaml.tmpl" \
    "MODULE=$module" \
    "ENV=$env"
}

bootstrap_optional_manifests() {
  local rendered_optional_manifest_count=0
  local env
  for env in local dev stage prod; do
    bootstrap_optional_manifest observability "$env"
    rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
  done

  if is_module_enabled workflows; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest workflows "$env"
      rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
    done
  fi

  if is_module_enabled langfuse; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest langfuse "$env"
      rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
    done
  fi

  if is_module_enabled neo4j; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest neo4j "$env"
      rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
    done
  fi

  log_metric "optional_manifest_rendered_count" "$rendered_optional_manifest_count"
}

prune_path_if_exists() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    return 1
  fi

  if [[ -d "$path" ]]; then
    run_cmd rm -rf "$path"
  else
    run_cmd rm -f "$path"
  fi
  log_info "pruned stale optional-module scaffold path: $path"
  return 0
}

prune_optional_module_scaffolding() {
  local pruned_path_count=0
  local env

  if ! is_module_enabled workflows; then
    prune_path_if_exists "$ROOT_DIR/dags" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/workflows" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/workflows" && pruned_path_count=$((pruned_path_count + 1))
    for env in local dev stage prod; do
      prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/workflows.yaml" && pruned_path_count=$((pruned_path_count + 1))
    done
  fi

  if ! is_module_enabled langfuse; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/langfuse" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/langfuse" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/langfuse" && pruned_path_count=$((pruned_path_count + 1))
    for env in local dev stage prod; do
      prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/langfuse.yaml" && pruned_path_count=$((pruned_path_count + 1))
    done
  fi

  if ! is_module_enabled postgres; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/postgres" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/postgres" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/postgres" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled neo4j; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/neo4j" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/neo4j" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/neo4j" && pruned_path_count=$((pruned_path_count + 1))
    for env in local dev stage prod; do
      prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/neo4j.yaml" && pruned_path_count=$((pruned_path_count + 1))
    done
  fi

  if ! is_module_enabled object-storage; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/object-storage" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/object-storage" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/object-storage" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled rabbitmq; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/rabbitmq" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/rabbitmq" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/rabbitmq" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled dns; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/dns" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/dns" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled public-endpoints; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/public-endpoints" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/public-endpoints" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/public-endpoints" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled secrets-manager; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/secrets-manager" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/secrets-manager" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled kms; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/kms" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/kms" && pruned_path_count=$((pruned_path_count + 1))
  fi

  if ! is_module_enabled identity-aware-proxy; then
    prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/identity-aware-proxy" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/infra/local/helm/identity-aware-proxy" && pruned_path_count=$((pruned_path_count + 1))
    prune_path_if_exists "$ROOT_DIR/tests/infra/modules/identity-aware-proxy" && pruned_path_count=$((pruned_path_count + 1))
  fi

  log_metric "optional_module_pruned_path_count" "$pruned_path_count"
  if [[ "$pruned_path_count" -gt 0 ]]; then
    log_info "optional module infra scaffolding pruned paths=$pruned_path_count"
  else
    log_info "optional module infra scaffolding prune skipped; no stale disabled-module paths found"
  fi
}

bootstrap_infra_directories
bootstrap_infra_static_templates
bootstrap_stackit_terraform_scaffolding
bootstrap_optional_module_scaffolding
bootstrap_argocd_overlay_scaffolding
bootstrap_optional_manifests
prune_optional_module_scaffolding

log_info "infra bootstrap complete"
