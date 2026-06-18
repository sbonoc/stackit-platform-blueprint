#!/usr/bin/env bash
# add_deferred_triggers.sh — idempotent helper that injects two
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
# ## Injection convention (per AGENTS.backlog.md "## Parked Proposals" structure)
# Each entry MUST land beneath its matching `### after: issue-NNN` subsection
# header. If the header exists, append the entry under it (before the next
# header). If the header does not exist, create it just before the
# `## Long Horizon` section (or end-of-file if that section is absent).
#
# Per Q-1 (Option B): #361.3 is deferred from file_children.sh and surfaces
# via the backlog after-trigger convention defined in AGENTS.backlog.md.
#
# Idempotency: each entry is matched by a unique grep token before injection.
# Re-runs append zero duplicates.
#
# Invocation:
#   bash specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh
#
# Environment overrides (intended for the pytest test only):
#   BACKLOG_FILE=/path/to/AGENTS.backlog.md  override target file
#
# Exit codes:
#   0  on success (any combination of injected and skipped entries)
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
      rationale: #361.3 is the layer — external-runtime clients boundary of the #361 5-child decomposition. Filing deferred per Q-1 (Option B) until #335 reaches spec-complete so the runtime-client child's API contracts are concrete. Parent spec: ${PARENT_SPEC_PATH}. When filing, the #361.3 body MUST cite parent spec FR-016 — the PR scope MUST include \`git rm\` of \`${PARENT_SPEC_PATH}file_children.sh\` and \`${PARENT_SPEC_PATH}add_deferred_triggers.sh\` (verified by AC-012 / T-211 to be authored in #361.3). Per parent spec FR-017, the #361.3 PR body MUST cite parent #361 as \`Tracks #361\` (informational); GitHub auto-close keywords (\`Closes\` / \`Fixes\` / \`Resolves\`) MUST NOT target #361. Parent close is a deliberate human action after the Contract C4 Integration AC checkboxes are ticked.
EOF
}

entry_336() {
  cat <<EOF

- [ ] (parked) proposal(issue-361-orchestrator-service): file #361.3 — RabbitMQ subscriber + OpenHands API client + work loop (trigger: after: issue-336)
      trigger: after: issue-336
      rationale: #361.3 is the layer — external-runtime clients boundary of the #361 5-child decomposition. Filing deferred per Q-1 (Option B) until #336 reaches spec-complete so the RabbitMQ trigger queue topology is concrete. Parent spec: ${PARENT_SPEC_PATH}. When filing, the #361.3 body MUST cite parent spec FR-016 — the PR scope MUST include \`git rm\` of \`${PARENT_SPEC_PATH}file_children.sh\` and \`${PARENT_SPEC_PATH}add_deferred_triggers.sh\` (verified by AC-012 / T-211 to be authored in #361.3). Per parent spec FR-017, the #361.3 PR body MUST cite parent #361 as \`Tracks #361\` (informational); GitHub auto-close keywords (\`Closes\` / \`Fixes\` / \`Resolves\`) MUST NOT target #361. Parent close is a deliberate human action after the Contract C4 Integration AC checkboxes are ticked.
EOF
}

# inject_into_section <section_header> <entry_text> <token>
#
# Idempotent injection algorithm (single-pass awk):
#   1. If `token` is already anywhere in the file, no-op (skip with stderr note).
#   2. If `section_header` exists: insert `entry_text` immediately after the
#      LAST line of the existing section (i.e., before the next `### ` header,
#      `## ` header, or EOF — whichever comes first).
#   3. If `section_header` is absent: create it immediately before the
#      `## Long Horizon` header. If that header is also absent, append at EOF.
inject_into_section() {
  local section_header="$1"
  local entry_text="$2"
  local token="$3"

  if grep -Fq "$token" "$BACKLOG_FILE"; then
    printf 'skip: backlog entry already present (token match: %s)\n' "$token" >&2
    return 0
  fi

  local tmpfile
  tmpfile="$(mktemp)"

  ENTRY="$entry_text" SECTION="$section_header" awk '
    BEGIN {
      section_seen = 0
      in_section = 0
      printed_entry = 0
      section_header = ENVIRON["SECTION"]
      entry_text = ENVIRON["ENTRY"]
    }
    {
      # Detect entry into our target section.
      if ($0 == section_header) {
        section_seen = 1
        in_section = 1
        print
        next
      }
      # While inside our section, look for the next ### / ## boundary.
      if (in_section && ($0 ~ /^### / || $0 ~ /^## / || $0 ~ /^---/)) {
        # End of section reached. Inject entry just before this line.
        print entry_text
        printed_entry = 1
        in_section = 0
        print
        next
      }
      # If section not yet seen, look for Long Horizon header so we can
      # create our own section just before it.
      if (!section_seen && !printed_entry && $0 == "## Long Horizon") {
        print section_header
        print entry_text
        printed_entry = 1
        print
        next
      }
      print
    }
    END {
      # If we entered the section and hit EOF without seeing a boundary, the
      # section ran all the way to end-of-file. Inject now.
      if (in_section && !printed_entry) {
        print entry_text
        printed_entry = 1
      }
      # If we never saw the section header AND never saw ## Long Horizon,
      # create the section at EOF as a last resort.
      if (!printed_entry) {
        print ""
        print section_header
        print entry_text
      }
    }
  ' "$BACKLOG_FILE" > "$tmpfile"

  mv "$tmpfile" "$BACKLOG_FILE"
}

main() {
  inject_into_section '### after: issue-335' "$(entry_335)" "$ENTRY_335_TOKEN"
  inject_into_section '### after: issue-336' "$(entry_336)" "$ENTRY_336_TOKEN"
}

main "$@"
