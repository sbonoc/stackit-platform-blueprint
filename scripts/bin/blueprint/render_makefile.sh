#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
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
  *)
    log_fatal "unsupported makefile module target block: $module"
    ;;
  esac
}

render_makefile() {
  local phony_observability phony_workflows phony_langfuse phony_postgres phony_neo4j
  phony_observability="$(makefile_module_phony_suffix observability)"
  phony_workflows="$(makefile_module_phony_suffix workflows)"
  phony_langfuse="$(makefile_module_phony_suffix langfuse)"
  phony_postgres="$(makefile_module_phony_suffix postgres)"
  phony_neo4j="$(makefile_module_phony_suffix neo4j)"

  local targets_observability targets_workflows targets_langfuse targets_postgres targets_neo4j
  targets_observability="$(makefile_module_target_block observability)"
  targets_workflows="$(makefile_module_target_block workflows)"
  targets_langfuse="$(makefile_module_target_block langfuse)"
  targets_postgres="$(makefile_module_target_block postgres)"
  targets_neo4j="$(makefile_module_target_block neo4j)"

  local rendered_makefile
  rendered_makefile="$({
    render_bootstrap_template_content \
      "blueprint" \
      "make/blueprint.generated.mk.tmpl" \
      "PHONY_OBSERVABILITY=$phony_observability" \
      "PHONY_WORKFLOWS=$phony_workflows" \
      "PHONY_LANGFUSE=$phony_langfuse" \
      "PHONY_POSTGRES=$phony_postgres" \
      "PHONY_NEO4J=$phony_neo4j" \
      "TARGETS_OBSERVABILITY=$targets_observability" \
      "TARGETS_WORKFLOWS=$targets_workflows" \
      "TARGETS_LANGFUSE=$targets_langfuse" \
      "TARGETS_POSTGRES=$targets_postgres" \
      "TARGETS_NEO4J=$targets_neo4j"
  })"

  local output_path="$ROOT_DIR/make/blueprint.generated.mk"
  ensure_dir "$(dirname "$output_path")"

  local current_makefile=""
  if [[ -f "$output_path" ]]; then
    current_makefile="$(cat "$output_path")"
  fi

  if [[ "$current_makefile" != "$rendered_makefile" ]]; then
    printf '%s' "$rendered_makefile" >"$output_path"
    log_info "updated make/blueprint.generated.mk from template based on enabled modules"
  else
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
