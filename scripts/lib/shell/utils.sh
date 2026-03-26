#!/usr/bin/env bash
set -euo pipefail

shell_normalize_bool_truefalse() {
  local raw_value="${1:-}"
  local normalized
  normalized="$(printf '%s' "$raw_value" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
  1 | true | yes | on)
    printf 'true'
    ;;
  *)
    printf 'false'
    ;;
  esac
}

shell_normalize_bool_10() {
  if [[ "$(shell_normalize_bool_truefalse "${1:-}")" == "true" ]]; then
    printf '1'
    return 0
  fi
  printf '0'
}

shell_detect_platform() {
  case "$(uname -s)" in
  Darwin)
    printf 'darwin'
    ;;
  Linux)
    printf 'linux'
    ;;
  *)
    printf 'unknown'
    ;;
  esac
}

shell_detect_arch() {
  case "$(uname -m)" in
  x86_64 | amd64)
    printf 'amd64'
    ;;
  arm64 | aarch64)
    printf 'arm64'
    ;;
  *)
    printf 'unknown'
    ;;
  esac
}

shell_resolve_dir() {
  local repo_root="$1"
  local dir="$2"
  if [[ "$dir" = /* ]]; then
    printf '%s' "$dir"
    return 0
  fi
  printf '%s/%s' "$repo_root" "$dir"
}

shell_resolve_executable() {
  local preferred_bin="${1:-}"
  local fallback_bin="${2:-}"
  local candidate="$preferred_bin"

  if [[ -z "$candidate" ]]; then
    candidate="$fallback_bin"
  fi
  if [[ -z "$candidate" ]]; then
    return 1
  fi

  if [[ "$candidate" == */* ]]; then
    [[ -x "$candidate" ]] || return 1
    printf '%s' "$candidate"
    return 0
  fi

  command -v "$candidate" >/dev/null 2>&1 || return 1
  command -v "$candidate"
}

shell_local_port_in_use() {
  local port="$1"
  nc -z 127.0.0.1 "$port" >/dev/null 2>&1
}
