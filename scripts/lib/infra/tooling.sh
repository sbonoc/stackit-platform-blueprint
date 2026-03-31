#!/usr/bin/env bash
set -euo pipefail

TOOLING_ENV_DEFAULTS_LOADED="${TOOLING_ENV_DEFAULTS_LOADED:-false}"
HELM_PREPARED_REPOS_CACHE="${HELM_PREPARED_REPOS_CACHE:-|}"

tooling_load_blueprint_env_defaults() {
  if [[ "$TOOLING_ENV_DEFAULTS_LOADED" == "true" ]]; then
    return 0
  fi
  TOOLING_ENV_DEFAULTS_LOADED="true"

  local contract_runtime="$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
  if [[ ! -f "$contract_runtime" ]]; then
    return 0
  fi

  # shellcheck disable=SC1090
  source "$contract_runtime"
  local defaults_env_file secrets_env_file
  defaults_env_file="$(blueprint_defaults_env_file)"
  secrets_env_file="$(blueprint_secrets_env_file)"
  local defaults_present="0"
  local secrets_present="0"
  [[ -f "$defaults_env_file" ]] && defaults_present="1"
  [[ -f "$secrets_env_file" ]] && secrets_present="1"

  blueprint_load_env_defaults
  log_metric \
    "blueprint_env_defaults_load_total" \
    "1" \
    "repo_mode=$(blueprint_repo_mode) defaults_present=$defaults_present secrets_present=$secrets_present" >&2
  if blueprint_repo_is_generated_consumer; then
    blueprint_require_runtime_env
  fi
}

tooling_load_blueprint_env_defaults

tooling_normalize_bool() {
  local value="${1:-false}"
  case "$value" in
  1 | true | TRUE | True | yes | YES | on | ON)
    echo "true"
    ;;
  *)
    echo "false"
    ;;
  esac
}

tooling_execution_mode() {
  if [[ "$(tooling_normalize_bool "${DRY_RUN:-true}")" == "true" ]]; then
    echo "dry-run"
    return 0
  fi
  echo "execute"
}

tooling_is_execution_enabled() {
  [[ "$(tooling_execution_mode)" == "execute" ]]
}

tooling_is_local_profile() {
  [[ "${BLUEPRINT_PROFILE:-local-full}" == local-* ]]
}

tooling_is_stackit_profile() {
  [[ "${BLUEPRINT_PROFILE:-local-full}" == stackit-* ]]
}

kubectl_contexts_list() {
  if ! command -v kubectl >/dev/null 2>&1; then
    return 0
  fi
  kubectl config get-contexts -o name 2>/dev/null || true
}

kubectl_current_context_name() {
  if ! command -v kubectl >/dev/null 2>&1; then
    return 0
  fi
  kubectl config current-context 2>/dev/null || true
}

kubectl_context_exists() {
  local context_name="$1"
  kubectl_contexts_list | grep -Fxq "$context_name"
}

stackit_kubeconfig_path() {
  set_default_env STACKIT_FOUNDATION_KUBECONFIG_OUTPUT "${HOME}/.kube/stackit-${BLUEPRINT_PROFILE}.yaml"
  local kubeconfig_path="$STACKIT_FOUNDATION_KUBECONFIG_OUTPUT"
  if [[ "$kubeconfig_path" != /* ]]; then
    kubeconfig_path="$ROOT_DIR/$kubeconfig_path"
  fi
  printf '%s\n' "$kubeconfig_path"
}

local_kubeconfig_artifact_path() {
  printf '%s/artifacts/infra/local_kubeconfig.yaml' "$ROOT_DIR"
}

resolve_local_kube_context() {
  # Local workstation runs should favor the user's Docker Desktop cluster when
  # available, while CI stays on ephemeral kind contexts for isolation.
  if [[ -n "${LOCAL_KUBE_CONTEXT:-}" ]]; then
    printf '%s\n' "$LOCAL_KUBE_CONTEXT"
    return 0
  fi

  local current_context
  current_context="$(kubectl_current_context_name)"

  if [[ "$(tooling_normalize_bool "${CI:-false}")" == "true" ]]; then
    if [[ "$current_context" =~ ^kind- ]]; then
      printf '%s\n' "$current_context"
      return 0
    fi

    if kubectl_context_exists "kind-blueprint-e2e"; then
      printf 'kind-blueprint-e2e\n'
      return 0
    fi

    local first_kind_context
    first_kind_context="$(kubectl_contexts_list | grep '^kind-' | head -n 1 || true)"
    if [[ -n "$first_kind_context" ]]; then
      printf '%s\n' "$first_kind_context"
      return 0
    fi
  fi

  if kubectl_context_exists "docker-desktop"; then
    printf 'docker-desktop\n'
    return 0
  fi

  if [[ -n "$current_context" ]]; then
    printf '%s\n' "$current_context"
    return 0
  fi

  local first_context
  first_context="$(kubectl_contexts_list | head -n 1 || true)"
  printf '%s\n' "$first_context"
}

resolve_local_kube_context_source() {
  if [[ -n "${LOCAL_KUBE_CONTEXT:-}" ]]; then
    printf 'env\n'
    return 0
  fi

  local current_context
  current_context="$(kubectl_current_context_name)"

  if [[ "$(tooling_normalize_bool "${CI:-false}")" == "true" ]]; then
    if [[ "$current_context" =~ ^kind- ]]; then
      printf 'ci-current-context\n'
      return 0
    fi
    if kubectl_context_exists "kind-blueprint-e2e"; then
      printf 'ci-kind-blueprint-e2e\n'
      return 0
    fi
    if kubectl_contexts_list | grep -q '^kind-'; then
      printf 'ci-first-kind-context\n'
      return 0
    fi
  fi

  if kubectl_context_exists "docker-desktop"; then
    printf 'docker-desktop-preferred\n'
    return 0
  fi

  if [[ -n "$current_context" ]]; then
    printf 'current-context\n'
    return 0
  fi

  printf 'first-context\n'
}

prepare_cluster_access() {
  if ! tooling_is_execution_enabled; then
    return 0
  fi

  if [[ -n "${BLUEPRINT_ACTIVE_KUBECONFIG:-}" && -f "${BLUEPRINT_ACTIVE_KUBECONFIG:-}" && -n "${BLUEPRINT_ACTIVE_KUBE_CONTEXT:-}" ]]; then
    export KUBECONFIG="$BLUEPRINT_ACTIVE_KUBECONFIG"
    return 0
  fi

  require_command kubectl

  local kubeconfig_path context_name context_source
  if tooling_is_stackit_profile; then
    kubeconfig_path="$(stackit_kubeconfig_path)"
    context_source="stackit-kubeconfig"
    if [[ ! -f "$kubeconfig_path" ]]; then
      log_fatal "missing STACKIT kubeconfig: $kubeconfig_path"
    fi
    export KUBECONFIG="$kubeconfig_path"
    context_name="$(kubectl config current-context 2>/dev/null || true)"
  elif tooling_is_local_profile; then
    context_name="$(resolve_local_kube_context)"
    context_source="$(resolve_local_kube_context_source)"
    if [[ -z "$context_name" ]]; then
      log_fatal "unable to resolve a local kubectl context; set LOCAL_KUBE_CONTEXT explicitly"
    fi
    kubeconfig_path="$(local_kubeconfig_artifact_path)"
    ensure_dir "$(dirname "$kubeconfig_path")"
    if ! kubectl --context="$context_name" config view --raw --minify --flatten >"$kubeconfig_path"; then
      log_fatal "failed to materialize kubeconfig for local context=$context_name"
    fi
    chmod 600 "$kubeconfig_path"
    export KUBECONFIG="$kubeconfig_path"
  else
    return 0
  fi

  export BLUEPRINT_ACTIVE_KUBECONFIG="$kubeconfig_path"
  export BLUEPRINT_ACTIVE_KUBE_CONTEXT="${context_name:-unset}"
  export BLUEPRINT_ACTIVE_KUBE_SOURCE="$context_source"
  log_metric \
    "kube_access_context_prepare_total" \
    "1" \
    "profile=${BLUEPRINT_PROFILE:-unset} context=${BLUEPRINT_ACTIVE_KUBE_CONTEXT} source=$context_source"
  log_info \
    "prepared cluster access profile=${BLUEPRINT_PROFILE:-unset} context=${BLUEPRINT_ACTIVE_KUBE_CONTEXT} source=$context_source kubeconfig=$kubeconfig_path"
}

active_kube_context_name() {
  if [[ -n "${BLUEPRINT_ACTIVE_KUBE_CONTEXT:-}" ]]; then
    printf '%s\n' "$BLUEPRINT_ACTIVE_KUBE_CONTEXT"
    return 0
  fi

  if tooling_is_local_profile; then
    if ! command -v kubectl >/dev/null 2>&1; then
      return 0
    fi
    resolve_local_kube_context
    return 0
  fi

  if tooling_is_stackit_profile; then
    if ! command -v kubectl >/dev/null 2>&1; then
      return 0
    fi
    local kubeconfig_path
    kubeconfig_path="$(stackit_kubeconfig_path)"
    if [[ -f "$kubeconfig_path" ]]; then
      kubectl --kubeconfig "$kubeconfig_path" config current-context 2>/dev/null || true
    fi
    return 0
  fi

  kubectl_current_context_name
}

active_kubeconfig_path() {
  if [[ -n "${BLUEPRINT_ACTIVE_KUBECONFIG:-}" ]]; then
    printf '%s\n' "$BLUEPRINT_ACTIVE_KUBECONFIG"
    return 0
  fi

  if tooling_is_stackit_profile; then
    stackit_kubeconfig_path
    return 0
  fi

  if tooling_is_local_profile; then
    printf '%s\n' "$(local_kubeconfig_artifact_path)"
    return 0
  fi

  printf '%s\n' "${KUBECONFIG:-}"
}

active_kube_access_source() {
  if [[ -n "${BLUEPRINT_ACTIVE_KUBE_SOURCE:-}" ]]; then
    printf '%s\n' "$BLUEPRINT_ACTIVE_KUBE_SOURCE"
    return 0
  fi

  if tooling_is_local_profile; then
    resolve_local_kube_context_source
    return 0
  fi

  if tooling_is_stackit_profile; then
    printf 'stackit-kubeconfig\n'
    return 0
  fi

  printf 'current-context\n'
}

cluster_crd_exists() {
  local crd_name="$1"

  if ! tooling_is_execution_enabled; then
    return 0
  fi

  prepare_cluster_access
  require_command kubectl
  kubectl get crd "$crd_name" >/dev/null 2>&1
}

blueprint_managed_namespaces() {
  set_default_env ARGOCD_NAMESPACE "argocd"
  set_default_env EXTERNAL_SECRETS_NAMESPACE "external-secrets"
  set_default_env CROSSPLANE_NAMESPACE "crossplane-system"
  set_default_env PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE "envoy-gateway-system"

  printf '%s\n' \
    "apps" \
    "observability" \
    "network" \
    "security" \
    "messaging" \
    "data" \
    "$ARGOCD_NAMESPACE" \
    "$EXTERNAL_SECRETS_NAMESPACE" \
    "$CROSSPLANE_NAMESPACE" \
    "$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" |
    awk '!seen[$0]++'
}

wait_for_namespace_deletion() {
  local namespace="$1"
  local timeout_seconds="${2:-180}"
  local metric_name="${3:-namespace_wait_total}"
  local started_at
  local now
  local phase

  if ! tooling_is_execution_enabled; then
    log_metric "$metric_name" "1" "namespace=$namespace status=dry_run"
    return 0
  fi

  started_at="$(date +%s)"
  while true; do
    if ! kubectl get namespace "$namespace" >/dev/null 2>&1; then
      log_metric "$metric_name" "1" "namespace=$namespace status=deleted"
      return 0
    fi

    now="$(date +%s)"
    if ((now - started_at >= timeout_seconds)); then
      phase="$(kubectl get namespace "$namespace" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
      log_metric "$metric_name" "1" "namespace=$namespace status=timeout"
      log_warn "namespace did not finish deleting before timeout namespace=$namespace phase=${phase:-unknown}"
      return 0
    fi

    sleep 2
  done
}

delete_blueprint_managed_namespaces() {
  local timeout_seconds="${1:-180}"
  local metric_prefix="${2:-blueprint_namespace_cleanup}"
  local namespace

  if ! tooling_is_execution_enabled; then
    while IFS= read -r namespace; do
      [[ -n "$namespace" ]] || continue
      log_metric "${metric_prefix}_delete_total" "1" "namespace=$namespace status=dry_run"
      log_metric "${metric_prefix}_wait_total" "1" "namespace=$namespace status=dry_run"
    done < <(blueprint_managed_namespaces)
    return 0
  fi

  require_command kubectl

  while IFS= read -r namespace; do
    [[ -n "$namespace" ]] || continue
    run_cmd kubectl delete namespace "$namespace" --ignore-not-found --wait=false
    log_metric "${metric_prefix}_delete_total" "1" "namespace=$namespace status=requested"
  done < <(blueprint_managed_namespaces)

  while IFS= read -r namespace; do
    [[ -n "$namespace" ]] || continue
    wait_for_namespace_deletion "$namespace" "$timeout_seconds" "${metric_prefix}_wait_total"
  done < <(blueprint_managed_namespaces)
}

terraform_dir_has_config() {
  local terraform_dir="$1"
  [[ -d "$terraform_dir" ]] || return 1
  find "$terraform_dir" -maxdepth 2 -type f -name '*.tf' | grep -q .
}

kustomize_dir_has_config() {
  local kustomize_dir="$1"
  [[ -f "$kustomize_dir/kustomization.yaml" ]] || [[ -f "$kustomize_dir/kustomization.yml" ]] || [[ -f "$kustomize_dir/Kustomization" ]]
}

run_terraform_action() {
  local action="$1"
  local terraform_dir="$2"
  if ! terraform_dir_has_config "$terraform_dir"; then
    log_warn "terraform config not found; skipping action=$action dir=$terraform_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command terraform
    run_cmd terraform -chdir="$terraform_dir" init -input=false -no-color || return "$?"
    case "$action" in
    plan)
      run_cmd terraform -chdir="$terraform_dir" plan -input=false -no-color || return "$?"
      ;;
    apply)
      run_cmd terraform -chdir="$terraform_dir" apply -input=false -auto-approve -no-color || return "$?"
      ;;
    destroy)
      run_cmd terraform -chdir="$terraform_dir" destroy -input=false -auto-approve -no-color || return "$?"
      ;;
    *)
      log_fatal "unsupported terraform action: $action"
      ;;
    esac
    return 0
  fi

  log_info "dry-run terraform action=$action dir=$terraform_dir (set DRY_RUN=false to execute)"
}

terraform_backend_init() {
  local terraform_dir="$1"
  local backend_file="$2"
  if [[ ! -f "$backend_file" ]]; then
    log_warn "terraform backend config not found; skipping init dir=$terraform_dir backend=$backend_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command terraform
    require_env_vars STACKIT_TFSTATE_ACCESS_KEY_ID STACKIT_TFSTATE_SECRET_ACCESS_KEY
    local tf_init_cmd=(
      terraform
      -chdir="$terraform_dir"
      init
      -reconfigure
      -input=false
      -no-color
      "-backend-config=$backend_file" \
      "-backend-config=access_key=$STACKIT_TFSTATE_ACCESS_KEY_ID" \
      "-backend-config=secret_key=$STACKIT_TFSTATE_SECRET_ACCESS_KEY"
    )
    local tf_init_log_cmd=(
      terraform
      -chdir="$terraform_dir"
      init
      -reconfigure
      -input=false
      -no-color
      "-backend-config=$backend_file"
      "-backend-config=access_key=***"
      "-backend-config=secret_key=***"
    )
    if [[ -n "${STACKIT_TFSTATE_BUCKET:-}" ]]; then
      tf_init_cmd+=("-backend-config=bucket=$STACKIT_TFSTATE_BUCKET")
      tf_init_log_cmd+=("-backend-config=bucket=$STACKIT_TFSTATE_BUCKET")
    fi
    if [[ -n "${STACKIT_REGION:-}" ]]; then
      tf_init_cmd+=("-backend-config=region=$STACKIT_REGION")
      tf_init_log_cmd+=("-backend-config=region=$STACKIT_REGION")
    fi
    printf '+ %s\n' "${tf_init_log_cmd[*]}"
    "${tf_init_cmd[@]}" || return "$?"
    return 0
  fi

  log_info "dry-run terraform init dir=$terraform_dir backend=$backend_file (set DRY_RUN=false to execute)"
}

run_terraform_action_with_backend() {
  local action="$1"
  local terraform_dir="$2"
  local backend_file="$3"
  local var_file="$4"
  shift 4 || true
  local extra_args=("$@")

  if ! terraform_dir_has_config "$terraform_dir"; then
    log_warn "terraform config not found; skipping action=$action dir=$terraform_dir"
    return 0
  fi
  if [[ ! -f "$backend_file" ]]; then
    log_warn "terraform backend config not found; skipping action=$action backend=$backend_file"
    return 0
  fi
  if [[ ! -f "$var_file" ]]; then
    log_warn "terraform var-file not found; skipping action=$action var_file=$var_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command terraform
    require_env_vars STACKIT_TFSTATE_ACCESS_KEY_ID STACKIT_TFSTATE_SECRET_ACCESS_KEY

    local tf_init_cmd=(
      terraform
      -chdir="$terraform_dir"
      init
      -reconfigure
      -input=false
      -no-color
      "-backend-config=$backend_file"
      "-backend-config=access_key=$STACKIT_TFSTATE_ACCESS_KEY_ID"
      "-backend-config=secret_key=$STACKIT_TFSTATE_SECRET_ACCESS_KEY"
    )
    if [[ -n "${STACKIT_TFSTATE_BUCKET:-}" ]]; then
      tf_init_cmd+=("-backend-config=bucket=$STACKIT_TFSTATE_BUCKET")
    fi
    if [[ -n "${STACKIT_REGION:-}" ]]; then
      tf_init_cmd+=("-backend-config=region=$STACKIT_REGION")
    fi
    local tf_init_log_cmd=(
      terraform
      -chdir="$terraform_dir"
      init
      -reconfigure
      -input=false
      -no-color
      "-backend-config=$backend_file"
      "-backend-config=access_key=***"
      "-backend-config=secret_key=***"
    )
    if [[ -n "${STACKIT_TFSTATE_BUCKET:-}" ]]; then
      tf_init_log_cmd+=("-backend-config=bucket=$STACKIT_TFSTATE_BUCKET")
    fi
    if [[ -n "${STACKIT_REGION:-}" ]]; then
      tf_init_log_cmd+=("-backend-config=region=$STACKIT_REGION")
    fi
    printf '+ %s\n' "${tf_init_log_cmd[*]}"
    "${tf_init_cmd[@]}" || return "$?"

    local tf_cmd=(terraform -chdir="$terraform_dir")
    case "$action" in
    plan)
      tf_cmd+=(plan -input=false -no-color "-var-file=$var_file")
      ;;
    apply)
      tf_cmd+=(apply -input=false -auto-approve -no-color "-var-file=$var_file")
      ;;
    destroy)
      tf_cmd+=(destroy -input=false -auto-approve -no-color "-var-file=$var_file")
      ;;
    *)
      log_fatal "unsupported terraform action: $action"
      ;;
    esac
    if [[ "${#extra_args[@]}" -gt 0 ]]; then
      tf_cmd+=("${extra_args[@]}")
    fi
    run_cmd "${tf_cmd[@]}" || return "$?"
    return 0
  fi

  log_info "dry-run terraform action=$action dir=$terraform_dir backend=$backend_file var_file=$var_file extra_args=${extra_args[*]:-none} (set DRY_RUN=false to execute)"
}

run_kustomize_apply() {
  local kustomize_dir="$1"
  if ! kustomize_dir_has_config "$kustomize_dir"; then
    log_warn "kustomization not found; skipping dir=$kustomize_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command kubectl
    run_cmd kubectl apply -k "$kustomize_dir"
    return 0
  fi

  log_info "dry-run kubectl apply -k $kustomize_dir (set DRY_RUN=false to execute)"
}

run_kustomize_delete() {
  local kustomize_dir="$1"
  if ! kustomize_dir_has_config "$kustomize_dir"; then
    log_warn "kustomization not found; skipping dir=$kustomize_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command kubectl
    run_cmd kubectl delete -k "$kustomize_dir" --ignore-not-found
    return 0
  fi

  log_info "dry-run kubectl delete -k $kustomize_dir (set DRY_RUN=false to execute)"
}

run_manifest_apply() {
  local manifest_file="$1"
  if [[ ! -f "$manifest_file" ]]; then
    log_warn "manifest file not found; skipping file=$manifest_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command kubectl
    run_cmd kubectl apply -f "$manifest_file"
    return 0
  fi

  log_info "dry-run kubectl apply -f $manifest_file (set DRY_RUN=false to execute)"
}

run_manifest_delete() {
  local manifest_file="$1"
  if [[ ! -f "$manifest_file" ]]; then
    log_warn "manifest file not found; skipping file=$manifest_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command kubectl
    run_cmd kubectl delete -f "$manifest_file" --ignore-not-found
    return 0
  fi

  log_info "dry-run kubectl delete -f $manifest_file (set DRY_RUN=false to execute)"
}

run_helm_upgrade_install() {
  local release_name="$1"
  local namespace="$2"
  local chart_ref="$3"
  local chart_version="$4"
  local values_file="$5"

  if [[ ! -f "$values_file" ]]; then
    log_warn "helm values file not found; skipping values_file=$values_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command helm
    prepare_helm_repo_for_chart "$chart_ref"
    run_cmd helm upgrade --install \
      "$release_name" \
      "$chart_ref" \
      --namespace "$namespace" \
      --create-namespace \
      --version "$chart_version" \
      --values "$values_file"
    return 0
  fi

  log_info "dry-run helm upgrade --install release=$release_name chart=$chart_ref version=$chart_version values=$values_file (set DRY_RUN=false to execute)"
}

run_helm_uninstall() {
  local release_name="$1"
  local namespace="$2"

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command helm
    run_cmd helm uninstall "$release_name" --namespace "$namespace" --ignore-not-found
    return 0
  fi

  log_info "dry-run helm uninstall release=$release_name namespace=$namespace (set DRY_RUN=false to execute)"
}

run_helm_template() {
  local release_name="$1"
  local namespace="$2"
  local chart_ref="$3"
  local chart_version="$4"
  local values_file="$5"

  if [[ ! -f "$values_file" ]]; then
    log_warn "helm values file not found; skipping values_file=$values_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    prepare_cluster_access
    require_command helm
    prepare_helm_repo_for_chart "$chart_ref"
    run_cmd helm template \
      "$release_name" \
      "$chart_ref" \
      --namespace "$namespace" \
      --version "$chart_version" \
      --values "$values_file" >/dev/null
    return 0
  fi

  log_info "dry-run helm template release=$release_name chart=$chart_ref version=$chart_version values=$values_file (set DRY_RUN=false to execute)"
}

prepare_helm_repo_for_chart() {
  local chart_ref="$1"
  if [[ "$chart_ref" == oci://* ]]; then
    return 0
  fi

  local repo_name
  repo_name="${chart_ref%%/*}"
  local repo_url=""
  case "$repo_name" in
  bitnami)
    repo_url="https://charts.bitnami.com/bitnami"
    ;;
  argo)
    repo_url="https://argoproj.github.io/argo-helm"
    ;;
  crossplane-stable)
    repo_url="https://charts.crossplane.io/stable"
    ;;
  external-secrets)
    repo_url="https://charts.external-secrets.io"
    ;;
  jetstack)
    repo_url="https://charts.jetstack.io"
    ;;
  neo4j)
    repo_url="https://helm.neo4j.com/neo4j"
    ;;
  grafana)
    repo_url="https://grafana.github.io/helm-charts"
    ;;
  langfuse)
    repo_url="https://langfuse.github.io/langfuse-k8s"
    ;;
  open-telemetry)
    repo_url="https://open-telemetry.github.io/opentelemetry-helm-charts"
    ;;
  oauth2-proxy)
    repo_url="https://oauth2-proxy.github.io/manifests"
    ;;
  codecentric)
    repo_url="https://codecentric.github.io/helm-charts"
    ;;
  *)
    log_warn "unknown helm repository prefix '$repo_name'; continuing without repo bootstrap"
    return 0
    ;;
  esac

  if [[ "$HELM_PREPARED_REPOS_CACHE" == *"|${repo_name}|"* ]]; then
    log_metric "helm_repo_prepare_total" "1" "repo=$repo_name status=cached"
    return 0
  fi

  run_cmd helm repo add "$repo_name" "$repo_url"
  # Refresh each repo only once per process to reduce strict-lane runtime and
  # external flakiness while preserving deterministic pin checks.
  run_cmd helm repo update "$repo_name"
  HELM_PREPARED_REPOS_CACHE="${HELM_PREPARED_REPOS_CACHE}${repo_name}|"
  log_metric "helm_repo_prepare_total" "1" "repo=$repo_name status=updated"
}
