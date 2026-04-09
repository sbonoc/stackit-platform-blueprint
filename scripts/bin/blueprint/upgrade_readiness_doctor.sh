#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_upgrade_readiness_doctor"

usage() {
  cat <<'EOF'
Usage: upgrade_readiness_doctor.sh

Generates upgrade readiness diagnostics for generated-consumer upgrade flows:
- required upgrade target availability,
- runtime dependency edge integrity,
- latest preflight/apply artifact presence and manual-action hints,
- consumer-owned apps-ci-bootstrap placeholder detection.

Environment variables:
  BLUEPRINT_UPGRADE_READINESS_REPORT_PATH   Output report path (default: artifacts/blueprint/upgrade_readiness_doctor.json)
  BLUEPRINT_UPGRADE_READINESS_STRICT        true|false strict mode (default: false)
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env BLUEPRINT_UPGRADE_READINESS_REPORT_PATH "$ROOT_DIR/artifacts/blueprint/upgrade_readiness_doctor.json"
set_default_env BLUEPRINT_UPGRADE_READINESS_STRICT "false"

strict_flag=""
if [[ "$(shell_normalize_bool_truefalse "$BLUEPRINT_UPGRADE_READINESS_STRICT")" == "true" ]]; then
  strict_flag="--strict"
fi

run_cmd python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_readiness_doctor.py" \
  --repo-root "$ROOT_DIR" \
  --output "$BLUEPRINT_UPGRADE_READINESS_REPORT_PATH" \
  $strict_flag

log_info "upgrade readiness diagnostics written to $BLUEPRINT_UPGRADE_READINESS_REPORT_PATH"
