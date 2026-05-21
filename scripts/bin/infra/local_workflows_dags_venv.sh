#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"

start_script_metric_trap "infra_local_workflows_dags_venv"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows dags-venv"
  exit 0
fi

require_command uv

venv_path="$ROOT_DIR/.venv-dags"
log_info "creating DAG development venv at $venv_path (Python 3.12)"
uv venv --python 3.12 "$venv_path"
log_info "DAG development venv ready: $venv_path"
log_info "run: uv pip install --python $venv_path/bin/python apache-airflow==3.1.8"
