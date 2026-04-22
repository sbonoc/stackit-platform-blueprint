#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "infra_contract_test_fast"

usage() {
  cat <<'EOF'
Usage: contract_test_fast.sh

Runs fast infra contract helper CLI/unit tests:
- runtime identity contract helper CLI
- ArgoCD repo contract helper CLI
- state artifact env/json contract renderer + schema validation
- shell root-resolution helper + prelude drift assertions
- optional-module fixture required_env parity
- generated-consumer upgrade fixture matrix safety coverage (template-source only)
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command pytest

repo_mode="$(blueprint_repo_mode)"
template_source_mode="$(blueprint_repo_mode_from)"
generated_consumer_mode="$(blueprint_repo_mode_to)"

base_tests=(
  "tests/infra/test_runtime_identity_contract_cli.py"
  "tests/infra/test_argocd_repo_contract_cli.py"
  "tests/infra/test_state_artifact_contract.py"
  "tests/infra/test_root_dir_resolution.py"
  "tests/infra/test_optional_module_required_env_contract.py"
  "tests/infra/test_tooling_contracts.py"
)
template_source_only_tests=(
  "tests/blueprint/test_upgrade_fixture_matrix.py"
)

selected_tests=("${base_tests[@]}")
if [[ "$repo_mode" == "$template_source_mode" ]]; then
  selected_tests+=("${template_source_only_tests[@]}")
elif [[ "$repo_mode" == "$generated_consumer_mode" ]]; then
  log_info "repo_mode=$repo_mode; skipping template-source-only fast contract tests"
  log_metric \
    "infra_contract_test_fast_test_selection_total" \
    "${#template_source_only_tests[@]}" \
    "repo_mode=$repo_mode selection=skipped_template_source_only"
else
  log_fatal "unsupported repo_mode for fast contract test selection: $repo_mode"
fi

pytest_args=()
missing_tests=()
for relative_test_path in "${selected_tests[@]}"; do
  absolute_test_path="$ROOT_DIR/$relative_test_path"
  if [[ ! -f "$absolute_test_path" ]]; then
    missing_tests+=("$relative_test_path")
    continue
  fi
  pytest_args+=("$absolute_test_path")
done

if (( ${#missing_tests[@]} > 0 )); then
  log_fatal \
    "missing required fast contract test path(s) for repo_mode=$repo_mode: ${missing_tests[*]}"
fi

log_metric \
  "infra_contract_test_fast_test_selection_total" \
  "${#pytest_args[@]}" \
  "repo_mode=$repo_mode selection=selected"

run_cmd pytest -q "${pytest_args[@]}"
