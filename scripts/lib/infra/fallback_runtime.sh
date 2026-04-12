#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"

# These helpers are often used in command substitutions, so stdout must stay
# reserved for the returned artifact path. Diagnostic logs go to stderr.
render_optional_module_values_file() {
  local module="$1"
  local template_rel="$2"
  shift 2 || true

  local target_path
  target_path="$(rendered_module_helm_values_file "$module")"
  ensure_dir "$(dirname "$target_path")"
  printf '%s' "$(render_bootstrap_template_content "infra" "$template_rel" "$@")" >"$target_path"
  log_metric "optional_module_values_render_total" "1" "module=$module target=$target_path" >&2
  log_info "rendered optional-module values artifact: $target_path" >&2
  printf '%s\n' "$target_path"
}

optional_module_namespace_manifest_file() {
  local namespace="$1"
  printf '%s/namespace-%s.yaml' "$(rendered_optional_module_secret_artifacts_dir)" "$namespace"
}

optional_module_secret_manifest_file() {
  local namespace="$1"
  local name="$2"
  printf '%s/secret-%s-%s.yaml' "$(rendered_optional_module_secret_artifacts_dir)" "$namespace" "$name"
}

render_optional_module_secret_manifests() {
  local namespace="$1"
  local name="$2"
  shift 2 || true

  ensure_dir "$(rendered_optional_module_secret_artifacts_dir)"

  local namespace_manifest_file secret_manifest_file
  namespace_manifest_file="$(optional_module_namespace_manifest_file "$namespace")"
  secret_manifest_file="$(optional_module_secret_manifest_file "$namespace" "$name")"

  cat >"$namespace_manifest_file" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${namespace}
EOF

  {
    cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: ${name}
  namespace: ${namespace}
type: Opaque
data:
EOF
    local pair key value encoded
    for pair in "$@"; do
      key="${pair%%=*}"
      value="${pair#*=}"
      encoded="$(printf '%s' "$value" | base64 | tr -d '\n')"
      printf '  %s: %s\n' "$key" "$encoded"
    done
  } >"$secret_manifest_file"

  log_metric "optional_module_secret_render_total" "1" "namespace=$namespace secret=$name" >&2
  printf '%s\n' "$secret_manifest_file"
}

apply_optional_module_secret_from_literals() {
  local namespace="$1"
  local name="$2"
  shift 2 || true

  local secret_manifest_file namespace_manifest_file
  secret_manifest_file="$(render_optional_module_secret_manifests "$namespace" "$name" "$@")"
  namespace_manifest_file="$(optional_module_namespace_manifest_file "$namespace")"

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_kubectl_with_active_access apply -f "$namespace_manifest_file"
    run_kubectl_with_active_access apply -f "$secret_manifest_file"
  else
    # Dry-run still writes deterministic manifests so tests and operators can
    # inspect the exact runtime secret contract without requiring kubectl.
    log_info "dry-run secret reconcile namespace=$namespace secret=$name (set DRY_RUN=false to execute)"
  fi

  log_info "optional-module secret manifest written to $secret_manifest_file"
}

delete_optional_module_secret() {
  local namespace="$1"
  local name="$2"
  local secret_manifest_file
  secret_manifest_file="$(optional_module_secret_manifest_file "$namespace" "$name")"

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_kubectl_with_active_access -n "$namespace" delete secret "$name" --ignore-not-found
  else
    log_info "dry-run secret delete namespace=$namespace secret=$name (set DRY_RUN=false to execute)"
  fi

  rm -f "$secret_manifest_file"
}
