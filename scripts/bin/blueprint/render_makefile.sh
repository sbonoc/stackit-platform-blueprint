#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"

start_script_metric_trap "blueprint_render_makefile"

usage() {
  cat <<'USAGE'
Usage: render_makefile.sh

Renders blueprint-managed make/blueprint.generated.mk from template with
optional-module targets materialized only for enabled module flags.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command bash
require_command make

makefile_module_phony_suffix() {
  local module="$1"
  if ! is_module_enabled "$module"; then
    return 0
  fi

  case "$module" in
  observability)
    cat <<'OUT'
 \
  infra-observability-plan infra-observability-apply infra-observability-deploy infra-observability-smoke infra-observability-destroy
OUT
    ;;
  workflows)
    cat <<'OUT'
 \
  infra-stackit-workflows-plan infra-stackit-workflows-apply infra-stackit-workflows-reconcile infra-stackit-workflows-dag-deploy infra-stackit-workflows-dag-parse-smoke infra-stackit-workflows-smoke infra-stackit-workflows-destroy
OUT
    ;;
  langfuse)
    cat <<'OUT'
 \
  infra-langfuse-plan infra-langfuse-apply infra-langfuse-deploy infra-langfuse-smoke infra-langfuse-destroy
OUT
    ;;
  postgres)
    cat <<'OUT'
 \
  infra-postgres-plan infra-postgres-apply infra-postgres-smoke infra-postgres-destroy
OUT
    ;;
  neo4j)
    cat <<'OUT'
 \
  infra-neo4j-plan infra-neo4j-apply infra-neo4j-deploy infra-neo4j-smoke infra-neo4j-destroy
OUT
    ;;
  object-storage)
    cat <<'OUT'
 \
  infra-object-storage-plan infra-object-storage-apply infra-object-storage-smoke infra-object-storage-destroy
OUT
    ;;
  rabbitmq)
    cat <<'OUT'
 \
  infra-rabbitmq-plan infra-rabbitmq-apply infra-rabbitmq-smoke infra-rabbitmq-destroy
OUT
    ;;
  dns)
    cat <<'OUT'
 \
  infra-dns-plan infra-dns-apply infra-dns-smoke infra-dns-destroy
OUT
    ;;
  public-endpoints)
    cat <<'OUT'
 \
  infra-public-endpoints-plan infra-public-endpoints-apply infra-public-endpoints-deploy infra-public-endpoints-smoke infra-public-endpoints-destroy
OUT
    ;;
  secrets-manager)
    cat <<'OUT'
 \
  infra-secrets-manager-plan infra-secrets-manager-apply infra-secrets-manager-smoke infra-secrets-manager-destroy
OUT
    ;;
  kms)
    cat <<'OUT'
 \
  infra-kms-plan infra-kms-apply infra-kms-smoke infra-kms-destroy
OUT
    ;;
  identity-aware-proxy)
    cat <<'OUT'
 \
  infra-identity-aware-proxy-plan infra-identity-aware-proxy-apply infra-identity-aware-proxy-deploy infra-identity-aware-proxy-smoke infra-identity-aware-proxy-destroy
OUT
    ;;
  *)
    log_fatal "unsupported makefile module phony suffix: $module"
    ;;
  esac
}

makefile_module_target_block() {
  local module="$1"
  if ! is_module_enabled "$module"; then
    return 0
  fi

  case "$module" in
  observability)
    cat <<'OUT'

infra-observability-plan: ## Plan observability resources and OTEL runtime contract
	@scripts/bin/infra/observability_plan.sh

infra-observability-apply: ## Apply observability resources and OTEL collector stack
	@scripts/bin/infra/observability_apply.sh

infra-observability-deploy: ## Deploy observability runtime config through ArgoCD
	@scripts/bin/infra/observability_deploy.sh

infra-observability-smoke: ## Smoke observability and OTEL runtime contract
	@scripts/bin/infra/observability_smoke.sh

infra-observability-destroy: ## Destroy observability artifacts
	@scripts/bin/infra/observability_destroy.sh
OUT
    ;;
  workflows)
    cat <<'OUT'

infra-stackit-workflows-plan: ## Plan Workflows resources
	@scripts/bin/infra/stackit_workflows_plan.sh

infra-stackit-workflows-apply: ## Apply Workflows resources
	@scripts/bin/infra/stackit_workflows_apply.sh

infra-stackit-workflows-reconcile: ## Reconcile existing/desired Workflows state
	@scripts/bin/infra/stackit_workflows_reconcile.sh

infra-stackit-workflows-dag-deploy: ## Deploy DAGs to managed Airflow
	@scripts/bin/infra/stackit_workflows_dag_deploy.sh

infra-stackit-workflows-dag-parse-smoke: ## DAG import/parse smoke
	@scripts/bin/infra/stackit_workflows_dag_parse_smoke.sh

infra-stackit-workflows-smoke: ## Workflows runtime smoke
	@scripts/bin/infra/stackit_workflows_smoke.sh

infra-stackit-workflows-destroy: ## Destroy Workflows resources
	@scripts/bin/infra/stackit_workflows_destroy.sh
OUT
    ;;
  langfuse)
    cat <<'OUT'

infra-langfuse-plan: ## Plan Langfuse resources
	@scripts/bin/infra/langfuse_plan.sh

infra-langfuse-apply: ## Apply Langfuse resources
	@scripts/bin/infra/langfuse_apply.sh

infra-langfuse-deploy: ## Deploy Langfuse runtime
	@scripts/bin/infra/langfuse_deploy.sh

infra-langfuse-smoke: ## Langfuse smoke checks
	@scripts/bin/infra/langfuse_smoke.sh

infra-langfuse-destroy: ## Destroy Langfuse resources
	@scripts/bin/infra/langfuse_destroy.sh
OUT
    ;;
  postgres)
    cat <<'OUT'

infra-postgres-plan: ## Plan Postgres resources
	@scripts/bin/infra/postgres_plan.sh

infra-postgres-apply: ## Apply Postgres resources
	@scripts/bin/infra/postgres_apply.sh

infra-postgres-smoke: ## Postgres smoke checks
	@scripts/bin/infra/postgres_smoke.sh

infra-postgres-destroy: ## Destroy Postgres resources
	@scripts/bin/infra/postgres_destroy.sh
OUT
    ;;
  neo4j)
    cat <<'OUT'

infra-neo4j-plan: ## Plan Neo4j resources
	@scripts/bin/infra/neo4j_plan.sh

infra-neo4j-apply: ## Apply Neo4j resources
	@scripts/bin/infra/neo4j_apply.sh

infra-neo4j-deploy: ## Deploy Neo4j runtime
	@scripts/bin/infra/neo4j_deploy.sh

infra-neo4j-smoke: ## Neo4j smoke checks
	@scripts/bin/infra/neo4j_smoke.sh

infra-neo4j-destroy: ## Destroy Neo4j resources
	@scripts/bin/infra/neo4j_destroy.sh
OUT
    ;;
  object-storage)
    cat <<'OUT'

infra-object-storage-plan: ## Plan Object Storage resources
	@scripts/bin/infra/object_storage_plan.sh

infra-object-storage-apply: ## Apply Object Storage resources
	@scripts/bin/infra/object_storage_apply.sh

infra-object-storage-smoke: ## Object Storage smoke checks
	@scripts/bin/infra/object_storage_smoke.sh

infra-object-storage-destroy: ## Destroy Object Storage resources
	@scripts/bin/infra/object_storage_destroy.sh
OUT
    ;;
  rabbitmq)
    cat <<'OUT'

infra-rabbitmq-plan: ## Plan RabbitMQ resources
	@scripts/bin/infra/rabbitmq_plan.sh

infra-rabbitmq-apply: ## Apply RabbitMQ resources
	@scripts/bin/infra/rabbitmq_apply.sh

infra-rabbitmq-smoke: ## RabbitMQ smoke checks
	@scripts/bin/infra/rabbitmq_smoke.sh

infra-rabbitmq-destroy: ## Destroy RabbitMQ resources
	@scripts/bin/infra/rabbitmq_destroy.sh
OUT
    ;;
  dns)
    cat <<'OUT'

infra-dns-plan: ## Plan DNS resources
	@scripts/bin/infra/dns_plan.sh

infra-dns-apply: ## Apply DNS resources
	@scripts/bin/infra/dns_apply.sh

infra-dns-smoke: ## DNS smoke checks
	@scripts/bin/infra/dns_smoke.sh

infra-dns-destroy: ## Destroy DNS resources
	@scripts/bin/infra/dns_destroy.sh
OUT
    ;;
  public-endpoints)
    cat <<'OUT'

infra-public-endpoints-plan: ## Plan public endpoint resources
	@scripts/bin/infra/public_endpoints_plan.sh

infra-public-endpoints-apply: ## Apply public endpoint resources
	@scripts/bin/infra/public_endpoints_apply.sh

infra-public-endpoints-deploy: ## Deploy public endpoint runtime
	@scripts/bin/infra/public_endpoints_deploy.sh

infra-public-endpoints-smoke: ## Public endpoint smoke checks
	@scripts/bin/infra/public_endpoints_smoke.sh

infra-public-endpoints-destroy: ## Destroy public endpoint resources
	@scripts/bin/infra/public_endpoints_destroy.sh
OUT
    ;;
  secrets-manager)
    cat <<'OUT'

infra-secrets-manager-plan: ## Plan Secrets Manager resources
	@scripts/bin/infra/secrets_manager_plan.sh

infra-secrets-manager-apply: ## Apply Secrets Manager resources
	@scripts/bin/infra/secrets_manager_apply.sh

infra-secrets-manager-smoke: ## Secrets Manager smoke checks
	@scripts/bin/infra/secrets_manager_smoke.sh

infra-secrets-manager-destroy: ## Destroy Secrets Manager resources
	@scripts/bin/infra/secrets_manager_destroy.sh
OUT
    ;;
  kms)
    cat <<'OUT'

infra-kms-plan: ## Plan KMS resources
	@scripts/bin/infra/kms_plan.sh

infra-kms-apply: ## Apply KMS resources
	@scripts/bin/infra/kms_apply.sh

infra-kms-smoke: ## KMS smoke checks
	@scripts/bin/infra/kms_smoke.sh

infra-kms-destroy: ## Destroy KMS resources
	@scripts/bin/infra/kms_destroy.sh
OUT
    ;;
  identity-aware-proxy)
    cat <<'OUT'

infra-identity-aware-proxy-plan: ## Plan Identity-Aware Proxy resources (requires Keycloak OIDC config)
	@scripts/bin/infra/identity_aware_proxy_plan.sh

infra-identity-aware-proxy-apply: ## Apply Identity-Aware Proxy resources (requires Keycloak OIDC config)
	@scripts/bin/infra/identity_aware_proxy_apply.sh

infra-identity-aware-proxy-deploy: ## Deploy Identity-Aware Proxy runtime
	@scripts/bin/infra/identity_aware_proxy_deploy.sh

infra-identity-aware-proxy-smoke: ## Identity-Aware Proxy smoke checks (Keycloak OIDC contract)
	@scripts/bin/infra/identity_aware_proxy_smoke.sh

infra-identity-aware-proxy-destroy: ## Destroy Identity-Aware Proxy resources
	@scripts/bin/infra/identity_aware_proxy_destroy.sh
OUT
    ;;
  *)
    log_fatal "unsupported makefile module target block: $module"
    ;;
  esac
}

render_makefile() {
  local phony_observability phony_workflows phony_langfuse phony_postgres phony_neo4j
  local phony_object_storage phony_rabbitmq phony_dns phony_public_endpoints phony_secrets_manager phony_kms
  local phony_identity_aware_proxy
  phony_observability="$(makefile_module_phony_suffix observability)"
  phony_workflows="$(makefile_module_phony_suffix workflows)"
  phony_langfuse="$(makefile_module_phony_suffix langfuse)"
  phony_postgres="$(makefile_module_phony_suffix postgres)"
  phony_neo4j="$(makefile_module_phony_suffix neo4j)"
  phony_object_storage="$(makefile_module_phony_suffix object-storage)"
  phony_rabbitmq="$(makefile_module_phony_suffix rabbitmq)"
  phony_dns="$(makefile_module_phony_suffix dns)"
  phony_public_endpoints="$(makefile_module_phony_suffix public-endpoints)"
  phony_secrets_manager="$(makefile_module_phony_suffix secrets-manager)"
  phony_kms="$(makefile_module_phony_suffix kms)"
  phony_identity_aware_proxy="$(makefile_module_phony_suffix identity-aware-proxy)"

  local targets_observability targets_workflows targets_langfuse targets_postgres targets_neo4j
  local targets_object_storage targets_rabbitmq targets_dns targets_public_endpoints targets_secrets_manager
  local targets_kms targets_identity_aware_proxy
  targets_observability="$(makefile_module_target_block observability)"
  targets_workflows="$(makefile_module_target_block workflows)"
  targets_langfuse="$(makefile_module_target_block langfuse)"
  targets_postgres="$(makefile_module_target_block postgres)"
  targets_neo4j="$(makefile_module_target_block neo4j)"
  targets_object_storage="$(makefile_module_target_block object-storage)"
  targets_rabbitmq="$(makefile_module_target_block rabbitmq)"
  targets_dns="$(makefile_module_target_block dns)"
  targets_public_endpoints="$(makefile_module_target_block public-endpoints)"
  targets_secrets_manager="$(makefile_module_target_block secrets-manager)"
  targets_kms="$(makefile_module_target_block kms)"
  targets_identity_aware_proxy="$(makefile_module_target_block identity-aware-proxy)"

  local output_path="$ROOT_DIR/make/blueprint.generated.mk"
  ensure_dir "$(dirname "$output_path")"
  local rendered_tmp
  rendered_tmp="$(mktemp)"

  render_bootstrap_template_content \
    "blueprint" \
    "make/blueprint.generated.mk.tmpl" \
    "PHONY_OBSERVABILITY=$phony_observability" \
    "PHONY_WORKFLOWS=$phony_workflows" \
    "PHONY_LANGFUSE=$phony_langfuse" \
    "PHONY_POSTGRES=$phony_postgres" \
    "PHONY_NEO4J=$phony_neo4j" \
    "PHONY_OBJECT_STORAGE=$phony_object_storage" \
    "PHONY_RABBITMQ=$phony_rabbitmq" \
    "PHONY_DNS=$phony_dns" \
    "PHONY_PUBLIC_ENDPOINTS=$phony_public_endpoints" \
    "PHONY_SECRETS_MANAGER=$phony_secrets_manager" \
    "PHONY_KMS=$phony_kms" \
    "PHONY_IDENTITY_AWARE_PROXY=$phony_identity_aware_proxy" \
    "INFRA_ENV_GUARDED_OBSERVABILITY=$phony_observability" \
    "INFRA_ENV_GUARDED_WORKFLOWS=$phony_workflows" \
    "INFRA_ENV_GUARDED_LANGFUSE=$phony_langfuse" \
    "INFRA_ENV_GUARDED_POSTGRES=$phony_postgres" \
    "INFRA_ENV_GUARDED_NEO4J=$phony_neo4j" \
    "INFRA_ENV_GUARDED_OBJECT_STORAGE=$phony_object_storage" \
    "INFRA_ENV_GUARDED_RABBITMQ=$phony_rabbitmq" \
    "INFRA_ENV_GUARDED_DNS=$phony_dns" \
    "INFRA_ENV_GUARDED_PUBLIC_ENDPOINTS=$phony_public_endpoints" \
    "INFRA_ENV_GUARDED_SECRETS_MANAGER=$phony_secrets_manager" \
    "INFRA_ENV_GUARDED_KMS=$phony_kms" \
    "INFRA_ENV_GUARDED_IDENTITY_AWARE_PROXY=$phony_identity_aware_proxy" \
    "TARGETS_OBSERVABILITY=$targets_observability" \
    "TARGETS_WORKFLOWS=$targets_workflows" \
    "TARGETS_LANGFUSE=$targets_langfuse" \
    "TARGETS_POSTGRES=$targets_postgres" \
    "TARGETS_NEO4J=$targets_neo4j" \
    "TARGETS_OBJECT_STORAGE=$targets_object_storage" \
    "TARGETS_RABBITMQ=$targets_rabbitmq" \
    "TARGETS_DNS=$targets_dns" \
    "TARGETS_PUBLIC_ENDPOINTS=$targets_public_endpoints" \
    "TARGETS_SECRETS_MANAGER=$targets_secrets_manager" \
    "TARGETS_KMS=$targets_kms" \
    "TARGETS_IDENTITY_AWARE_PROXY=$targets_identity_aware_proxy" \
    >"$rendered_tmp"

  # Normalize generated output to end with exactly one newline and no trailing blank lines.
  local rendered_content
  rendered_content="$(cat "$rendered_tmp")"
  printf '%s\n' "$rendered_content" >"$rendered_tmp"

  if [[ ! -f "$output_path" ]] || ! cmp -s "$output_path" "$rendered_tmp"; then
    mv "$rendered_tmp" "$output_path"
    log_info "updated make/blueprint.generated.mk from template based on enabled modules"
  else
    rm -f "$rendered_tmp"
    log_info "make/blueprint.generated.mk already up to date for enabled module set"
  fi
}

optional_target_count() {
  local count=0
  if is_module_enabled observability; then
    count=$((count + 5))
  fi
  if is_module_enabled workflows; then
    count=$((count + 7))
  fi
  if is_module_enabled langfuse; then
    count=$((count + 5))
  fi
  if is_module_enabled postgres; then
    count=$((count + 4))
  fi
  if is_module_enabled neo4j; then
    count=$((count + 5))
  fi
  if is_module_enabled object-storage; then
    count=$((count + 4))
  fi
  if is_module_enabled rabbitmq; then
    count=$((count + 4))
  fi
  if is_module_enabled dns; then
    count=$((count + 4))
  fi
  if is_module_enabled public-endpoints; then
    count=$((count + 5))
  fi
  if is_module_enabled secrets-manager; then
    count=$((count + 4))
  fi
  if is_module_enabled kms; then
    count=$((count + 4))
  fi
  if is_module_enabled identity-aware-proxy; then
    count=$((count + 5))
  fi
  echo "$count"
}

render_makefile

module_target_count="$(optional_target_count)"
log_metric "optional_module_make_target_count" "$module_target_count"
if [[ "$module_target_count" -gt 0 ]]; then
  log_info "makefile optional module targets materialized for: $(enabled_modules_csv)"
else
  log_info "makefile optional module targets pruned; no optional modules enabled"
fi
