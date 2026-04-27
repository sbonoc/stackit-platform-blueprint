#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
blueprint_load_env_defaults
if blueprint_repo_is_generated_consumer; then
  blueprint_require_runtime_env
fi
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/infra/postgres.sh"
source "$ROOT_DIR/scripts/lib/infra/object_storage.sh"
source "$ROOT_DIR/scripts/lib/infra/rabbitmq.sh"
source "$ROOT_DIR/scripts/lib/infra/opensearch.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"
source "$ROOT_DIR/scripts/lib/infra/identity_aware_proxy.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"

start_script_metric_trap "infra_bootstrap"

usage() {
  cat <<'USAGE'
Usage: bootstrap.sh

Bootstraps infra-scoped scaffolding only:
- required infra directories and baseline manifests,
- stack-specific Terraform and ArgoCD overlay scaffolding,
- optional-module infra scaffolding when enabled,
- preserves disabled optional-module scaffolding for safe future enablement.

When present, blueprint/repo.init.env and blueprint/repo.init.secrets.env are auto-loaded.
In generated repos, init-managed identity files are not recreated here.
Restore them intentionally with BLUEPRINT_INIT_FORCE=true make blueprint-init-repo.
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
set_default_env APP_RUNTIME_GITOPS_ENABLED "true"
app_runtime_gitops_enabled="$(shell_normalize_bool_truefalse "$APP_RUNTIME_GITOPS_ENABLED")"
log_metric "app_runtime_gitops_enabled_total" "1" "enabled=$app_runtime_gitops_enabled"

infra_bootstrap_init_managed_skip_count=0
infra_bootstrap_consumer_seeded_skip_count=0

ensure_infra_template_file() {
  local relative_path="$1"
  local template_rel="${2:-$relative_path}"
  if blueprint_repo_is_generated_consumer && blueprint_path_is_init_managed "$relative_path"; then
    if [[ ! -f "$ROOT_DIR/$relative_path" ]]; then
      log_fatal "missing init-managed file: $relative_path; rerun with $(blueprint_init_force_env_var)=true make blueprint-init-repo"
    fi
    infra_bootstrap_init_managed_skip_count=$((infra_bootstrap_init_managed_skip_count + 1))
    return 0
  fi

  if blueprint_repo_is_generated_consumer && blueprint_path_is_consumer_seeded "$relative_path"; then
    log_info "skipping consumer-seeded file (consumer-owned): $relative_path"
    infra_bootstrap_consumer_seeded_skip_count=$((infra_bootstrap_consumer_seeded_skip_count + 1))
    return 0
  fi

  ensure_file_from_template "$ROOT_DIR/$relative_path" "infra" "$template_rel"
}

ensure_infra_rendered_file() {
  local relative_path="$1"
  local template_rel="$2"
  shift 2 || true

  if blueprint_repo_is_generated_consumer && blueprint_path_is_init_managed "$relative_path"; then
    if [[ ! -f "$ROOT_DIR/$relative_path" ]]; then
      log_fatal "missing init-managed file: $relative_path; rerun with $(blueprint_init_force_env_var)=true make blueprint-init-repo"
    fi
    infra_bootstrap_init_managed_skip_count=$((infra_bootstrap_init_managed_skip_count + 1))
    return 0
  fi

  if blueprint_repo_is_generated_consumer && blueprint_path_is_consumer_seeded "$relative_path"; then
    log_info "skipping consumer-seeded file (consumer-owned): $relative_path"
    infra_bootstrap_consumer_seeded_skip_count=$((infra_bootstrap_consumer_seeded_skip_count + 1))
    return 0
  fi

  ensure_file_from_rendered_template "$ROOT_DIR/$relative_path" "infra" "$template_rel" "$@"
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
  # Core directories always required regardless of enabled optional modules.
  # Conditional-module scaffold directories (e.g. infra/local/helm/observability,
  # infra/cloud/stackit/terraform/modules/observability, tests/infra/modules/observability)
  # are created by bootstrap_optional_module_scaffolding() when the module is enabled,
  # keeping the working tree clean for disabled modules.
  ensure_dir "$ROOT_DIR/tests/infra/modules"
  ensure_dir "$ROOT_DIR/scripts/lib/infra"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/env"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/bootstrap/state-backend"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/env"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/foundation/state-backend"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/dev"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/stage"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/environments/prod"
  ensure_dir "$ROOT_DIR/infra/local/crossplane"
  ensure_dir "$ROOT_DIR/infra/local/helm/core"
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
  ensure_dir "$ROOT_DIR/infra/gitops/platform/base/apps"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/base/security"
  ensure_dir "$ROOT_DIR/infra/gitops/platform/base/extensions"
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
  # Observability module files (tests/infra/modules/observability/, infra/local/helm/observability/)
  # are seeded by bootstrap_observability_module_scaffold() when OBSERVABILITY_ENABLED=true.
  # They must not be created here because blueprint-contract enforces their absence when disabled.
  ensure_infra_template_file "infra/local/crossplane/kustomization.yaml"
  ensure_infra_template_file "infra/local/crossplane/namespace.yaml"
  ensure_infra_template_file "infra/local/helm/core/argocd.values.yaml"
  ensure_infra_template_file "infra/local/helm/core/external-secrets.values.yaml"
  ensure_infra_template_file "infra/local/helm/core/cert-manager.values.yaml"
  ensure_infra_template_file "infra/local/helm/core/crossplane.values.yaml"
  ensure_infra_template_file "infra/gitops/argocd/base/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/argocd/base/namespace.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/namespaces.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/apps/kustomization.yaml"
  local _app_kust_tmpl _app_manifest
  _app_kust_tmpl="$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml"
  if [[ ! -f "$_app_kust_tmpl" ]]; then
    log_fatal "missing infra template kustomization: $_app_kust_tmpl"
  fi
  while IFS= read -r _app_manifest; do
    [[ -z "$_app_manifest" ]] && continue
    ensure_infra_template_file "infra/gitops/platform/base/apps/$_app_manifest"
  done < <(sed -n 's/^[[:space:]]*-[[:space:]]*\([^[:space:]#][^[:space:]#]*\.yaml\).*/\1/p' "$_app_kust_tmpl")
  ensure_infra_template_file "infra/gitops/platform/base/security/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/security/runtime-source-store.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml"
  ensure_infra_template_file "infra/gitops/platform/base/extensions/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/platform/environments/local/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/platform/environments/local/runtime-contract-configmap.yaml"
  ensure_infra_template_file "infra/gitops/argocd/root/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/argocd/root/applicationset-platform-environments.yaml"

  local env
  for env in dev stage prod; do
    ensure_infra_template_file "infra/gitops/platform/environments/$env/kustomization.yaml"
    ensure_infra_template_file "infra/gitops/platform/environments/$env/runtime-contract-configmap.yaml"
    ensure_infra_template_file "infra/gitops/argocd/environments/$env/kustomization.yaml"
    ensure_infra_template_file "infra/gitops/argocd/environments/$env/platform-config.yaml"
    ensure_infra_template_file "infra/gitops/argocd/environments/$env/platform-application.yaml"
    ensure_infra_template_file "infra/gitops/argocd/overlays/$env/kustomization.yaml"
    ensure_infra_template_file "infra/gitops/argocd/overlays/$env/appproject.yaml"
    ensure_infra_template_file "infra/gitops/argocd/overlays/$env/applicationset-platform-environments.yaml"
  done
  ensure_infra_template_file "infra/gitops/argocd/overlays/local/kustomization.yaml"
  ensure_infra_template_file "infra/gitops/argocd/overlays/local/appproject.yaml"
  ensure_infra_template_file "infra/gitops/argocd/overlays/local/application-platform-local.yaml"
  ensure_infra_template_file "infra/gitops/argocd/overlays/local/keycloak.yaml"
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
    ensure_infra_template_file "$rel"
  done

  local env
  for env in dev stage prod; do
    ensure_infra_rendered_file \
      "infra/cloud/stackit/terraform/bootstrap/env/$env.tfvars" \
      "infra/cloud/stackit/terraform/bootstrap/env/$env.tfvars" \
      "STACKIT_PROJECT_ID=$BLUEPRINT_STACKIT_PROJECT_ID" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION" \
      "STACKIT_TENANT_SLUG=$BLUEPRINT_STACKIT_TENANT_SLUG" \
      "STACKIT_PLATFORM_SLUG=$BLUEPRINT_STACKIT_PLATFORM_SLUG" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX"

    ensure_infra_rendered_file \
      "infra/cloud/stackit/terraform/foundation/env/$env.tfvars" \
      "infra/cloud/stackit/terraform/foundation/env/$env.tfvars" \
      "STACKIT_TENANT_SLUG=$BLUEPRINT_STACKIT_TENANT_SLUG" \
      "STACKIT_PLATFORM_SLUG=$BLUEPRINT_STACKIT_PLATFORM_SLUG" \
      "STACKIT_PROJECT_ID=$BLUEPRINT_STACKIT_PROJECT_ID" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"

    ensure_infra_rendered_file \
      "infra/cloud/stackit/terraform/bootstrap/state-backend/$env.hcl" \
      "infra/cloud/stackit/terraform/bootstrap/state-backend/$env.hcl" \
      "STACKIT_TFSTATE_BUCKET=$BLUEPRINT_STACKIT_TFSTATE_BUCKET" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"

    ensure_infra_rendered_file \
      "infra/cloud/stackit/terraform/foundation/state-backend/$env.hcl" \
      "infra/cloud/stackit/terraform/foundation/state-backend/$env.hcl" \
      "STACKIT_TFSTATE_BUCKET=$BLUEPRINT_STACKIT_TFSTATE_BUCKET" \
      "STACKIT_TFSTATE_KEY_PREFIX=$BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX" \
      "STACKIT_REGION=$BLUEPRINT_STACKIT_REGION"
  done

  for env in dev stage prod; do
    ensure_infra_template_file \
      "infra/cloud/stackit/terraform/environments/$env/main.tf" \
      "infra/cloud/stackit/terraform/main.tf"
  done
  # Observability terraform module is seeded by bootstrap_observability_module_scaffold()
  # when OBSERVABILITY_ENABLED=true.  Creating it here unconditionally violates the
  # blueprint contract: paths_required_when_enabled must be absent when the module is disabled.
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
    postgres)
      postgres_init_env
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml" \
        "POSTGRES_HELM_RELEASE=$POSTGRES_HELM_RELEASE" \
        "POSTGRES_USER=$POSTGRES_USER" \
        "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" \
        "POSTGRES_DB_NAME=$POSTGRES_DB_NAME" \
        "POSTGRES_IMAGE_REGISTRY=$POSTGRES_IMAGE_REGISTRY" \
        "POSTGRES_IMAGE_REPOSITORY=$POSTGRES_IMAGE_REPOSITORY" \
        "POSTGRES_IMAGE_TAG=$POSTGRES_IMAGE_TAG"
      ;;
    object-storage)
      object_storage_init_env
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml" \
        "OBJECT_STORAGE_HELM_RELEASE=$OBJECT_STORAGE_HELM_RELEASE" \
        "OBJECT_STORAGE_ACCESS_KEY=$OBJECT_STORAGE_ACCESS_KEY" \
        "OBJECT_STORAGE_SECRET_KEY=$OBJECT_STORAGE_SECRET_KEY" \
        "OBJECT_STORAGE_BUCKET_NAME=$OBJECT_STORAGE_BUCKET_NAME" \
        "OBJECT_STORAGE_IMAGE_REGISTRY=$OBJECT_STORAGE_IMAGE_REGISTRY" \
        "OBJECT_STORAGE_IMAGE_REPOSITORY=$OBJECT_STORAGE_IMAGE_REPOSITORY" \
        "OBJECT_STORAGE_IMAGE_TAG=$OBJECT_STORAGE_IMAGE_TAG" \
        "OBJECT_STORAGE_CLIENT_IMAGE_REGISTRY=$OBJECT_STORAGE_CLIENT_IMAGE_REGISTRY" \
        "OBJECT_STORAGE_CLIENT_IMAGE_REPOSITORY=$OBJECT_STORAGE_CLIENT_IMAGE_REPOSITORY" \
        "OBJECT_STORAGE_CLIENT_IMAGE_TAG=$OBJECT_STORAGE_CLIENT_IMAGE_TAG"
      ;;
    rabbitmq)
      rabbitmq_seed_env_defaults
      ensure_file_from_rendered_template \
        "$ROOT_DIR/infra/local/helm/$module/values.yaml" \
        "infra" \
        "infra/local/helm/$module/values.yaml" \
        "RABBITMQ_HELM_RELEASE=$RABBITMQ_HELM_RELEASE" \
        "RABBITMQ_USERNAME=$RABBITMQ_USERNAME" \
        "RABBITMQ_PASSWORD_SECRET_NAME=$(rabbitmq_password_secret_name)" \
        "RABBITMQ_IMAGE_REGISTRY=$RABBITMQ_IMAGE_REGISTRY" \
        "RABBITMQ_IMAGE_REPOSITORY=$RABBITMQ_IMAGE_REPOSITORY" \
        "RABBITMQ_IMAGE_TAG=$RABBITMQ_IMAGE_TAG"
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
        "KEYCLOAK_ISSUER_URL=$KEYCLOAK_ISSUER_URL" \
        "IAP_UPSTREAM_URL=$IAP_UPSTREAM_URL" \
        "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
        "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
        "IAP_PUBLIC_HOST=$(identity_aware_proxy_public_host)" \
        "IAP_REDIRECT_URL=$(identity_aware_proxy_redirect_url)" \
        "IAP_IMAGE_REGISTRY=$IAP_IMAGE_REGISTRY" \
        "IAP_IMAGE_REPOSITORY=$IAP_IMAGE_REPOSITORY" \
        "IAP_IMAGE_TAG=$IAP_IMAGE_TAG"
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

bootstrap_observability_module_scaffold() {
  # Observability uses two Helm values files (grafana + otel-collector) rather than
  # the single values.yaml that bootstrap_module_scaffold() produces, so it requires
  # a dedicated scaffold function.  All paths created here correspond 1-to-1 with
  # the paths_required_when_enabled list in the observability optional_module contract.
  ensure_dir "$ROOT_DIR/tests/infra/modules/observability"
  ensure_dir "$ROOT_DIR/infra/cloud/stackit/terraform/modules/observability"
  ensure_dir "$ROOT_DIR/infra/local/helm/observability"
  ensure_infra_template_file "tests/infra/modules/observability/README.md"
  ensure_infra_template_file \
    "infra/cloud/stackit/terraform/modules/observability/main.tf" \
    "infra/cloud/stackit/terraform/main.tf"
  ensure_infra_template_file "infra/local/helm/observability/grafana.values.yaml"
  ensure_infra_template_file "infra/local/helm/observability/otel-collector.values.yaml"
  log_metric "observability_module_scaffold_total" "1" "status=scaffolded"
}

bootstrap_optional_module_scaffolding() {
  local scaffolded_modules=()

  if is_module_enabled observability; then
    bootstrap_observability_module_scaffold
    scaffolded_modules+=("observability")
  fi

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

  if is_module_enabled opensearch; then
    bootstrap_module_scaffold opensearch false false
    scaffolded_modules+=("opensearch")
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
      "PUBLIC_ENDPOINTS_HELM_CHART_VERSION=$PUBLIC_ENDPOINTS_HELM_CHART_VERSION"
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
      "IAP_CONFIG_SECRET_NAME=$(identity_aware_proxy_argocd_config_secret_name)" \
      "KEYCLOAK_ISSUER_URL=$KEYCLOAK_ISSUER_URL" \
      "IAP_UPSTREAM_URL=$IAP_UPSTREAM_URL" \
      "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
      "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
      "IAP_PUBLIC_HOST=$(identity_aware_proxy_public_host)" \
      "IAP_REDIRECT_URL=$(identity_aware_proxy_redirect_url)" \
      "IAP_IMAGE_REGISTRY=$IAP_IMAGE_REGISTRY" \
      "IAP_IMAGE_REPOSITORY=$IAP_IMAGE_REPOSITORY" \
      "IAP_IMAGE_TAG=$IAP_IMAGE_TAG"
    ;;
  keycloak)
    keycloak_seed_env_defaults
    local keycloak_extra_manifests
    local keycloak_sync_automated_block
    keycloak_extra_manifests="$(keycloak_extra_manifests_block)"
    keycloak_sync_automated_block="$(keycloak_sync_automated_block "$env")"
    # Keycloak is a mandatory identity baseline; render under argocd/core even
    # though other modules continue using argocd/optional.
    ensure_file_from_rendered_template \
      "$ROOT_DIR/infra/gitops/argocd/core/$env/$module.yaml" \
      "infra" \
      "infra/gitops/argocd/core/keycloak.application.yaml.tmpl" \
      "ENV=$env" \
      "KEYCLOAK_NAMESPACE=$KEYCLOAK_NAMESPACE" \
      "KEYCLOAK_HELM_RELEASE=$KEYCLOAK_HELM_RELEASE" \
      "KEYCLOAK_HELM_CHART_VERSION=$KEYCLOAK_HELM_CHART_VERSION" \
      "KEYCLOAK_IMAGE_TAG=$KEYCLOAK_IMAGE_TAG" \
      "KEYCLOAK_ADMIN_USERNAME=$KEYCLOAK_ADMIN_USERNAME" \
      "KEYCLOAK_PUBLIC_HOST=$KEYCLOAK_PUBLIC_HOST" \
      "KEYCLOAK_ACME_EMAIL=$KEYCLOAK_ACME_EMAIL" \
      "KEYCLOAK_ACME_SERVER=$KEYCLOAK_ACME_SERVER" \
      "KEYCLOAK_GATEWAY_NAME=$KEYCLOAK_GATEWAY_NAME" \
      "KEYCLOAK_GATEWAY_CLASS_NAME=$KEYCLOAK_GATEWAY_CLASS_NAME" \
      "KEYCLOAK_TLS_SECRET_NAME=$KEYCLOAK_TLS_SECRET_NAME" \
      "KEYCLOAK_SYNC_AUTOMATED_BLOCK=$keycloak_sync_automated_block" \
      "KEYCLOAK_EXTRA_MANIFESTS_BLOCK=$keycloak_extra_manifests"
    if [[ "$env" == "local" ]]; then
      local keycloak_core_manifest="$ROOT_DIR/infra/gitops/argocd/core/local/keycloak.yaml"
      local keycloak_overlay_manifest="$ROOT_DIR/infra/gitops/argocd/overlays/local/keycloak.yaml"
      if [[ ! -f "$keycloak_core_manifest" ]]; then
        log_fatal "missing rendered local keycloak manifest: $keycloak_core_manifest"
      fi
      cp "$keycloak_core_manifest" "$keycloak_overlay_manifest"
      log_info "synchronized local keycloak overlay manifest from rendered core contract"
    fi
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

  # Keycloak is a mandatory identity baseline — always rendered.
  for env in local dev stage prod; do
    bootstrap_optional_manifest keycloak "$env"
    rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
  done

  # Observability manifests (infra/gitops/argocd/optional/${ENV}/observability.yaml) are
  # listed in paths_required_when_enabled and must be absent when observability is disabled.
  if is_module_enabled observability; then
    for env in local dev stage prod; do
      bootstrap_optional_manifest observability "$env"
      rendered_optional_manifest_count=$((rendered_optional_manifest_count + 1))
    done
  fi

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

report_disabled_module_scaffolding_preserved() {
  local modules=(
    observability
    workflows
    langfuse
    postgres
    neo4j
    object-storage
    rabbitmq
    opensearch
    dns
    public-endpoints
    secrets-manager
    kms
    identity-aware-proxy
  )
  local disabled_modules=()
  local module

  for module in "${modules[@]}"; do
    if ! is_module_enabled "$module"; then
      disabled_modules+=("$module")
    fi
  done

  log_metric "optional_module_disabled_scaffold_preserved_count" "${#disabled_modules[@]}"
  if [[ "${#disabled_modules[@]}" -gt 0 ]]; then
    # Disabled module scaffolding stays on disk so flag toggles and review/test
    # runs cannot silently delete tracked repo content.
    log_info "disabled optional-module scaffolding preserved: ${disabled_modules[*]}"
  else
    log_info "all optional-module scaffolding active for current module flags"
  fi
}

bootstrap_infra_directories
bootstrap_infra_static_templates
bootstrap_stackit_terraform_scaffolding
bootstrap_optional_module_scaffolding
bootstrap_argocd_overlay_scaffolding
bootstrap_optional_manifests
report_disabled_module_scaffolding_preserved
log_metric "infra_init_managed_skip_count" "$infra_bootstrap_init_managed_skip_count"
log_metric "infra_consumer_seeded_skip_count" "$infra_bootstrap_consumer_seeded_skip_count"

log_info "infra bootstrap complete"
