#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/infra/rabbitmq.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"
source "$ROOT_DIR/scripts/lib/infra/identity_aware_proxy.sh"

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

bootstrap_stackit_seed_values() {
  local repo_slug github_org tenant_default platform_default platform_candidate bucket_default
  repo_slug="$(normalize_slug_component "${BLUEPRINT_REPO_NAME:-$(basename "$ROOT_DIR")}")"
  github_org="$(normalize_slug_component "${BLUEPRINT_GITHUB_ORG:-$repo_slug}")"

  tenant_default="$github_org"
  platform_candidate="${repo_slug%-blueprint}"
  if [[ -z "$platform_candidate" || "$platform_candidate" == "$repo_slug" ]]; then
    platform_candidate="$repo_slug"
  fi
  platform_default="$(normalize_slug_component "$platform_candidate")"

  set_default_env BLUEPRINT_STACKIT_REGION "${STACKIT_REGION:-eu01}"
  set_default_env BLUEPRINT_STACKIT_TENANT_SLUG "$tenant_default"
  set_default_env BLUEPRINT_STACKIT_PLATFORM_SLUG "$platform_default"
  set_default_env BLUEPRINT_STACKIT_PROJECT_ID "${STACKIT_PROJECT_ID:-${BLUEPRINT_STACKIT_TENANT_SLUG}-${BLUEPRINT_STACKIT_PLATFORM_SLUG}}"
  set_default_env BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX "terraform/state"

  bucket_default="$(normalize_bucket_name "${BLUEPRINT_STACKIT_TENANT_SLUG}-${BLUEPRINT_STACKIT_PLATFORM_SLUG}-tf-state")"
  set_default_env BLUEPRINT_STACKIT_TFSTATE_BUCKET "$bucket_default"
}

bootstrap_infra_directories() {
  ensure_dir "$ROOT_DIR/tests/infra/modules"
  ensure_dir "$ROOT_DIR/tests/infra/modules/observability"
  ensure_dir "$ROOT_DIR/scripts/lib/infra"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/dev"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/stage"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/prod"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/modules/observability"
  ensure_dir "$ROOT_DIR/infra/local/crossplane"
  ensure_dir "$ROOT_DIR/infra/local/helm/core"
  ensure_dir "$ROOT_DIR/infra/local/helm/observability"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/base"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/local"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/overlays/prod"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/root"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/environments/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/environments/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/environments/prod"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/base"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/environments/local"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/environments/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/environments/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/environments/prod"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/local"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/dev"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/stage"
  ensure_dir "$ROOT_DIR/infra/gitops/argocd/optional/prod"
}

bootstrap_infra_static_templates() {
  ensure_file_from_template "$ROOT_DIR/tests/infra/modules/observability/README.md" "infra" "tests/infra/modules/observability/README.md"
  ensure_file_from_template "$ROOT_DIR/infra/local/crossplane/kustomization.yaml" "infra" "infra/local/crossplane/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/crossplane/namespace.yaml" "infra" "infra/local/crossplane/namespace.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/core/argocd.values.yaml" "infra" "infra/local/helm/core/argocd.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/core/external-secrets.values.yaml" "infra" "infra/local/helm/core/external-secrets.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/core/crossplane.values.yaml" "infra" "infra/local/helm/core/crossplane.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/observability/grafana.values.yaml" "infra" "infra/local/helm/observability/grafana.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/local/helm/observability/otel-collector.values.yaml" "infra" "infra/local/helm/observability/otel-collector.values.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/base/kustomization.yaml" "infra" "infra/gitops/argocd/base/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/base/namespace.yaml" "infra" "infra/gitops/argocd/base/namespace.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/base/kustomization.yaml" "infra" "infra/gitops/platform/base/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/base/namespaces.yaml" "infra" "infra/gitops/platform/base/namespaces.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/environments/local/kustomization.yaml" "infra" "infra/gitops/platform/environments/local/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/environments/local/runtime-contract-configmap.yaml" "infra" "infra/gitops/platform/environments/local/runtime-contract-configmap.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/root/kustomization.yaml" "infra" "infra/gitops/argocd/root/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/root/applicationset-platform-environments.yaml" "infra" "infra/gitops/argocd/root/applicationset-platform-environments.yaml"

  local env
  for env in dev stage prod; do
    ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/environments/$env/kustomization.yaml" "infra" "infra/gitops/platform/environments/$env/kustomization.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/platform/environments/$env/runtime-contract-configmap.yaml" "infra" "infra/gitops/platform/environments/$env/runtime-contract-configmap.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/environments/$env/kustomization.yaml" "infra" "infra/gitops/argocd/environments/$env/kustomization.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/environments/$env/platform-config.yaml" "infra" "infra/gitops/argocd/environments/$env/platform-config.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/environments/$env/platform-application.yaml" "infra" "infra/gitops/argocd/environments/$env/platform-application.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/$env/kustomization.yaml" "infra" "infra/gitops/argocd/overlays/$env/kustomization.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/$env/appproject.yaml" "infra" "infra/gitops/argocd/overlays/$env/appproject.yaml"
    ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/$env/applicationset-platform-environments.yaml" "infra" "infra/gitops/argocd/overlays/$env/applicationset-platform-environments.yaml"
  done
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/local/kustomization.yaml" "infra" "infra/gitops/argocd/overlays/local/kustomization.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/local/appproject.yaml" "infra" "infra/gitops/argocd/overlays/local/appproject.yaml"
  ensure_file_from_template "$ROOT_DIR/infra/gitops/argocd/overlays/local/application-platform-local.yaml" "infra" "infra/gitops/argocd/overlays/local/application-platform-local.yaml"
}

bootstrap_stackit_terraform_scaffolding() {
  bootstrap_stackit_seed_values

  local stackit_tf_files=(
    "infra/cloud/stackit/terraform/bootstrap/versions.tf"
    "infra/cloud/stackit/terraform/bootstrap/providers.tf"
    "infra/cloud/stackit/terraform/bootstrap/variables.tf"
    "infra/cloud/stackit/terraform/bootstrap/main.tf"
    "infra/cloud/stackit/terraform/bootstrap/outputs.tf"
    "infra/cloud/stackit/terraform/foundation/versions.tf"
    "infra/cloud/stackit/terraform/foundation/providers.tf"
    "infra/cloud/stackit/terraform/foundation/variables.tf"
    "infra/cloud/stackit/terraform/foundation/locals.tf"
    "infra/cloud/stackit/terraform/foundation/main.tf"
    "infra/cloud/stackit/terraform/foundation/outputs.tf"
  )
  local rel
  for rel in "${stackit_tf_files[@]}"; do
    ensure_file_from_template "$ROOT_DIR/$rel" "infra" "$rel"
  done

  local env
  for env in dev stage prod; do
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env/$env.tfvars" \
      "infra" \
      "infra/cloud/stackit/terraform/bootstrap/env/$env.tfvars" \
      "STACKIT_PROJECT_ID=$BLUEPRINT_STACKIT_PROJECT_ID" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION" \
      "STACKIT_TENANT_SLUG=$BLUEPRINT_STACKIT_TENANT_SLUG" \
      "STACKIT_PLATFORM_SLUG=$BLUEPRINT_STACKIT_PLATFORM_SLUG" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX"

    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env/$env.tfvars" \
      "infra" \
      "infra/cloud/stackit/terraform/foundation/env/$env.tfvars" \
      "STACKIT_TENANT_SLUG=$BLUEPRINT_STACKIT_TENANT_SLUG" \
      "STACKIT_PLATFORM_SLUG=$BLUEPRINT_STACKIT_PLATFORM_SLUG" \
      "STACKIT_PROJECT_ID=$BLUEPRINT_STACKIT_PROJECT_ID" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"

    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend/$env.hcl" \
      "infra" \
      "infra/cloud/stackit/terraform/bootstrap/state-backend/$env.hcl" \
      "STACKIT_TFSTATE_BUCKET=$BLUEPRINT_STACKIT_TFSTATE_BUCKET" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"

    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend/$env.hcl" \
      "infra" \
      "infra/cloud/stackit/terraform/foundation/state-backend/$env.hcl" \
      "STACKIT_TFSTATE_BUCKET=$BLUEPRINT_STACKIT_TFSTATE_BUCKET" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"
  done

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
    case "$module" in
    rabbitmq)
      rabbitmq_seed_env_defaults
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml" \
        "RABBITMQ_HELM_RELEASE=$RABBITMQ_HELM_RELEASE" \
        "RABBITMQ_USERNAME=$RABBITMQ_USERNAME" \
        "RABBITMQ_PASSWORD_SECRET_NAME=$(rabbitmq_password_secret_name)"
      ;;
    public-endpoints)
      public_endpoints_seed_env_defaults
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml"
      ;;
    identity-aware-proxy)
      identity_aware_proxy_seed_env_defaults
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml" \
        "IAP_CONFIG_SECRET_NAME=$(identity_aware_proxy_config_secret_name)" \
        "KEYCLOAK_ISSUER_URL=${KEYCLOAK_ISSUER_URL:-https://keycloak.example/realms/platform}" \
        "IAP_UPSTREAM_URL=$IAP_UPSTREAM_URL" \
        "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
        "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
        "IAP_PUBLIC_HOST=$(identity_aware_proxy_public_host)" \
        "IAP_REDIRECT_URL=$(identity_aware_proxy_redirect_url)"
      ;;
    *)
      ensure_file_from_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml"
      ;;
    esac
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
  # ArgoCD stackit overlays are static files and are materialized from
  # template-synchronized assets in bootstrap_infra_static_templates.
  :
}

bootstrap_optional_manifest() {
  local module="$1"
  local env="$2"

  case "$module" in
  public-endpoints)
    public_endpoints_seed_env_defaults
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/gitops/argocd/optional/$env/$module.yaml" \
      "infra" \
      "infra/gitops/argocd/optional/public-endpoints.application.yaml.tmpl" \
      "ENV=$env" \
      "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
      "PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE=$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
      "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
      "PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" \
      "PUBLIC_ENDPOINTS_HELM_RELEASE=$PUBLIC_ENDPOINTS_HELM_RELEASE" \
      "PUBLIC_ENDPOINTS_HELM_CHART_VERSION=$PUBLIC_ENDPOINTS_HELM_CHART_VERSION" \
      "PUBLIC_ENDPOINTS_GATEWAY_MANIFEST=$(public_endpoints_gateway_manifest_content)"
    ;;
  identity-aware-proxy)
    identity_aware_proxy_seed_env_defaults
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/gitops/argocd/optional/$env/$module.yaml" \
      "infra" \
      "infra/gitops/argocd/optional/identity-aware-proxy.application.yaml.tmpl" \
      "ENV=$env" \
      "IAP_NAMESPACE=$IAP_NAMESPACE" \
      "IAP_HELM_RELEASE=$IAP_HELM_RELEASE" \
      "IAP_HELM_CHART_VERSION=$IAP_HELM_CHART_VERSION" \
      "IAP_CONFIG_SECRET_NAME=$(identity_aware_proxy_config_secret_name)" \
      "KEYCLOAK_ISSUER_URL=${KEYCLOAK_ISSUER_URL:-https://keycloak.example/realms/platform}" \
      "IAP_UPSTREAM_URL=$IAP_UPSTREAM_URL" \
      "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
      "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
      "IAP_PUBLIC_HOST=$(identity_aware_proxy_public_host)" \
      "IAP_REDIRECT_URL=$(identity_aware_proxy_redirect_url)"
    ;;
  *)
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/gitops/argocd/optional/$env/$module.yaml" \
      "infra" \
      "infra/gitops/argocd/optional/module.yaml.tmpl" \
      "MODULE=$module" \
      "ENV=$env"
    ;;
  esac
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

  if is_module_enabled public-endpoints; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest public-endpoints "$env"
      rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
    done
  fi

  if is_module_enabled identity-aware-proxy; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest identity-aware-proxy "$env"
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
    for env in local dev stage prod; do
      prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/public-endpoints.yaml" && pruned_path_count=$((pruned_path_count + 1))
    done
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
    for env in local dev stage prod; do
      prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/identity-aware-proxy.yaml" && pruned_path_count=$((pruned_path_count + 1))
    done
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
