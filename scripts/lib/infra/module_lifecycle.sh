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
  object-storage:plan)
    echo "$ROOT_DIR/scripts/bin/infra/object_storage_plan.sh"
    ;;
  object-storage:apply)
    echo "$ROOT_DIR/scripts/bin/infra/object_storage_apply.sh"
    ;;
  object-storage:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/object_storage_smoke.sh"
    ;;
  object-storage:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/object_storage_destroy.sh"
    ;;
  rabbitmq:plan)
    echo "$ROOT_DIR/scripts/bin/infra/rabbitmq_plan.sh"
    ;;
  rabbitmq:apply)
    echo "$ROOT_DIR/scripts/bin/infra/rabbitmq_apply.sh"
    ;;
  rabbitmq:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/rabbitmq_smoke.sh"
    ;;
  rabbitmq:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/rabbitmq_destroy.sh"
    ;;
  opensearch:plan)
    echo "$ROOT_DIR/scripts/bin/infra/opensearch_plan.sh"
    ;;
  opensearch:apply)
    echo "$ROOT_DIR/scripts/bin/infra/opensearch_apply.sh"
    ;;
  opensearch:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/opensearch_smoke.sh"
    ;;
  opensearch:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/opensearch_destroy.sh"
    ;;
  dns:plan)
    echo "$ROOT_DIR/scripts/bin/infra/dns_plan.sh"
    ;;
  dns:apply)
    echo "$ROOT_DIR/scripts/bin/infra/dns_apply.sh"
    ;;
  dns:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/dns_smoke.sh"
    ;;
  dns:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/dns_destroy.sh"
    ;;
  public-endpoints:plan)
    echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_plan.sh"
    ;;
  public-endpoints:apply)
    echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_apply.sh"
    ;;
  public-endpoints:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_deploy.sh"
    ;;
  public-endpoints:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_smoke.sh"
    ;;
  public-endpoints:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_destroy.sh"
    ;;
  secrets-manager:plan)
    echo "$ROOT_DIR/scripts/bin/infra/secrets_manager_plan.sh"
    ;;
  secrets-manager:apply)
    echo "$ROOT_DIR/scripts/bin/infra/secrets_manager_apply.sh"
    ;;
  secrets-manager:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/secrets_manager_smoke.sh"
    ;;
  secrets-manager:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/secrets_manager_destroy.sh"
    ;;
  kms:plan)
    echo "$ROOT_DIR/scripts/bin/infra/kms_plan.sh"
    ;;
  kms:apply)
    echo "$ROOT_DIR/scripts/bin/infra/kms_apply.sh"
    ;;
  kms:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/kms_smoke.sh"
    ;;
  kms:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/kms_destroy.sh"
    ;;
  identity-aware-proxy:plan)
    echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_plan.sh"
    ;;
  identity-aware-proxy:apply)
    echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_apply.sh"
    ;;
  identity-aware-proxy:deploy)
    echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_deploy.sh"
    ;;
  identity-aware-proxy:smoke)
    echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_smoke.sh"
    ;;
  identity-aware-proxy:destroy)
    echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_destroy.sh"
    ;;
  *)
    ;;
  esac
}

default_optional_modules() {
  cat <<'OUT'
observability
workflows
langfuse
postgres
neo4j
object-storage
rabbitmq
opensearch
dns
public-endpoints
secrets-manager
kms
identity-aware-proxy
OUT
}

run_enabled_modules_action() {
  local action="$1"
  shift || true

  local modules=("$@")
  if [[ "${#modules[@]}" -eq 0 ]]; then
    mapfile -t modules < <(default_optional_modules)
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

run_disabled_modules_action() {
  local action="$1"
  shift || true

  local modules=("$@")
  if [[ "${#modules[@]}" -eq 0 ]]; then
    mapfile -t modules < <(default_optional_modules)
  fi

  local disabled_modules_count=0
  local executed_scripts_count=0
  local module
  local module_script
  local had_script
  for module in "${modules[@]}"; do
    if is_module_enabled "${module}"; then
      continue
    fi

    disabled_modules_count=$((disabled_modules_count + 1))
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
      log_info "no ${action} action script for disabled module=${module}; skipping"
    fi
  done

  log_metric "module_action_disabled_count" "$disabled_modules_count" "action=$action"
  log_metric "module_action_disabled_script_count" "$executed_scripts_count" "action=$action"
}

run_all_modules_action() {
  local action="$1"
  shift || true

  local modules=("$@")
  if [[ "${#modules[@]}" -eq 0 ]]; then
    mapfile -t modules < <(default_optional_modules)
  fi

  local selected_modules_count=0
  local executed_scripts_count=0
  local module
  local module_script
  local had_script
  for module in "${modules[@]}"; do
    selected_modules_count=$((selected_modules_count + 1))
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

  log_metric "module_action_all_count" "$selected_modules_count" "action=$action"
  log_metric "module_action_all_script_count" "$executed_scripts_count" "action=$action"
}
