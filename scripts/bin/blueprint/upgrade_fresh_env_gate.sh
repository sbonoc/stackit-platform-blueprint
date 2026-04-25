#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_upgrade_fresh_env_gate"

usage() {
  cat <<'USAGE'
Usage: upgrade_fresh_env_gate.sh

Run the fresh-environment smoke gate after blueprint consumer upgrade.

The gate creates a temporary git worktree from the current HEAD of the consumer
upgrade branch, runs make infra-validate and make blueprint-upgrade-consumer-postcheck
inside that clean worktree, then diffs the resulting file state against the working
tree to surface CI-equivalent failures before the PR is opened.

A gate failure means CI would see a different result from the local upgrade run.
The worktree is unconditionally removed on exit (pass, fail, or interrupt).

Environment variables:
  BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH   Default: artifacts/blueprint/fresh_env_gate.json
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
require_command make
require_command git

set_default_env BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH "artifacts/blueprint/fresh_env_gate.json"

gate_report_path="$BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH"
consumer_root="$(pwd)"
worktree_path=""
worktree_created=false

# ---------------------------------------------------------------------------
# EXIT trap — unconditionally remove the temporary worktree
# ---------------------------------------------------------------------------
_cleanup_worktree() {
  if [[ "$worktree_created" == "true" && -n "$worktree_path" ]]; then
    git -C "$consumer_root" worktree remove --force "$worktree_path" 2>/dev/null || true
  fi
  # Belt-and-suspenders: remove the directory if it still exists
  if [[ -n "$worktree_path" && -d "$worktree_path" ]]; then
    rm -rf "$worktree_path" 2>/dev/null || true
  fi
}
trap _cleanup_worktree EXIT

# ---------------------------------------------------------------------------
# Helper: write the gate JSON report via the Python module
# ---------------------------------------------------------------------------
_write_report() {
  local status="$1"
  local exit_code="$2"
  local error_msg="${3:-}"

  local report_args=(
    --worktree-path "$worktree_path"
    --working-tree-path "$consumer_root"
    --output-path "$gate_report_path"
    --status "$status"
    --targets-run "make infra-validate"
    --targets-run "make blueprint-upgrade-consumer-postcheck"
    --exit-code "$exit_code"
  )
  if [[ -n "$error_msg" ]]; then
    report_args+=(--error "$error_msg")
  fi

  python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_fresh_env_gate.py" "${report_args[@]}" || true
}

# ---------------------------------------------------------------------------
# Create temporary worktree
# ---------------------------------------------------------------------------
worktree_path="$(mktemp -d)"

log_info "fresh-env gate: creating temporary worktree at ${worktree_path}"

worktree_create_rc=0
if ! git -C "$consumer_root" worktree add "$worktree_path" HEAD 2>&1; then
  worktree_create_rc=1
fi

if [[ "$worktree_create_rc" -ne 0 ]]; then
  log_error "fresh-env gate: worktree creation failed — gate cannot run"
  _write_report "error" 1 "worktree creation failed"
  log_metric "blueprint_upgrade_fresh_env_gate_status_total" "1" "status=error"
  exit 1
fi

worktree_created=true

# ---------------------------------------------------------------------------
# Seed upgrade artifacts into the worktree (gitignored files absent by design)
# ---------------------------------------------------------------------------
if [[ -d "$consumer_root/artifacts/blueprint" ]]; then
  log_info "fresh-env gate: seeding blueprint upgrade artifacts into worktree from ${consumer_root}/artifacts/blueprint"
  mkdir -p "$worktree_path/artifacts"
  cp -r "$consumer_root/artifacts/blueprint" "$worktree_path/artifacts/"
else
  log_info "fresh-env gate: artifacts/blueprint not found in working tree — skipping artifact seeding"
fi

# ---------------------------------------------------------------------------
# Run targets inside the clean worktree
# ---------------------------------------------------------------------------
gate_exit_code=0

log_info "fresh-env gate: running make infra-validate in clean worktree"
if run_cmd make -C "$worktree_path" infra-validate; then
  infra_validate_rc=0
else
  infra_validate_rc=$?
fi

if [[ "$infra_validate_rc" -ne 0 ]]; then
  gate_exit_code="$infra_validate_rc"
  log_error "fresh-env gate: make infra-validate failed in clean worktree (exit ${infra_validate_rc})"
else
  log_info "fresh-env gate: running make blueprint-upgrade-consumer-postcheck in clean worktree"
  if run_cmd make -C "$worktree_path" blueprint-upgrade-consumer-postcheck; then
    postcheck_rc=0
  else
    postcheck_rc=$?
  fi

  if [[ "$postcheck_rc" -ne 0 ]]; then
    gate_exit_code="$postcheck_rc"
    log_error "fresh-env gate: make blueprint-upgrade-consumer-postcheck failed in clean worktree (exit ${postcheck_rc})"
  fi
fi

# ---------------------------------------------------------------------------
# Determine status, write report, emit metric
# ---------------------------------------------------------------------------
if [[ "$gate_exit_code" -eq 0 ]]; then
  gate_status="pass"
else
  gate_status="fail"
  log_error "fresh-env gate: FAIL — make targets failed; check divergences in ${gate_report_path}"
fi

_write_report "$gate_status" "$gate_exit_code"

# FR-014: re-read the effective status from the written report — the Python module may
# have upgraded "pass" to "fail" when artifact checksum divergences were detected even
# though both make targets exited 0.
_resolved_report_path="$consumer_root/$gate_report_path"
if [[ "$gate_report_path" == /* ]]; then
  _resolved_report_path="$gate_report_path"
fi
if [[ -f "$_resolved_report_path" ]]; then
  effective_status="$(python3 -c "import json; print(json.load(open('$_resolved_report_path'))['status'])" 2>/dev/null || echo "$gate_status")"
  if [[ "$effective_status" != "$gate_status" ]]; then
    gate_status="$effective_status"
    gate_exit_code=1
  fi
fi

if [[ "$gate_status" == "pass" ]]; then
  log_info "fresh-env gate: PASS — upgrade is CI-equivalent"
else
  log_error "fresh-env gate: FAIL — CI would see a different result; check divergences in ${gate_report_path}"
fi

log_metric "blueprint_upgrade_fresh_env_gate_status_total" "1" "status=${gate_status}"

exit "$gate_exit_code"
