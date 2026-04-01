#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_bootstrap"

usage() {
  cat <<'USAGE'
Usage: bootstrap.sh

Bootstraps blueprint-scoped repository assets:
- baseline template/hygiene files,
- blueprint docs templates,
- platform docs baseline (seeded only when missing),
- optional-module wrapper skeleton templates rendered from module contracts,
- blueprint makefile rendering from template with conditional module targets,
- local pre-commit and pre-push hook installation.

In generated repos, consumer-seeded init files are not recreated here.
Restore them intentionally with make blueprint-resync-consumer-seeds
(or force init when full re-seed is intentional).
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

blueprint_bootstrap_seeded_skip_count=0

ensure_blueprint_seed_file() {
  local relative_path="$1"
  if blueprint_repo_is_generated_consumer && blueprint_path_is_consumer_seeded "$relative_path"; then
    if [[ ! -f "$ROOT_DIR/$relative_path" ]]; then
      log_fatal "missing consumer-initialized file: $relative_path; run make blueprint-resync-consumer-seeds first (or $(blueprint_init_force_env_var)=true make blueprint-init-repo for full re-seed)"
    fi
    blueprint_bootstrap_seeded_skip_count=$((blueprint_bootstrap_seeded_skip_count + 1))
    return 0
  fi

  ensure_file_from_template "$ROOT_DIR/$relative_path" "blueprint" "$relative_path"
}

bootstrap_blueprint_directories() {
  ensure_dir "$ROOT_DIR/blueprint"
  ensure_dir "$ROOT_DIR/docs"
  ensure_dir "$ROOT_DIR/docs/blueprint/architecture"
  ensure_dir "$ROOT_DIR/docs/blueprint/governance"
  ensure_dir "$ROOT_DIR/docs/platform/consumer"
  ensure_dir "$ROOT_DIR/docs/platform/modules"
  ensure_dir "$ROOT_DIR/docs/reference/generated"
  ensure_dir "$ROOT_DIR/make/platform"
}

bootstrap_blueprint_templates() {
  # All files below are create-if-missing seeds from the bootstrap template root.
  # docs/platform/** remain consumer-editable after first materialization.
  local template_files=(
    ".editorconfig"
    ".gitignore"
    ".dockerignore"
    ".pre-commit-config.yaml"
    "Makefile"
    "make/platform.mk"
    "make/platform/.gitkeep"
    "blueprint/repo.init.env"
    "blueprint/repo.init.secrets.example.env"
    "blueprint/runtime_identity_contract.yaml"
    "contracts/async/pact/messages/producer/.gitkeep"
    "contracts/async/pact/messages/producer/README.md"
    "contracts/async/pact/messages/consumer/.gitkeep"
    "contracts/async/pact/messages/consumer/README.md"
    "docs/README.md"
    "docs/blueprint/README.md"
    "docs/blueprint/architecture/system_overview.md"
    "docs/blueprint/architecture/execution_model.md"
    "docs/blueprint/contracts/async_message_contracts.md"
    "docs/blueprint/governance/ownership_matrix.md"
    "docs/platform/README.md"
    "docs/platform/consumer/first_30_minutes.md"
    "docs/platform/consumer/quickstart.md"
    "docs/platform/consumer/endpoint_exposure_model.md"
    "docs/platform/consumer/protected_api_routes.md"
    "docs/platform/consumer/event_messaging_baseline.md"
    "docs/platform/consumer/zero_downtime_evolution.md"
    "docs/platform/consumer/tenant_context_propagation.md"
    "docs/platform/consumer/runtime_credentials_eso.md"
    "docs/platform/consumer/troubleshooting.md"
    "docs/platform/modules/observability/README.md"
    "docs/platform/modules/workflows/README.md"
    "docs/platform/modules/langfuse/README.md"
    "docs/platform/modules/postgres/README.md"
    "docs/platform/modules/neo4j/README.md"
    "docs/platform/modules/object-storage/README.md"
    "docs/platform/modules/rabbitmq/README.md"
    "docs/platform/modules/dns/README.md"
    "docs/platform/modules/public-endpoints/README.md"
    "docs/platform/modules/secrets-manager/README.md"
    "docs/platform/modules/kms/README.md"
    "docs/platform/modules/identity-aware-proxy/README.md"
  )

  local rel
  for rel in "${template_files[@]}"; do
    ensure_blueprint_seed_file "$rel"
  done

  log_metric "blueprint_template_file_count" "${#template_files[@]}"
  log_metric "blueprint_consumer_seeded_skip_count" "$blueprint_bootstrap_seeded_skip_count"
  log_info "blueprint static templates ensured"
}

bootstrap_blueprint_directories
bootstrap_blueprint_templates
run_cmd "$ROOT_DIR/scripts/bin/blueprint/render_module_wrapper_skeletons.sh"
run_cmd "$ROOT_DIR/scripts/bin/blueprint/render_makefile.sh"

# `.github/workflows/ci.yml` is consumer-seeded in generated repos and must
# remain consumer-owned after init. Only render the source blueprint workflow
# in template-source mode.
if blueprint_repo_is_generated_consumer; then
  log_metric "blueprint_ci_workflow_sync_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping source CI workflow render in generated-consumer repo"
else
  run_cmd python3 "$ROOT_DIR/scripts/lib/quality/render_ci_workflow.py" \
    --output "$ROOT_DIR/.github/workflows/ci.yml"
  log_metric "blueprint_ci_workflow_sync_total" "1" "status=success repo_mode=template-source"
fi

run_cmd python3 "$ROOT_DIR/scripts/bin/quality/render_core_targets_doc.py" \
  --output "$ROOT_DIR/docs/reference/generated/core_targets.generated.md"
run_cmd python3 "$ROOT_DIR/scripts/lib/docs/generate_contract_docs.py" \
  --contract "$ROOT_DIR/blueprint/contract.yaml" \
  --modules-dir "$ROOT_DIR/blueprint/modules" \
  --output "$ROOT_DIR/docs/reference/generated/contract_metadata.generated.md"
run_cmd python3 "$ROOT_DIR/scripts/lib/docs/sync_platform_seed_docs.py"
run_cmd python3 "$ROOT_DIR/scripts/lib/docs/sync_runtime_identity_contract_summary.py"

if command -v pre-commit >/dev/null 2>&1; then
  run_cmd pre-commit install --install-hooks --hook-type pre-commit --hook-type pre-push
else
  log_warn "pre-commit not installed; skipping hook installation"
fi

log_info "blueprint bootstrap complete"
