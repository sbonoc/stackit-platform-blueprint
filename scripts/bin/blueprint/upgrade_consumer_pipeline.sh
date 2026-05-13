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
                                  URL form (https://, git@, ssh://): the pipeline performs
                                  an auto-clone (--depth 1) to a tmp dir before Stage 1b
                                  and removes the clone on exit via an EXIT trap.
                                  Local path form (/…, ./…, ../…): used as-is; no clone.
  BLUEPRINT_UPGRADE_ALLOW_DELETE Default: true (pipeline default; set false for non-destructive mode).
  BLUEPRINT_UPGRADE_APPLY        Default: true (pipeline default; set false for plan-only/dry-run mode).

Artifacts produced:
  artifacts/blueprint/upgrade-residual.md          — always emitted, even on partial failure.
  artifacts/blueprint/contract_resolve_decisions.json — Stage 3 contract resolution decisions.
  artifacts/blueprint/upgrade_triage.json          — emitted by Stage 2 when conflict_count > 0;
                                                     contains recommended_action per conflict.

Post-pipeline step (when conflicts exist):
  make blueprint-upgrade-consumer-resolve          — auto-applies take_source/take_target rows and
                                                     prints a residual table of human_required rows.

Post-Stage-2 convergence:
  make blueprint-upgrade-consumer-finalize         — single canonical command to sync and verify
                                                     the upgrade result (replaces manual Stage 8+9).
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env BLUEPRINT_UPGRADE_ALLOW_DELETE true
set_default_env BLUEPRINT_UPGRADE_APPLY true

upgrade_ref="${BLUEPRINT_UPGRADE_REF:-}"
upgrade_source="${BLUEPRINT_UPGRADE_SOURCE:-}"
allow_delete="${BLUEPRINT_UPGRADE_ALLOW_DELETE}"
allow_apply="${BLUEPRINT_UPGRADE_APPLY}"

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
cloned_source_dir=""

# Guarantee residual report is produced and tmp clone dir is removed on all exit paths.
# cloned_source_dir is populated by the URL normalization block below when a clone is needed.
# _real_exit captures $? at trap time so unanticipated set -e exits are not reported as 0.
trap '_real_exit=$?; [[ "$pipeline_exit" -ne 0 ]] || pipeline_exit=$_real_exit; \
  [[ -n "$cloned_source_dir" ]] && rm -rf "$cloned_source_dir"; \
  uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_residual_report.py" \
  --repo-root "$ROOT_DIR" \
  --pipeline-exit "$pipeline_exit" \
  --output-path "$residual_report_path" \
  2>/dev/null || true' EXIT

# ---------------------------------------------------------------------------
# URL normalization — auto-clone URL-form upgrade_source to a local path.
# Runs before Stage 1 so all stages receive a local filesystem path.
# FR-001, FR-002, FR-004, NFR-REL-001, NFR-SEC-001.
# ---------------------------------------------------------------------------
if [[ -n "$upgrade_source" ]] && ! [[ -d "$upgrade_source/.git" ]]; then
  case "$upgrade_source" in
    https://*|git@*|ssh://*)
      cloned_source_dir="$(mktemp -d -t blueprint-upgrade-source-XXXXXX)"
      log_info "[PIPELINE] auto-clone: cloning $upgrade_source@$upgrade_ref → $cloned_source_dir (--depth 1)"
      if ! git clone --quiet --depth 1 --branch "$upgrade_ref" "$upgrade_source" "$cloned_source_dir"; then
        log_fatal "[PIPELINE] auto-clone: git clone failed for $upgrade_source — check that BLUEPRINT_UPGRADE_REF='$upgrade_ref' exists in the remote."
      fi
      upgrade_source="$cloned_source_dir"
      log_info "[PIPELINE] auto-clone: complete — upgrade_source reassigned to local clone"
      ;;
    /*|./*|../*)
      ;;
    *)
      log_fatal "[PIPELINE] auto-clone: BLUEPRINT_UPGRADE_SOURCE='$upgrade_source' is not a recognised form. Use https://, git@, ssh://, or a local path (/, ./, ../)."
      ;;
  esac
fi

if [[ "$allow_apply" != "true" ]]; then
  log_info "[PIPELINE] PLAN-ONLY mode: BLUEPRINT_UPGRADE_APPLY=false — stages will plan but not write files."
fi

# ---------------------------------------------------------------------------
# Stage 1 — Pre-flight validation
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 1: starting — pre-flight validation"
if ! BLUEPRINT_UPGRADE_REF="$upgrade_ref" \
     BLUEPRINT_UPGRADE_SOURCE="$upgrade_source" \
     uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_pipeline_preflight.py" \
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
uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_version_pin_diff.py" \
  --repo-root "$ROOT_DIR" || true
log_info "[PIPELINE] Stage 1b: complete"

# ---------------------------------------------------------------------------
# Stage 2 — Apply with delete
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 2: starting — apply"
stage2_rc=0
BLUEPRINT_UPGRADE_ALLOW_DELETE="$allow_delete" \
BLUEPRINT_UPGRADE_APPLY="$allow_apply" \
  make -C "$ROOT_DIR" blueprint-upgrade-consumer-apply || stage2_rc=$?
if [[ "$stage2_rc" -ne 0 ]]; then
  # Engine exits 0 for both clean apply and conflicts (status='conflicts' in artifact).
  # Any non-zero exit is an unexpected error — abort the pipeline.
  pipeline_exit=$stage2_rc
  log_fatal "[PIPELINE] Stage 2: FAILED (exit $stage2_rc) — apply step encountered an error; aborting."
fi
apply_artifact="$ROOT_DIR/artifacts/blueprint/upgrade_apply.json"
# stage2_status is observability only — the pipeline continues through resolution stages
# regardless of "conflicts" vs "success"; only a non-zero exit above aborts.
stage2_status=""
if [[ -f "$apply_artifact" ]]; then
  stage2_status="$(uv run python3 -c "import json,sys; d=json.load(open('$apply_artifact')); print(d.get('status',''))" 2>/dev/null || true)"
fi
log_info "[PIPELINE] Stage 2: complete (status=${stage2_status:-unknown})"

# ---------------------------------------------------------------------------
# Stage 3 — Contract file resolution
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 3: starting — contract file resolution"
stage3_rc=0
uv run python3 "$ROOT_DIR/scripts/lib/blueprint/resolve_contract_upgrade.py" \
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
uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_coverage_fetch.py" \
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
uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_mirror_sync.py" \
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
uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_doc_target_check.py" \
  --repo-root "$ROOT_DIR" \
  --modified-md-paths-json "$_modified_md_json" || true
rm -f "$_modified_md_json"
unset _modified_md_json
log_info "[PIPELINE] Stage 7: complete"

# ---------------------------------------------------------------------------
# Stages 8+9 — Post-apply quality convergence (delegated to finalize target)
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stages 8+9: starting — post-apply quality convergence (finalize)"
make -C "$ROOT_DIR" blueprint-upgrade-consumer-finalize || pipeline_exit=$?
if [[ "$pipeline_exit" -ne 0 ]]; then
  log_error "[PIPELINE] Stages 8+9: blueprint-upgrade-consumer-finalize FAILED (exit $pipeline_exit)"
else
  log_info "[PIPELINE] Stages 8+9: complete — finalize passed"
fi
# Stage 10 (residual report) is always executed via the EXIT trap above.

# ---------------------------------------------------------------------------
# Stage 10 is emitted by the EXIT trap — always runs.
# ---------------------------------------------------------------------------
log_info "[PIPELINE] Stage 10: residual report will be written on exit → $residual_report_path"

exit "$pipeline_exit"
