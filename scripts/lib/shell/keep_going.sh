#!/usr/bin/env bash
# keep_going.sh — keep-going aggregation helper for quality hooks
# Requires: logging.sh and exec.sh sourced in calling environment (via bootstrap.sh)

_KG_TMPDIR=""
_KG_NAMES=()
_KG_STATUSES=()
_KG_DURATIONS=()
_KG_CAPFILES=()
_KG_FAILED_COUNT=0
_KG_PREV_TRAP=""

keep_going_active() {
  [[ "${QUALITY_HOOKS_KEEP_GOING:-}" == "true" ]]
}

_kg_cleanup() {
  if [[ -n "${_KG_TMPDIR:-}" && -d "$_KG_TMPDIR" ]]; then
    rm -rf "$_KG_TMPDIR"
    _KG_TMPDIR=""
  fi
}

_kg_exit_handler() {
  _kg_cleanup
  if [[ -n "$_KG_PREV_TRAP" ]]; then
    eval "$_KG_PREV_TRAP" || true
  fi
}

keep_going_init() {
  _KG_TMPDIR="$(mktemp -d -t quality_hook_XXXX)"
  _KG_NAMES=()
  _KG_STATUSES=()
  _KG_DURATIONS=()
  _KG_CAPFILES=()
  _KG_FAILED_COUNT=0
  # Extract existing EXIT trap command for composition
  _KG_PREV_TRAP="$(trap -p EXIT 2>/dev/null | sed -n "s/^trap -- '\\(.*\\)' EXIT\$/\\1/p" || true)"
  trap '_kg_exit_handler' EXIT
}

run_check() {
  local name="$1"
  shift
  [[ "${1:-}" == "--" ]] && shift

  local capfile start_epoch end_epoch duration exit_code
  capfile="${_KG_TMPDIR}/cap_${#_KG_NAMES[@]}"
  start_epoch="$(date +%s)"

  log_info "run_check: $name: $*"

  if "$@" >"$capfile" 2>&1; then
    exit_code=0
  else
    exit_code=$?
  fi

  end_epoch="$(date +%s)"
  duration=$((end_epoch - start_epoch))

  _KG_NAMES+=("$name")
  _KG_STATUSES+=("$exit_code")
  _KG_DURATIONS+=("$duration")
  _KG_CAPFILES+=("$capfile")

  if [[ "$exit_code" -ne 0 ]]; then
    _KG_FAILED_COUNT=$((_KG_FAILED_COUNT + 1))
    local tail_lines="${QUALITY_HOOKS_KEEP_GOING_TAIL_LINES:-40}"
    log_warn "run_check: $name: FAILED (exit $exit_code) — last ${tail_lines} lines:"
    tail -n "$tail_lines" "$capfile" >&2 || true
  fi
}

keep_going_finalize() {
  local phase="${QUALITY_HOOKS_PHASE:-unknown}"
  printf '===== quality-hooks keep-going summary =====\n'
  local i
  for i in "${!_KG_NAMES[@]}"; do
    local label="PASS"
    [[ "${_KG_STATUSES[$i]}" -ne 0 ]] && label="FAIL"
    printf '  %-50s %s (%ds)\n' "${_KG_NAMES[$i]}" "$label" "${_KG_DURATIONS[$i]}"
  done
  if [[ "$_KG_FAILED_COUNT" -eq 0 ]]; then
    printf '===== all checks passed =====\n'
    log_metric "quality_hooks_keep_going_total" "1" "status=success phase=${phase} failed_checks=0"
    _kg_cleanup
    return 0
  else
    printf '===== %d check(s) failed =====\n' "$_KG_FAILED_COUNT"
    log_metric "quality_hooks_keep_going_total" "1" "status=failure phase=${phase} failed_checks=${_KG_FAILED_COUNT}"
    _kg_cleanup
    return 1
  fi
}
