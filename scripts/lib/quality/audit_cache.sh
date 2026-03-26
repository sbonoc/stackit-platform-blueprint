#!/usr/bin/env bash
set -euo pipefail

audit_cache_hash_file() {
  local file_path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file_path" | awk '{print $1}'
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file_path" | awk '{print $1}'
    return 0
  fi
  log_fatal "missing hash tool (shasum or sha256sum)"
}

audit_cache_hash_stdin() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
    return 0
  fi
  log_fatal "missing hash tool (shasum or sha256sum)"
}

audit_cache_calculate_fingerprint() {
  local payload=""
  local rel_path
  for rel_path in "$@"; do
    local abs_path="$ROOT_DIR/$rel_path"
    if [[ ! -f "$abs_path" ]]; then
      log_fatal "audit cache fingerprint file missing: $rel_path"
    fi
    payload+="$rel_path:$(audit_cache_hash_file "$abs_path")"$'\n'
  done
  printf '%s' "$payload" | audit_cache_hash_stdin
}

audit_cache_read_field() {
  local cache_file="$1"
  local key="$2"
  awk -F'=' -v target="$key" '$1 == target {print substr($0, index($0, "=") + 1); exit}' "$cache_file" 2>/dev/null || true
}

audit_cache_write_success() {
  local cache_file="$1"
  local fingerprint="$2"
  local now_epoch="$3"
  mkdir -p "$(dirname "$cache_file")"
  cat >"$cache_file" <<EOF
timestamp=$now_epoch
fingerprint=$fingerprint
EOF
}

audit_cache_should_skip() {
  local cache_file="$1"
  local fingerprint="$2"
  local ttl_seconds="$3"
  local now_epoch="$4"

  [[ -f "$cache_file" ]] || return 1
  [[ "$ttl_seconds" =~ ^[0-9]+$ ]] || return 1
  ((ttl_seconds > 0)) || return 1

  local cached_timestamp
  local cached_fingerprint
  local age_seconds
  cached_timestamp="$(audit_cache_read_field "$cache_file" "timestamp")"
  cached_fingerprint="$(audit_cache_read_field "$cache_file" "fingerprint")"

  [[ "$cached_timestamp" =~ ^[0-9]+$ ]] || return 1
  [[ -n "$cached_fingerprint" ]] || return 1
  [[ "$cached_fingerprint" == "$fingerprint" ]] || return 1

  age_seconds=$((now_epoch - cached_timestamp))
  ((age_seconds >= 0)) || return 1
  ((age_seconds <= ttl_seconds)) || return 1
  return 0
}

audit_cache_run() {
  local label="$1"
  local strict_script="$2"
  local cache_file="$3"
  local ttl_seconds="$4"
  local use_cache="$5"
  local force_refresh="$6"
  shift 6 || true
  local fingerprint_files=("$@")

  if [[ "${CI:-}" == "1" || "${CI:-}" == "true" ]]; then
    use_cache="false"
  fi
  if [[ "$force_refresh" == "true" ]]; then
    use_cache="false"
  fi

  local fingerprint=""
  local now_epoch
  now_epoch="$(date +%s)"
  if [[ "$use_cache" == "true" ]]; then
    fingerprint="$(audit_cache_calculate_fingerprint "${fingerprint_files[@]}")"
    if audit_cache_should_skip "$cache_file" "$fingerprint" "$ttl_seconds" "$now_epoch"; then
      log_info "$label cache hit; skipping strict audit (ttl=${ttl_seconds}s)"
      log_metric "audit_cache_hit" "1" "audit=$label"
      return 0
    fi
  fi

  log_metric "audit_cache_hit" "0" "audit=$label"
  run_cmd "$strict_script"

  if [[ "$use_cache" == "true" ]]; then
    if [[ -z "$fingerprint" ]]; then
      fingerprint="$(audit_cache_calculate_fingerprint "${fingerprint_files[@]}")"
    fi
    audit_cache_write_success "$cache_file" "$fingerprint" "$now_epoch"
    log_info "$label cache updated: $cache_file"
  fi
}
