#!/usr/bin/env bash
set -euo pipefail

STATE_NAMESPACE="${STATE_NAMESPACE:-infra}"

normalize_state_namespace() {
  local namespace="${1:-infra}"
  case "$namespace" in
  infra | apps | docs)
    echo "$namespace"
    ;;
  *)
    log_fatal "unsupported state namespace: $namespace"
    ;;
  esac
}

set_state_namespace() {
  STATE_NAMESPACE="$(normalize_state_namespace "$1")"
}

state_dir() {
  local namespace="${1:-$STATE_NAMESPACE}"
  namespace="$(normalize_state_namespace "$namespace")"
  echo "$ROOT_DIR/artifacts/$namespace"
}

state_file_path() {
  local name="$1"
  local namespace="${2:-$STATE_NAMESPACE}"
  echo "$(state_dir "$namespace")/$name.env"
}

state_json_file_path() {
  local name="$1"
  local namespace="${2:-$STATE_NAMESPACE}"
  echo "$(state_dir "$namespace")/$name.json"
}

write_state_file() {
  local name="$1"
  shift
  local file json_file schema_path contract_cli
  file="$(state_file_path "$name" "$STATE_NAMESPACE")"
  json_file="$(state_json_file_path "$name" "$STATE_NAMESPACE")"
  mkdir -p "$(dirname "$file")"
  : >"$file"
  while (($#)); do
    printf '%s\n' "$1" >>"$file"
    shift
  done

  contract_cli="$ROOT_DIR/scripts/lib/infra/state_artifact_contract.py"
  schema_path="$ROOT_DIR/scripts/lib/infra/schemas/state_artifact.schema.json"
  if [[ ! -f "$contract_cli" || ! -f "$schema_path" ]]; then
    log_fatal "state artifact contract helper missing ($contract_cli or $schema_path)"
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    log_fatal "python3 is required to render state artifact JSON sidecars"
  fi
  if ! python3 "$contract_cli" \
    --repo-root "$ROOT_DIR" \
    --schema "$schema_path" \
    render \
    --name "$name" \
    --namespace "$STATE_NAMESPACE" \
    --env-file "$file" \
    --output-json "$json_file"; then
    log_fatal "state artifact JSON validation failed for $(basename "$file")"
  fi
  echo "$file"
}

state_file_exists() {
  local name="$1"
  local namespace="${2:-$STATE_NAMESPACE}"
  local file
  file="$(state_file_path "$name" "$namespace")"
  [[ -f "$file" ]]
}

remove_state_file() {
  local name="$1"
  local file json_file
  file="$(state_file_path "$name" "$STATE_NAMESPACE")"
  json_file="$(state_json_file_path "$name" "$STATE_NAMESPACE")"
  rm -f "$file"
  rm -f "$json_file"
}

remove_state_files_by_prefix() {
  local prefix="$1"
  local dir
  dir="$(state_dir "$STATE_NAMESPACE")"
  if [[ ! -d "$dir" ]]; then
    return 0
  fi
  rm -f "$dir/${prefix}"*.env
  rm -f "$dir/${prefix}"*.json
}
