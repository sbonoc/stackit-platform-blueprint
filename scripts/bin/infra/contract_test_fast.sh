#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "infra_contract_test_fast"

usage() {
  cat <<'EOF'
Usage: contract_test_fast.sh

Runs fast infra contract helper CLI/unit tests:
- runtime identity contract helper CLI
- ArgoCD repo contract helper CLI
- state artifact env/json contract renderer + schema validation
- shell root-resolution helper + prelude drift assertions
- generated-consumer upgrade fixture matrix safety coverage
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command pytest
run_cmd pytest -q \
  "$ROOT_DIR/tests/blueprint/test_upgrade_fixture_matrix.py" \
  "$ROOT_DIR/tests/infra/test_runtime_identity_contract_cli.py" \
  "$ROOT_DIR/tests/infra/test_argocd_repo_contract_cli.py" \
  "$ROOT_DIR/tests/infra/test_state_artifact_contract.py" \
  "$ROOT_DIR/tests/infra/test_root_dir_resolution.py"
