#!/usr/bin/env bash
set -euo pipefail

bootstrap_templates_root() {
  local namespace="$1"
  case "$namespace" in
  blueprint|infra)
    echo "$ROOT_DIR/scripts/templates/$namespace/bootstrap"
    ;;
  *)
    log_fatal "unsupported bootstrap template namespace: $namespace"
    ;;
  esac
}

bootstrap_template_path() {
  local namespace="$1"
  local template_rel="$2"
  echo "$(bootstrap_templates_root "$namespace")/$template_rel"
}

bootstrap_template_content() {
  local namespace="$1"
  local template_rel="$2"
  local template_path
  template_path="$(bootstrap_template_path "$namespace" "$template_rel")"
  if [[ ! -f "$template_path" ]]; then
    log_fatal "missing bootstrap template ($namespace): $template_path"
  fi
  cat "$template_path"
}

render_bootstrap_template_content() {
  local namespace="$1"
  local template_rel="$2"
  shift 2 || true

  local content
  content="$(bootstrap_template_content "$namespace" "$template_rel")"

  local pair key value
  for pair in "$@"; do
    key="${pair%%=*}"
    value="${pair#*=}"
    content="${content//\{\{$key\}\}/$value}"
  done

  printf '%s' "$content"
}

ensure_file_from_template() {
  local target_path="$1"
  local namespace="$2"
  local template_rel="$3"
  ensure_file_with_content "$target_path" "$(bootstrap_template_content "$namespace" "$template_rel")"
}

ensure_file_from_rendered_template() {
  local target_path="$1"
  local namespace="$2"
  local template_rel="$3"
  shift 3 || true
  ensure_file_with_content "$target_path" "$(render_bootstrap_template_content "$namespace" "$template_rel" "$@")"
}
