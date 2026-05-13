#!/usr/bin/env bash
# Post-upgrade quality convergence — sync pass (aggregated) then verify pass (fail-fast).
# Replaces the manual sequence previously documented as pipeline Stages 8+9.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_finalize.sh

Runs two deterministic passes to converge the upgrade result to a green state.

  Sync pass (aggregated failures — no fail-fast):
    1. make quality-docs-sync-all
    2. make quality-sdd-sync-consumer-init-assets
    3. make quality-sdd-sync-policy-snippets
  All sync targets always run; failures are aggregated and reported together.

  Verify pass (fail-fast on first failure):
    1. make infra-validate
    2. make quality-hooks-run
    3. make blueprint-upgrade-consumer-validate
    4. make blueprint-upgrade-consumer-postcheck
    5. make blueprint-upgrade-fresh-env-gate
  The first failing verify target causes finalize to exit non-zero immediately
  with a summary banner naming the failing target and its exit code.

Precondition: Stages 3–7 of the upgrade pipeline must have already run (the
sync and verify steps depend on artifacts produced by those stages).

Idempotent: a second invocation after a clean first pass produces no file
changes and exits 0.

Environment variables forwarded to verify targets:
  BLUEPRINT_UPGRADE_SOURCE   Upgrade source URL/path (required by postcheck and gate).
  BLUEPRINT_UPGRADE_REF      Upgrade ref (required by postcheck and gate).
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command make

# ---------------------------------------------------------------------------
# Sync pass — aggregated failures, no fail-fast (FR-006, AC-003)
# ---------------------------------------------------------------------------
sync_errors=0

log_info "[finalize] sync: quality-docs-sync-all: starting"
if make -C "$ROOT_DIR" quality-docs-sync-all; then
  log_info "[finalize] sync: quality-docs-sync-all: OK"
else
  log_error "[finalize] sync: quality-docs-sync-all: FAILED"
  sync_errors=$(( sync_errors + 1 ))
fi

log_info "[finalize] sync: quality-sdd-sync-consumer-init-assets: starting"
if make -C "$ROOT_DIR" quality-sdd-sync-consumer-init-assets; then
  log_info "[finalize] sync: quality-sdd-sync-consumer-init-assets: OK"
else
  log_error "[finalize] sync: quality-sdd-sync-consumer-init-assets: FAILED"
  sync_errors=$(( sync_errors + 1 ))
fi

log_info "[finalize] sync: quality-sdd-sync-policy-snippets: starting"
if make -C "$ROOT_DIR" quality-sdd-sync-policy-snippets; then
  log_info "[finalize] sync: quality-sdd-sync-policy-snippets: OK"
else
  log_error "[finalize] sync: quality-sdd-sync-policy-snippets: FAILED"
  sync_errors=$(( sync_errors + 1 ))
fi

if [[ "$sync_errors" -gt 0 ]]; then
  log_error "[finalize] sync pass: $sync_errors target(s) FAILED — fix the above errors before the verify pass will succeed."
  exit 1
fi
log_info "[finalize] sync pass: all targets OK"

# ---------------------------------------------------------------------------
# Verify pass — fail-fast on first failure with summary banner (FR-007, AC-004)
# ---------------------------------------------------------------------------
_finalize_verify() {
  local target="$1"
  local rc=0
  log_info "[finalize] verify: $target: starting"
  make -C "$ROOT_DIR" "$target" || rc=$?
  if [[ "$rc" -ne 0 ]]; then
    log_error "[finalize] verify: $target: FAILED (exit $rc) — finalize aborted."
    exit "$rc"
  fi
  log_info "[finalize] verify: $target: OK"
}

_finalize_verify infra-validate
_finalize_verify quality-hooks-run
_finalize_verify blueprint-upgrade-consumer-validate
_finalize_verify blueprint-upgrade-consumer-postcheck
_finalize_verify blueprint-upgrade-fresh-env-gate

log_info "[finalize] verify pass: all targets OK"
log_info "[finalize] complete — upgrade converged to green state."
