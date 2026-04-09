#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"

start_script_metric_trap "infra_stackit_workflows_dag_parse_smoke"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows DAG parse smoke"
  exit 0
fi

workflows_init_env
if [[ -d "$ROOT_DIR/apps" ]]; then
  violations="$(find "$ROOT_DIR/apps" -type f -name '*dag*.py' | wc -l | tr -d ' ')"
else
  violations="0"
fi
if [[ "$violations" != "0" ]]; then
  log_fatal "found DAG entrypoints under apps/**; DAG entrypoints must live in repository-root dags/"
fi

state_file="$(write_state_file "workflows_dag_parse_smoke" \
  "status=passed" \
  "violations=$violations" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows DAG parse smoke state written to $state_file"
