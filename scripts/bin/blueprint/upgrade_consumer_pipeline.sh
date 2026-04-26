#!/usr/bin/env bash
# Scripted upgrade pipeline entry wrapper.
# Chains 10 deterministic stages and emits a residual report.
# See: specs/2026-04-25-scripted-upgrade-pipeline/architecture.md
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_pipeline.sh

Runs the full 10-stage scripted upgrade pipeline for a generated-consumer repository.

Environment variables:
  BLUEPRINT_UPGRADE_REF          REQUIRED: upgrade source ref (tag/branch/commit).
  BLUEPRINT_UPGRADE_SOURCE       Upgrade source repository URL/path.
                                  Default: remote.upstream.url or remote.origin.url.
  BLUEPRINT_UPGRADE_ALLOW_DELETE Default: true (pipeline default; set false for non-destructive mode).

Artifacts produced:
  artifacts/blueprint/upgrade-residual.md          — always emitted, even on partial failure.
  artifacts/blueprint/contract_resolve_decisions.json — Stage 3 contract resolution decisions.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env BLUEPRINT_UPGRADE_ALLOW_DELETE true

upgrade_ref="${BLUEPRINT_UPGRADE_REF:-}"
upgrade_source="${BLUEPRINT_UPGRADE_SOURCE:-}"
allow_delete="${BLUEPRINT_UPGRADE_ALLOW_DELETE}"

# Resolve upgrade source default (mirrors upgrade_consumer.sh resolve_default_upgrade_source).
# Applied before Stage 1 so pre-flight receives a concrete value.
if [[ -z "$upgrade_source" ]]; then
  _upstream="$(git -C "$ROOT_DIR" config --get remote.upstream.url 2>/dev/null || true)"
  if [[ -n "$_upstream" ]]; then
    upgrade_source="$_upstream"
  else
    upgrade_source="$(git -C "$ROOT_DIR" config --get remote.origin.url 2>/dev/null || true)"
  fi
  unset _upstream
fi

residual_report_path="$ROOT_DIR/artifacts/blueprint/upgrade-residual.md"
pipeline_exit=0

# Guarantee residual report is produced even on early abort.
trap 'python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_residual_report.py" \
  --repo-root "$ROOT_DIR" \
  --pipeline-exit "$pipeline_exit" \
  --output-path "$residual_report_path" \
  2>/dev/null || true' EXIT

# ---------------------------------------------------------------------------
# Stage 1 — Pre-flight validation
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 1: starting — pre-flight validation"
if ! BLUEPRINT_UPGRADE_REF="$upgrade_ref" \
     BLUEPRINT_UPGRADE_SOURCE="$upgrade_source" \
     python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_pipeline_preflight.py" \
       --repo-root "$ROOT_DIR"; then
  pipeline_exit=1
  log_fatal "[PIPELINE] Stage 1: FAILED — pre-flight checks did not pass; aborting."
fi
log_info "[PIPELINE] Stage 1: complete — pre-flight passed"

# ---------------------------------------------------------------------------
# Stage 1b — Version pin diff (non-blocking)
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 1b: starting — version pin diff"
BLUEPRINT_UPGRADE_SOURCE="$upgrade_source" \
BLUEPRINT_UPGRADE_REF="$upgrade_ref" \
python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_version_pin_diff.py" \
  --repo-root "$ROOT_DIR" || true
log_info "[PIPELINE] Stage 1b: complete"

# ---------------------------------------------------------------------------
# Stage 2 — Apply with delete
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 2: starting — apply with delete"
stage2_rc=0
BLUEPRINT_UPGRADE_ALLOW_DELETE="$allow_delete" \
  make -C "$ROOT_DIR" blueprint-upgrade-consumer-apply || stage2_rc=$?
if [[ "$stage2_rc" -gt 1 ]]; then
  # exit 0 = clean apply; exit 1 = conflicts present (expected during upgrade, Stage 3 resolves).
  # Any exit code > 1 is an unexpected error.
  pipeline_exit=$stage2_rc
  log_fatal "[PIPELINE] Stage 2: FAILED (exit $stage2_rc) — apply step encountered an error; aborting."
fi
log_info "[PIPELINE] Stage 2: complete (exit $stage2_rc)"

# ---------------------------------------------------------------------------
# Stage 3 — Contract file resolution
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 3: starting — contract file resolution"
stage3_rc=0
python3 "$ROOT_DIR/scripts/lib/blueprint/resolve_contract_upgrade.py" \
  --repo-root "$ROOT_DIR" || stage3_rc=$?
if [[ "$stage3_rc" -ne 0 ]]; then
  pipeline_exit=$stage3_rc
  log_fatal "[PIPELINE] Stage 3: FAILED — contract resolver exited $stage3_rc; aborting."
fi
log_info "[PIPELINE] Stage 3: complete"

# ---------------------------------------------------------------------------
# Stage 4 — Auto-resolve non-contract conflicts (existing apply behavior)
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 4: starting — auto-resolve non-contract conflicts"
# Handled by the existing upgrade engine during Stage 2; no new code.
log_info "[PIPELINE] Stage 4: complete"

# ---------------------------------------------------------------------------
# Stage 5 — Coverage gap detection and file fetch
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 5: starting — coverage gap detection and file fetch"
stage5_rc=0
BLUEPRINT_UPGRADE_SOURCE="$upgrade_source" \
BLUEPRINT_UPGRADE_REF="$upgrade_ref" \
python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_coverage_fetch.py" \
  --repo-root "$ROOT_DIR" || stage5_rc=$?
if [[ "$stage5_rc" -ne 0 ]]; then
  pipeline_exit=$stage5_rc
  log_fatal "[PIPELINE] Stage 5: FAILED — coverage fetch exited $stage5_rc; aborting."
fi
log_info "[PIPELINE] Stage 5: complete"

# ---------------------------------------------------------------------------
# Stage 6 — Bootstrap template mirror sync
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 6: starting — bootstrap template mirror sync"
stage6_rc=0
python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_mirror_sync.py" \
  --repo-root "$ROOT_DIR" || stage6_rc=$?
if [[ "$stage6_rc" -ne 0 ]]; then
  pipeline_exit=$stage6_rc
  log_fatal "[PIPELINE] Stage 6: FAILED — mirror sync exited $stage6_rc; aborting."
fi
log_info "[PIPELINE] Stage 6: complete"

# ---------------------------------------------------------------------------
# Stage 7 — Make target validation for new/changed docs
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 7: starting — make target validation for docs"
# Collect .md files modified in the working tree by Stages 2–6 (unstaged changes).
# Non-blocking: capture warnings but do not abort on missing targets (FR-012).
_modified_md_json="$(mktemp)"
git -C "$ROOT_DIR" status --porcelain -- '*.md' \
  | sed 's/^...//' \
  | python3 -c "import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))" \
  > "$_modified_md_json" 2>/dev/null || true
python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_doc_target_check.py" \
  --repo-root "$ROOT_DIR" \
  --modified-md-paths-json "$_modified_md_json" || true
rm -f "$_modified_md_json"
unset _modified_md_json
log_info "[PIPELINE] Stage 7: complete"

# ---------------------------------------------------------------------------
# Stage 8 — Generated reference docs regeneration
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 8: starting — generated reference docs regeneration"
stage8_rc=0
make -C "$ROOT_DIR" quality-docs-sync-core-targets quality-docs-sync-contract-metadata || stage8_rc=$?
if [[ "$stage8_rc" -ne 0 ]]; then
  pipeline_exit=$stage8_rc
  log_fatal "[PIPELINE] Stage 8: FAILED — docs regen exited $stage8_rc; aborting."
fi
log_info "[PIPELINE] Stage 8: complete"

# ---------------------------------------------------------------------------
# Stage 9 — Gate chain
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 9: starting — gate chain (infra-validate + quality-hooks-run + blueprint-upgrade-consumer-validate)"
stage9_rc=0
make -C "$ROOT_DIR" infra-validate || stage9_rc=$?
if [[ "$stage9_rc" -ne 0 ]]; then
  pipeline_exit=$stage9_rc
  log_error "[PIPELINE] Stage 9: infra-validate FAILED (exit $stage9_rc)"
else
  make -C "$ROOT_DIR" quality-hooks-run || stage9_rc=$?
  if [[ "$stage9_rc" -ne 0 ]]; then
    pipeline_exit=$stage9_rc
    log_error "[PIPELINE] Stage 9: quality-hooks-run FAILED (exit $stage9_rc)"
  else
    # Run validate to scan for prune-glob violations; result surfaces in Stage 10 residual report.
    make -C "$ROOT_DIR" blueprint-upgrade-consumer-validate || stage9_rc=$?
    if [[ "$stage9_rc" -ne 0 ]]; then
      pipeline_exit=$stage9_rc
      log_error "[PIPELINE] Stage 9: blueprint-upgrade-consumer-validate FAILED (exit $stage9_rc) — prune-glob violations or merge markers detected; see artifacts/blueprint/upgrade_validate.json"
    fi
  fi
fi
# Stage 10 (residual report) is always executed via the EXIT trap above.
log_info "[PIPELINE] Stage 9: complete (exit $stage9_rc)"

# ---------------------------------------------------------------------------
# Stage 10 is emitted by the EXIT trap — always runs.
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 10: residual report will be written on exit → $residual_report_path"

exit "$pipeline_exit"
