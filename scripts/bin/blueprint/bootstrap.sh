#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"

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

bootstrap_blueprint_directories() {
  ensure_dir "$ROOT_DIR/blueprint"
  ensure_dir "$ROOT_DIR/docs"
  ensure_dir "$ROOT_DIR/docs/blueprint/architecture"
  ensure_dir "$ROOT_DIR/docs/blueprint/governance"
  ensure_dir "$ROOT_DIR/docs/platform/consumer"
  ensure_dir "$ROOT_DIR/docs/platform/modules"
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
    "blueprint/repo.init.example.env"
    "docs/README.md"
    "docs/blueprint/README.md"
    "docs/blueprint/architecture/system_overview.md"
    "docs/blueprint/architecture/execution_model.md"
    "docs/blueprint/governance/template_release_policy.md"
    "docs/blueprint/governance/ownership_matrix.md"
    "docs/platform/README.md"
    "docs/platform/consumer/first_30_minutes.md"
    "docs/platform/consumer/quickstart.md"
    "docs/platform/consumer/troubleshooting.md"
    "docs/platform/consumer/upgrade_runbook.md"
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
    ensure_file_from_template "$ROOT_DIR/$rel" "blueprint" "$rel"
  done

  log_metric "blueprint_template_file_count" "${#template_files[@]}"
  log_info "blueprint static templates ensured"
}

bootstrap_blueprint_directories
bootstrap_blueprint_templates
run_cmd "$ROOT_DIR/scripts/bin/blueprint/render_module_wrapper_skeletons.sh"
run_cmd "$ROOT_DIR/scripts/bin/blueprint/render_makefile.sh"

if command -v pre-commit >/dev/null 2>&1; then
  run_cmd pre-commit install --install-hooks --hook-type pre-commit --hook-type pre-push
else
  log_warn "pre-commit not installed; skipping hook installation"
fi

log_info "blueprint bootstrap complete"
