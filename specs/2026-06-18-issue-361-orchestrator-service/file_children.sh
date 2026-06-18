#!/usr/bin/env bash
# file_children.sh — idempotent helper that files 4 of the 5 child GitHub
# issues declared by FR-001 of the parent #361 spec.
#
# ## Lifecycle (per parent spec FR-016)
# This script is single-purpose ephemera. It serves its function at parent
# #361 PR merge (when the operator runs it once) and has zero residual value
# thereafter. #361.3 (the canonically last-merging child) MUST include
# `git rm` of this file in its own PR scope. Verified by AC-012 / T-211.
# Do NOT extend this script for future decomposed parents — author a
# parent-specific helper alongside that parent's spec instead.
#
# Per Q-1 (Option B): #361.3 is NOT filed here — it is deferred until #335 and
# #336 reach spec-complete. The companion script add_deferred_triggers.sh
# appends AGENTS.backlog.md entries that surface #361.3 filing mechanically
# when those blockers resolve.
#
# Idempotency: each child is identified by a canonical title prefix. Before
# creating an issue, the script searches existing open issues by exact title
# match. Re-runs file zero duplicates.
#
# Invocation:
#   bash specs/2026-06-18-issue-361-orchestrator-service/file_children.sh
#
# Environment overrides (intended for the pytest test only):
#   GH_BIN=/path/to/gh-stub   override gh binary
#   PARENT_SPEC_PATH=...      override parent spec path cited in bodies
#
# Exit codes:
#   0  on success (any combination of created and skipped children)
#   2  on a gh CLI error
set -euo pipefail

GH_BIN="${GH_BIN:-gh}"
PARENT_SPEC_PATH="${PARENT_SPEC_PATH:-specs/2026-06-18-issue-361-orchestrator-service/}"

LABELS="agent-ready,enhancement,infrastructure,priority:p1"

child_title() {
  local slug="$1"
  local scope="$2"
  printf 'feat(orchestrator): %s (Child %s of #361)' "$scope" "$slug"
}

issue_exists() {
  local title="$1"
  # gh issue list returns matching titles; use --search to scope by title.
  # We compare exact title equality because --search is fuzzy.
  "$GH_BIN" issue list \
    --state open \
    --search "in:title \"$title\"" \
    --json title \
    --jq '.[].title' 2>/dev/null \
    | grep -Fxq "$title"
}

file_child() {
  local slug="$1"
  local scope="$2"
  local body="$3"
  local title
  title="$(child_title "$slug" "$scope")"
  if issue_exists "$title"; then
    printf 'skip: child %s already filed (title match)\n' "$slug" >&2
    return 0
  fi
  "$GH_BIN" issue create \
    --title "$title" \
    --body "$body" \
    --label "$LABELS"
}

body_361_1() {
  cat <<EOF
**Parent:** #361 — orchestrator service coordination spec at \`${PARENT_SPEC_PATH}\`.
**Boundary type:** layer — pure-Python core (no I/O).
**FR range owned:** FR-002 (dispatch matrix loader), FR-003 (convergence engine — 3 modes), FR-004 (schema validator), FR-012 (predicate-registry mechanism only — first predicate ships in #361.5).

## Scope

Pure-Python core for the orchestrator. Zero I/O. See the parent spec FRs listed above for the normative contract.

## Blocked by

None — #360 closed 2026-06-03, so the \`## Required Output Schema\` jsonschema blocks the schema validator parses already exist.

## Notes for intake

Per parent spec § Notes for Child Intake: this child's predicate-registry mechanism MUST be exercised with fixture predicates (e.g., \`always_true\`, \`always_false\`) in this child's own test suite. Do NOT reach into #361.5 mid-implementation for the first real predicate — the dependency direction is #361.5 → #361.1, not the reverse.

## Closing

Per parent spec FR-017: the PR body for this child MUST cite parent #361 as \`Tracks #361\` (informational). It MUST NOT use any GitHub auto-close keyword targeting #361 (\`Closes\` / \`Fixes\` / \`Resolves\` / etc.). Parent close is a deliberate human action after all 5 children merge AND the Contract C4 Integration AC checkboxes are ticked — never a side-effect of a child PR merge.
EOF
}

body_361_2() {
  cat <<EOF
**Parent:** #361 — orchestrator service coordination spec at \`${PARENT_SPEC_PATH}\`.
**Boundary type:** layer — emission and bus integration.
**FR range owned:** FR-005 (C7 emitter + deterministic event_id), FR-006 (additive extension fields: expert_verdicts / routing_keys / token_usage / merger_overhead / ticket_token_summary), FR-007 (reviewer-rotation picker reading prior phase: implement event).

## Scope

C7 event envelope construction, durable-bus publisher (RabbitMQ AMQP), reviewer-rotation picker, per-ticket token accumulator. See the parent spec FRs listed above for the normative contract.

## Blocked by

- #361.1 — depends on the pure-Python core for the schema-validated payload shapes the emitter wraps.

## Notes for intake

The reviewer-rotation picker reads from the bus (queries prior \`phase: implement\` event) but the read shape is tightly coupled to the write shape (both reference \`event_id\` derivation, both filter by \`phase\`). Keep both in this child; do not extract the read adapter to #361.1 unless a second consumer of bus-reads appears.

## Closing

Per parent spec FR-017: the PR body for this child MUST cite parent #361 as \`Tracks #361\` (informational). It MUST NOT use any GitHub auto-close keyword targeting #361 (\`Closes\` / \`Fixes\` / \`Resolves\` / etc.). Parent close is a deliberate human action after all 5 children merge AND the Contract C4 Integration AC checkboxes are ticked — never a side-effect of a child PR merge.
EOF
}

body_361_4() {
  cat <<EOF
**Parent:** #361 — orchestrator service coordination spec at \`${PARENT_SPEC_PATH}\`.
**Boundary type:** feature — deployment surface.
**FR range owned:** FR-009 (ESO-mounted credentials, no env-var injection), FR-010 (reusable Helm chart at \`scripts/templates/infra/orchestrator/\` + Contract C8 row), FR-011 (egress NetworkPolicy), NFR-SEC-001 (non-root distroless + read-only root filesystem), NFR-OPS-001 (single-replica Deployment + probes).

## Scope

Helm chart, NetworkPolicy, ESO ExternalSecret wiring, ServiceAccount. Reviewers: Security + Operations.

## Blocked by

- #361.1 — depends on the pure-Python core that the chart's runtime image bundles.
- #361.2 — depends on the emission + bus integration that the chart's runtime image bundles.
- **#334 spec-complete** — depends on the factory bot identity + ESO ClusterSecretStore wiring.

## Notes for intake

ESO chart shape locked at parent intake (Q-4 Option A): one \`eso.clusterSecretStoreRef\` plus three independent \`eso.secretKeyRef.{bus,openhands,litellm}\` mounted at \`/var/run/secrets/orchestrator/{bus,openhands,litellm}\`.

## Closing

Per parent spec FR-017: the PR body for this child MUST cite parent #361 as \`Tracks #361\` (informational). It MUST NOT use any GitHub auto-close keyword targeting #361 (\`Closes\` / \`Fixes\` / \`Resolves\` / etc.). Parent close is a deliberate human action after all 5 children merge AND the Contract C4 Integration AC checkboxes are ticked — never a side-effect of a child PR merge.
EOF
}

body_361_5() {
  cat <<EOF
**Parent:** #361 — orchestrator service coordination spec at \`${PARENT_SPEC_PATH}\`.
**Boundary type:** governance-docs — expert-panel roster addition.
**FR range owned:** FR-012 (PERSONA.md + C3 matrix wiring + #369 closure — the predicate-registry mechanism itself is in #361.1).

## Scope

\`.agents/personas/ux-ui-designer/PERSONA.md\` (6-section template per ADR-issue-364 § 3); C3 matrix wiring at step01/04/05/08 gated by the FR-012 \`has-user-facing-flow\` predicate; \`AGENTS.backlog.md\` #369 entry marked \`(incorporated: issue-361.5)\`; architecture-sign-off exception to ADR-issue-364 expert-ceiling-of-8.

## Blocked by

- #361.1 — depends on the predicate-registry mechanism the matrix row references.

## Notes for intake

Per parent spec § Notes for Child Intake: the 9-vs-8 expert-ceiling exception MUST be authored as an ADR amendment, NOT informal PERSONA.md front-matter prose. Choose EXACTLY ONE OF: (a) a \`Status: amended\` note on \`ADR-issue-364-expert-persona-model.md\` with an Amendments section, OR (b) a new narrowly-scoped \`ADR-issue-361.5-ux-ui-designer-ceiling-exception.md\`. The PERSONA.md front-matter cites the chosen ADR by path; the ADR carries the normative rationale.

Reviewers: Architecture + Product.

## Closing

Per parent spec FR-017: the PR body for this child MUST cite parent #361 as \`Tracks #361\` (informational). It MUST NOT use any GitHub auto-close keyword targeting #361 (\`Closes\` / \`Fixes\` / \`Resolves\` / etc.). Parent close is a deliberate human action after all 5 children merge AND the Contract C4 Integration AC checkboxes are ticked — never a side-effect of a child PR merge.

The single permitted auto-close keyword on this child PR body is \`Closes #369\` — a different issue (the ux-ui-designer expert addition) that this child legitimately resolves.
EOF
}

main() {
  file_child '1' 'dispatch matrix loader + convergence engine + schema validator + predicate-registry mechanism' "$(body_361_1)"
  file_child '2' 'C7 emitter + bus publisher + reviewer-rotation picker' "$(body_361_2)"
  file_child '4' 'Helm chart + NetworkPolicy + ESO + ServiceAccount' "$(body_361_4)"
  file_child '5' 'ux-ui-designer PERSONA.md + C3 matrix wiring + #369 closure' "$(body_361_5)"
}

main "$@"
