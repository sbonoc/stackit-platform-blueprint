#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

PORT_FORWARD_LAST_PID="${PORT_FORWARD_LAST_PID:-}"

port_forward_init_defaults() {
  set_default_env PORT_FORWARD_WAIT_TIMEOUT_SECONDS "30"
  set_default_env PORT_FORWARD_WAIT_POLL_SECONDS "1"
  set_default_env PORT_FORWARD_STOP_TIMEOUT_SECONDS "10"
  set_default_env PORT_FORWARD_FORCE_KILL "false"
}

port_forward_init_defaults

port_forward_force_kill_enabled() {
  [[ "$(tooling_normalize_bool "${PORT_FORWARD_FORCE_KILL:-false}")" == "true" ]]
}

port_forward_require_port_number() {
  local value="$1"
  local name="$2"
  if [[ ! "$value" =~ ^[0-9]+$ || "$value" -le 0 || "$value" -gt 65535 ]]; then
    log_fatal "$name must be a valid port in range 1..65535 (got '$value')"
  fi
}

port_forward_registry_file() {
  printf '%s/artifacts/infra/port-forwards.registry' "$ROOT_DIR"
}

port_forward_registry_ensure() {
  local file
  file="$(port_forward_registry_file)"
  ensure_dir "$(dirname "$file")"
  touch "$file"
}

port_forward_registry_lookup() {
  local name="$1"
  local file
  file="$(port_forward_registry_file)"
  [[ -f "$file" ]] || return 1
  awk -F'|' -v name="$name" '
    $1 == name {
      print $0
      found = 1
      exit 0
    }
    END {
      if (!found) {
        exit 1
      }
    }
  ' "$file"
}

port_forward_registry_upsert() {
  local name="$1"
  local pid="$2"
  local local_port="$3"
  local log_path="$4"

  port_forward_registry_ensure
  local file tmp_file
  file="$(port_forward_registry_file)"
  tmp_file="$(mktemp)"

  awk -F'|' -v name="$name" '$1 != name { print $0 }' "$file" >"$tmp_file"
  printf '%s|%s|%s|%s\n' "$name" "$pid" "$local_port" "$log_path" >>"$tmp_file"
  mv "$tmp_file" "$file"
}

port_forward_registry_remove() {
  local name="$1"
  local file tmp_file
  file="$(port_forward_registry_file)"
  [[ -f "$file" ]] || return 0
  tmp_file="$(mktemp)"
  awk -F'|' -v name="$name" '$1 != name { print $0 }' "$file" >"$tmp_file"
  mv "$tmp_file" "$file"
}

port_forward_registry_names() {
  local file
  file="$(port_forward_registry_file)"
  [[ -f "$file" ]] || return 0
  awk -F'|' 'NF >= 1 && $1 != "" { print $1 }' "$file"
}

port_forward_registry_prune_stale_entries() {
  port_forward_registry_ensure
  local file tmp_file
  file="$(port_forward_registry_file)"
  tmp_file="$(mktemp)"

  local pruned_count="0"
  local name pid local_port log_path
  while IFS='|' read -r name pid local_port log_path; do
    [[ -n "$name" ]] || continue
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      printf '%s|%s|%s|%s\n' "$name" "$pid" "$local_port" "$log_path" >>"$tmp_file"
      continue
    fi
    pruned_count=$((pruned_count + 1))
  done <"$file"

  mv "$tmp_file" "$file"
  if [[ "$pruned_count" -gt 0 ]]; then
    log_metric "port_forward_registry_prune_total" "$pruned_count" "status=stale_entries_removed"
  fi
}

port_forward_pid_for_name() {
  local name="$1"
  local line
  line="$(port_forward_registry_lookup "$name")" || return 1
  IFS='|' read -r _name pid _port _log_path <<<"$line"
  printf '%s\n' "$pid"
}

port_forward_log_path_for_name() {
  local name="$1"
  local line
  line="$(port_forward_registry_lookup "$name")" || return 1
  IFS='|' read -r _name _pid _port log_path <<<"$line"
  printf '%s\n' "$log_path"
}

start_port_forward() {
  local name="$1"
  local namespace="$2"
  local resource_ref="$3"
  local local_port="$4"
  local remote_port="$5"
  local log_path="${6:-$ROOT_DIR/artifacts/infra/port-forward-${name}.log}"

  port_forward_require_port_number "$local_port" "local_port"
  port_forward_require_port_number "$remote_port" "remote_port"

  if ! tooling_is_execution_enabled; then
    log_metric "port_forward_start_total" "1" "name=$name status=dry_run"
    log_info \
      "dry-run kubectl port-forward name=$name namespace=$namespace resource=$resource_ref local_port=$local_port remote_port=$remote_port (set DRY_RUN=false to execute)"
    return 0
  fi

  require_command kubectl
  require_command nc

  # Prune stale PIDs first so previous crashed sessions do not block reuse.
  port_forward_registry_prune_stale_entries

  if port_forward_registry_lookup "$name" >/dev/null 2>&1; then
    stop_port_forward "$name"
  fi

  if shell_local_port_in_use "$local_port"; then
    log_fatal "local port already in use for port-forward name=$name local_port=$local_port"
  fi

  ensure_dir "$(dirname "$log_path")"
  : >"$log_path"

  resolve_active_kube_access_args
  local -a cmd=(
    kubectl
    "${KUBECTL_ACTIVE_ACCESS_ARGS[@]}"
    -n "$namespace"
    port-forward
    "$resource_ref"
    "${local_port}:${remote_port}"
  )

  printf '+ %s >%s 2>&1 &\n' "${cmd[*]}" "$log_path"
  "${cmd[@]}" >"$log_path" 2>&1 &
  local pf_pid=$!

  PORT_FORWARD_LAST_PID="$pf_pid"
  port_forward_registry_upsert "$name" "$pf_pid" "$local_port" "$log_path"

  log_metric \
    "port_forward_start_total" \
    "1" \
    "name=$name status=started namespace=$namespace resource=$resource_ref local_port=$local_port remote_port=$remote_port pid=$pf_pid"
  log_info \
    "started port-forward name=$name namespace=$namespace resource=$resource_ref local_port=$local_port remote_port=$remote_port pid=$pf_pid log_path=$log_path"
}

wait_for_local_port() {
  local name="$1"
  local local_port="$2"
  local timeout_seconds="${3:-$PORT_FORWARD_WAIT_TIMEOUT_SECONDS}"

  port_forward_require_port_number "$local_port" "local_port"
  tooling_require_positive_integer "$timeout_seconds" "timeout_seconds"
  tooling_require_positive_integer "$PORT_FORWARD_WAIT_POLL_SECONDS" "PORT_FORWARD_WAIT_POLL_SECONDS"

  if ! tooling_is_execution_enabled; then
    log_metric "port_forward_wait_total" "1" "name=$name status=dry_run local_port=$local_port"
    return 0
  fi

  require_command nc

  local pid log_path
  pid="$(port_forward_pid_for_name "$name" || true)"
  log_path="$(port_forward_log_path_for_name "$name" || true)"
  local start_epoch
  start_epoch="$(date +%s)"

  while true; do
    if shell_local_port_in_use "$local_port"; then
      local elapsed_success=$(( $(date +%s) - start_epoch ))
      log_metric "port_forward_wait_total" "1" "name=$name status=ready local_port=$local_port wait_seconds=$elapsed_success"
      return 0
    fi

    if [[ -n "$pid" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
      local elapsed_exited=$(( $(date +%s) - start_epoch ))
      log_metric "port_forward_wait_total" "1" "name=$name status=process_exited local_port=$local_port wait_seconds=$elapsed_exited"
      if [[ -n "$log_path" && -f "$log_path" ]]; then
        log_warn "port-forward process exited early name=$name pid=$pid local_port=$local_port (tailing log: $log_path)"
        tail -n 20 "$log_path" >&2 || true
      fi
      return 1
    fi

    if (( $(date +%s) - start_epoch >= timeout_seconds )); then
      local elapsed_timeout=$(( $(date +%s) - start_epoch ))
      log_metric "port_forward_wait_total" "1" "name=$name status=timeout local_port=$local_port wait_seconds=$elapsed_timeout"
      log_warn "timed out waiting for local port-forward readiness name=$name local_port=$local_port timeout=${timeout_seconds}s"
      return 1
    fi

    sleep "$PORT_FORWARD_WAIT_POLL_SECONDS"
  done
}

stop_port_forward() {
  local name="$1"
  local force_kill="${2:-$PORT_FORWARD_FORCE_KILL}"

  if ! tooling_is_execution_enabled; then
    log_metric "port_forward_stop_total" "1" "name=$name status=dry_run"
    return 0
  fi

  tooling_require_positive_integer "$PORT_FORWARD_STOP_TIMEOUT_SECONDS" "PORT_FORWARD_STOP_TIMEOUT_SECONDS"
  port_forward_registry_prune_stale_entries

  local line pid local_port log_path
  line="$(port_forward_registry_lookup "$name" || true)"
  if [[ -z "$line" ]]; then
    log_metric "port_forward_stop_total" "1" "name=$name status=missing"
    return 0
  fi
  IFS='|' read -r _name pid local_port log_path <<<"$line"

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    port_forward_registry_remove "$name"
    log_metric "port_forward_stop_total" "1" "name=$name status=already_exited pid=$pid local_port=$local_port"
    return 0
  fi

  kill "$pid" >/dev/null 2>&1 || true

  local start_epoch
  start_epoch="$(date +%s)"
  while kill -0 "$pid" >/dev/null 2>&1; do
    if (( $(date +%s) - start_epoch >= PORT_FORWARD_STOP_TIMEOUT_SECONDS )); then
      if [[ "$(tooling_normalize_bool "$force_kill")" == "true" ]]; then
        kill -9 "$pid" >/dev/null 2>&1 || true
        log_metric "port_forward_stop_total" "1" "name=$name status=force_killed pid=$pid local_port=$local_port"
      else
        log_warn \
          "port-forward process still running after timeout name=$name pid=$pid timeout=${PORT_FORWARD_STOP_TIMEOUT_SECONDS}s log_path=$log_path"
        log_metric "port_forward_stop_total" "1" "name=$name status=timeout pid=$pid local_port=$local_port"
      fi
      if [[ "$(tooling_normalize_bool "$force_kill")" != "true" ]]; then
        break
      fi
    fi
    sleep 1
  done

  if kill -0 "$pid" >/dev/null 2>&1; then
    log_metric "port_forward_stop_total" "1" "name=$name status=still_running pid=$pid local_port=$local_port"
    log_warn "port-forward process still running name=$name pid=$pid; registry entry kept for follow-up stop/cleanup"
    return 1
  fi

  wait "$pid" >/dev/null 2>&1 || true
  port_forward_registry_remove "$name"
  log_metric "port_forward_stop_total" "1" "name=$name status=stopped pid=$pid local_port=$local_port"
}

cleanup_port_forwards() {
  local force_kill="${1:-$PORT_FORWARD_FORCE_KILL}"
  port_forward_registry_prune_stale_entries
  local name
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    stop_port_forward "$name" "$force_kill" || true
  done < <(port_forward_registry_names)

  local remaining_count="0"
  if [[ -f "$(port_forward_registry_file)" ]]; then
    remaining_count="$(port_forward_registry_names | wc -l | tr -d '[:space:]')"
  fi
  log_metric "port_forward_cleanup_total" "1" "remaining=$remaining_count"
}
