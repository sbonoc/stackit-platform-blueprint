#!/usr/bin/env bash
# add_deferred_triggers.sh — idempotent helper that appends two
# AGENTS.backlog.md entries so #361.3 filing surfaces mechanically when its
# blockers (#335 + #336 spec-complete) resolve.
#
# ## Lifecycle (per parent spec FR-016)
# This script is single-purpose ephemera. It serves its function at parent
# #361 PR merge (when the operator runs it once) and has zero residual value
# thereafter. #361.3 (the canonically last-merging child) MUST include
# `git rm` of this file in its own PR scope. Verified by AC-012 / T-211.
# Do NOT extend this script for future decomposed parents — author a
# parent-specific helper alongside that parent's spec instead.
#
# Per Q-1 (Option B): #361.3 is deferred from file_children.sh and surfaces
# via the backlog after-trigger convention defined in AGENTS.backlog.md.
#
# Idempotency: each entry is matched by a unique grep token before append.
# Re-runs append zero duplicates.
#
# Invocation:
#   bash specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh
#
# Environment overrides (intended for the pytest test only):
#   BACKLOG_FILE=/path/to/AGENTS.backlog.md  override target file
#
# Exit codes:
#   0  on success (any combination of appended and skipped entries)
#   2  on a missing backlog file
set -euo pipefail

BACKLOG_FILE="${BACKLOG_FILE:-AGENTS.backlog.md}"
PARENT_SPEC_PATH="${PARENT_SPEC_PATH:-specs/2026-06-18-issue-361-orchestrator-service/}"

if [[ ! -f "$BACKLOG_FILE" ]]; then
  printf 'error: backlog file not found: %s\n' "$BACKLOG_FILE" >&2
  exit 2
fi

ENTRY_335_TOKEN='proposal(issue-361-orchestrator-service): file #361.3 — RabbitMQ subscriber + OpenHands API client + work loop (trigger: after: issue-335)'
ENTRY_336_TOKEN='proposal(issue-361-orchestrator-service): file #361.3 — RabbitMQ subscriber + OpenHands API client + work loop (trigger: after: issue-336)'

entry_335() {
  cat <<EOF

- [ ] (parked) proposal(issue-361-orchestrator-service): file #361.3 — RabbitMQ subscriber + OpenHands API client + work loop (trigger: after: issue-335)
      trigger: after: issue-335
      rationale: #361.3 is the layer — external-runtime clients boundary of the #361 5-child decomposition. Filing deferred per Q-1 (Option B) until #335 reaches spec-complete so the runtime-client child's API contracts are concrete. Parent spec: ${PARENT_SPEC_PATH}. When filing, the #361.3 body MUST cite parent spec FR-016 — the PR scope MUST include \`git rm\` of \`${PARENT_SPEC_PATH}file_children.sh\` and \`${PARENT_SPEC_PATH}add_deferred_triggers.sh\` (verified by AC-012 / T-211 to be authored in #361.3).
EOF
}

entry_336() {
  cat <<EOF

- [ ] (parked) proposal(issue-361-orchestrator-service): file #361.3 — RabbitMQ subscriber + OpenHands API client + work loop (trigger: after: issue-336)
      trigger: after: issue-336
      rationale: #361.3 is the layer — external-runtime clients boundary of the #361 5-child decomposition. Filing deferred per Q-1 (Option B) until #336 reaches spec-complete so the RabbitMQ trigger queue topology is concrete. Parent spec: ${PARENT_SPEC_PATH}. When filing, the #361.3 body MUST cite parent spec FR-016 — the PR scope MUST include \`git rm\` of \`${PARENT_SPEC_PATH}file_children.sh\` and \`${PARENT_SPEC_PATH}add_deferred_triggers.sh\` (verified by AC-012 / T-211 to be authored in #361.3).
EOF
}

append_if_absent() {
  local token="$1"
  local entry="$2"
  if grep -Fq "$token" "$BACKLOG_FILE"; then
    printf 'skip: backlog entry already present (token match: %s)\n' "$token" >&2
    return 0
  fi
  printf '%s' "$entry" >> "$BACKLOG_FILE"
}

main() {
  append_if_absent "$ENTRY_335_TOKEN" "$(entry_335)"
  append_if_absent "$ENTRY_336_TOKEN" "$(entry_336)"
}

main "$@"
