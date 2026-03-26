#!/usr/bin/env bash
set -euo pipefail

module_action_scripts() {
  local module="$1"
  local action="$2"
  case "${module}:${action}" in
  observability:plan)
    echo "$ROOT_DIR/scripts/bin/infra/observability_plan.sh"
    ;;
  observability:apply)
    echo "$ROOT_DIR/scripts/bin/infra/observability_apply.sh"
    ;;
  observability:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/observability_deploy.sh"
    ;;
  observability:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/observability_smoke.sh"
    ;;
  observability:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/observability_destroy.sh"
    ;;
  workflows:plan)
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_plan.sh"
    ;;
  workflows:apply)
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_apply.sh"
    ;;
  workflows:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_reconcile.sh"
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_dag_deploy.sh"
    ;;
  workflows:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_smoke.sh"
    ;;
  workflows:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/stackit_workflows_destroy.sh"
    ;;
  langfuse:plan)
    echo "$ROOT_DIR/scripts/bin/infra/langfuse_plan.sh"
    ;;
  langfuse:apply)
    echo "$ROOT_DIR/scripts/bin/infra/langfuse_apply.sh"
    ;;
  langfuse:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/langfuse_deploy.sh"
    ;;
  langfuse:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/langfuse_smoke.sh"
    ;;
  langfuse:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/langfuse_destroy.sh"
    ;;
  postgres:plan)
    echo "$ROOT_DIR/scripts/bin/infra/postgres_plan.sh"
    ;;
  postgres:apply)
    echo "$ROOT_DIR/scripts/bin/infra/postgres_apply.sh"
    ;;
  postgres:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/postgres_smoke.sh"
    ;;
  postgres:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/postgres_destroy.sh"
    ;;
  neo4j:plan)
    echo "$ROOT_DIR/scripts/bin/infra/neo4j_plan.sh"
    ;;
  neo4j:apply)
    echo "$ROOT_DIR/scripts/bin/infra/neo4j_apply.sh"
    ;;
  neo4j:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/neo4j_deploy.sh"
    ;;
  neo4j:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/neo4j_smoke.sh"
    ;;
  neo4j:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/neo4j_destroy.sh"
    ;;
  *)
    ;;
  esac
}

run_enabled_modules_action() {
  local action="$1"
  shift || true

  local modules=("$@")
  if [[ "${#modules[@]}" -eq 0 ]]; then
    modules=(observability workflows langfuse postgres neo4j)
  fi

  local enabled_modules_count=0
  local executed_scripts_count=0
  local module
  local module_script
  local had_script
  for module in "${modules[@]}"; do
    if ! is_module_enabled "${module}"; then
      continue
    fi

    enabled_modules_count=$((enabled_modules_count + 1))
    had_script="false"
    while IFS= read -r module_script; do
      [[ -n "${module_script}" ]] || continue
      had_script="true"
      if [[ ! -x "${module_script}" ]]; then
        log_fatal "module action script not executable: ${module_script}"
      fi
      run_cmd "${module_script}"
      executed_scripts_count=$((executed_scripts_count + 1))
    done < <(module_action_scripts "${module}" "${action}")

    if [[ "${had_script}" != "true" ]]; then
      log_info "no ${action} action script for module=${module}; skipping"
    fi
  done

  log_metric "module_action_enabled_count" "$enabled_modules_count" "action=$action"
  log_metric "module_action_script_count" "$executed_scripts_count" "action=$action"
}
