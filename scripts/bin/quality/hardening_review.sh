#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "quality_hardening_review"

usage() {
  cat <<'EOF'
Usage: hardening_review.sh

Validates SDD Publish-phase hardening assets:
- specs/<work-item>/hardening_review.md sections
- specs/<work-item>/pr_context.md sections
- PR template heading contract for source + consumer template surfaces
- blueprint-defect escalation section fields in spec.md
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "quality hardening-review gate start"
if blueprint_repo_is_generated_consumer; then
  log_info "running in generated-consumer mode; validating local SDD assets only"
fi

run_cmd python3 "$ROOT_DIR/scripts/bin/quality/check_sdd_assets.py"
log_metric "quality_hardening_review_total" "1" "status=success"
log_info "quality hardening-review gate completed"
