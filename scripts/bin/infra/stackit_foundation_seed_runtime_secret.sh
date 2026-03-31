#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_foundation_seed_runtime_secret"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_seed_runtime_secret.sh

Reads STACKIT foundation Terraform outputs and seeds runtime Kubernetes Secret
used by platform workloads (`platform-foundation-contract`).
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-foundation-seed-runtime-secret requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

set_default_env STACKIT_RUNTIME_CONTRACT_SECRET_NAMESPACE "apps"
set_default_env STACKIT_RUNTIME_CONTRACT_SECRET_NAME "platform-foundation-contract"

stackit_layer_preflight "foundation"
foundation_dir="$(stackit_layer_dir "foundation")"
backend_file="$(stackit_layer_backend_file "foundation")"

seed_mode="dry-run-state"
secret_key_count=0

if tooling_is_execution_enabled; then
  prepare_cluster_access
  require_command terraform
  require_command kubectl
  require_command python3

  terraform_backend_init "$foundation_dir" "$backend_file"

  outputs_json_file="$(mktemp)"
  secret_env_file="$(mktemp)"
  namespace_manifest_file="$(mktemp)"
  secret_manifest_file="$(mktemp)"
  trap 'rm -f "$outputs_json_file" "$secret_env_file" "$namespace_manifest_file" "$secret_manifest_file"' EXIT

  run_cmd_capture terraform -chdir="$foundation_dir" output -json >"$outputs_json_file"

  python3 - "$outputs_json_file" "$secret_env_file" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])

# Keep this allowlist tight so the secret contract is deterministic and does
# not include large/non-scalar outputs (for example module metadata maps).
# Each entry maps <terraform_output_name> -> <runtime_secret_key>.
allowed = [
    ("ske_cluster_name", "ske_cluster_name"),
    ("postgres_host", "postgres_host"),
    ("postgres_port", "postgres_port"),
    ("postgres_username", "postgres_username"),
    ("postgres_password", "postgres_password"),
    ("postgres_database", "postgres_database"),
    ("keycloak_postgres_host", "KEYCLOAK_DATABASE_HOST"),
    ("keycloak_postgres_port", "KEYCLOAK_DATABASE_PORT"),
    ("keycloak_postgres_username", "KEYCLOAK_DATABASE_USERNAME"),
    ("keycloak_postgres_password", "KEYCLOAK_DATABASE_PASSWORD"),
    ("keycloak_postgres_database", "KEYCLOAK_DATABASE_NAME"),
    ("object_storage_bucket_name", "object_storage_bucket_name"),
    ("object_storage_access_key", "object_storage_access_key"),
    ("object_storage_secret_access_key", "object_storage_secret_access_key"),
    ("rabbitmq_instance_id", "rabbitmq_instance_id"),
    ("rabbitmq_host", "rabbitmq_host"),
    ("rabbitmq_port", "rabbitmq_port"),
    ("rabbitmq_username", "rabbitmq_username"),
    ("rabbitmq_password", "rabbitmq_password"),
    ("rabbitmq_uri", "rabbitmq_uri"),
    ("secrets_manager_instance_id", "secrets_manager_instance_id"),
    ("secrets_manager_username", "secrets_manager_username"),
    ("secrets_manager_password", "secrets_manager_password"),
    ("observability_instance_id", "observability_instance_id"),
    ("observability_grafana_url", "observability_grafana_url"),
    ("observability_credential_username", "observability_credential_username"),
    ("observability_credential_password", "observability_credential_password"),
    ("kms_key_ring_name", "kms_key_ring_name"),
    ("kms_key_name", "kms_key_name"),
    ("kms_key_ring_id", "kms_key_ring_id"),
    ("kms_key_id", "kms_key_id"),
]

lines = []
for output_name, secret_key in allowed:
    if output_name not in payload:
      continue
    value = payload[output_name].get("value")
    if value is None:
      continue
    if isinstance(value, bool):
      rendered = "true" if value else "false"
    elif isinstance(value, (int, float)):
      rendered = str(value)
    elif isinstance(value, str):
      rendered = value
    else:
      continue
    if "\n" in rendered or rendered == "":
      continue
    lines.append(f"{secret_key}={rendered}")

out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
PY

  {
    echo "stackit_project_id=${STACKIT_PROJECT_ID}"
    echo "stackit_region=${STACKIT_REGION}"
    echo "environment=$(profile_environment)"
  } >>"$secret_env_file"

  secret_key_count="$(grep -c '=' "$secret_env_file" || true)"
  if [[ "$secret_key_count" -eq 0 ]]; then
    log_warn "no foundation runtime outputs resolved; creating metadata-only secret payload"
  fi

  run_cmd_capture kubectl create namespace "$STACKIT_RUNTIME_CONTRACT_SECRET_NAMESPACE" --dry-run=client -o yaml >"$namespace_manifest_file"
  run_cmd kubectl apply -f "$namespace_manifest_file"

  run_cmd_capture kubectl -n "$STACKIT_RUNTIME_CONTRACT_SECRET_NAMESPACE" create secret generic "$STACKIT_RUNTIME_CONTRACT_SECRET_NAME" \
    --from-env-file="$secret_env_file" \
    --dry-run=client -o yaml >"$secret_manifest_file"
  run_cmd kubectl apply -f "$secret_manifest_file"

  seed_mode="kubectl-apply"
fi

state_file="$(
  write_state_file "stackit_foundation_runtime_secret" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "seed_mode=$seed_mode" \
    "terraform_dir=$foundation_dir" \
    "backend_file=$backend_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "secret_namespace=$STACKIT_RUNTIME_CONTRACT_SECRET_NAMESPACE" \
    "secret_name=$STACKIT_RUNTIME_CONTRACT_SECRET_NAME" \
    "secret_key_count=$secret_key_count" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_metric "stackit_runtime_secret_key_count" "$secret_key_count" "secret=$STACKIT_RUNTIME_CONTRACT_SECRET_NAME"
log_info "stackit foundation runtime secret state written to $state_file"
