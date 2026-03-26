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

write_state_file() {
  local name="$1"
  shift
  local file
  file="$(state_file_path "$name" "$STATE_NAMESPACE")"
  mkdir -p "$(dirname "$file")"
  : >"$file"
  while (($#)); do
    printf '%s\n' "$1" >>"$file"
    shift
  done
  echo "$file"
}

state_file_exists() {
  local name="$1"
  local file
  file="$(state_file_path "$name" "$STATE_NAMESPACE")"
  [[ -f "$file" ]]
}

remove_state_file() {
  local name="$1"
  local file
  file="$(state_file_path "$name" "$STATE_NAMESPACE")"
  rm -f "$file"
}

remove_state_files_by_prefix() {
  local prefix="$1"
  local dir
  dir="$(state_dir "$STATE_NAMESPACE")"
  if [[ ! -d "$dir" ]]; then
    return 0
  fi
  rm -f "$dir/${prefix}"*.env
}
