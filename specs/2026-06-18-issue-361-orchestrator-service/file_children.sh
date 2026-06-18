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
EXPECTED_REPO="${EXPECTED_REPO:-sbonoc/stackit-platform-blueprint}"

LABELS="agent-ready,enhancement,infrastructure,priority:p1"

# Precondition checks — fail fast with clear stderr so the operator does not
# silently file issues into the wrong repo or rely on swallowed gh failures.
check_preconditions() {
  # gh CLI present
  if ! command -v "$GH_BIN" >/dev/null 2>&1; then
    printf 'error: gh CLI not found on PATH (GH_BIN=%s)\n' "$GH_BIN" >&2
    exit 2
  fi
  # gh authenticated against the expected repo's host
  if ! "$GH_BIN" auth status >/dev/null 2>&1; then
    printf 'error: gh CLI is not authenticated. Run `gh auth login` first.\n' >&2
    exit 2
  fi
  # Working directory resolves to the expected repo. Bypass with PRECHECK_SKIP_REPO=1
  # ONLY for the pytest stub harness (which has no real git repo context).
  if [[ "${PRECHECK_SKIP_REPO:-0}" != "1" ]]; then
    local actual_repo
    actual_repo="$("$GH_BIN" repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)"
    if [[ -z "$actual_repo" ]]; then
      printf 'error: gh could not resolve the current repo. Run from a clone of %s.\n' "$EXPECTED_REPO" >&2
      exit 2
    fi
    if [[ "$actual_repo" != "$EXPECTED_REPO" ]]; then
      printf 'error: gh resolves to repo %s but EXPECTED_REPO=%s. Refusing to file issues in the wrong repo.\n' "$actual_repo" "$EXPECTED_REPO" >&2
      exit 2
    fi
  fi
}

child_title() {
  local slug="$1"
  local scope="$2"
  printf 'feat(orchestrator): %s (Child %s of #361)' "$scope" "$slug"
}

# issue_exists returns:
#   0 — issue with the exact title is present (skip create)
#   1 — issue is absent (proceed to create)
#   2 — gh issue list itself FAILED (do NOT proceed; the script exits 2 below)
# Crucial: gh-list-failure MUST NOT be conflated with issue-absent. The
# previous implementation swallowed `2>/dev/null` and treated any failure
# as "absent", which silently filed duplicates if gh auth was stale at
# re-run time. See PR #372 review finding 3.
# issue_exists prints to stdout one of three tokens, never relies on $?:
#   "present"  — issue with the exact title is on file (skip create)
#   "absent"   — issue is not present (proceed to create)
#   "failure"  — gh issue list itself FAILED (abort the script)
# We use stdout because returning non-zero from a function under `set -e`
# trips the trap before the caller can inspect $?. See PR #372 review
# finding 3 — the previous implementation silently filed duplicates when
# gh auth was stale.
issue_exists() {
  local title="$1"
  local list_out
  local list_rc=0
  list_out="$("$GH_BIN" issue list \
    --repo "$EXPECTED_REPO" \
    --state open \
    --search "in:title \"$title\"" \
    --json title \
    --jq '.[].title' 2>&1)" || list_rc=$?
  if [[ $list_rc -ne 0 ]]; then
    printf 'error: `gh issue list` failed (exit %d) for title check: %s\n' "$list_rc" "$title" >&2
    printf '%s\n' "$list_out" >&2
    printf 'failure'
    return 0
  fi
  if printf '%s\n' "$list_out" | grep -Fxq "$title"; then
    printf 'present'
  else
    printf 'absent'
  fi
}

file_child() {
  local slug="$1"
  local scope="$2"
  local body="$3"
  local title
  local state
  title="$(child_title "$slug" "$scope")"
  state="$(issue_exists "$title")"
  case "$state" in
    present)
      printf 'skip: child %s already filed (title match)\n' "$slug" >&2
      return 0
      ;;
    absent) ;;  # fall through to create
    failure)
      printf 'aborting: gh issue list failure cannot be conflated with "issue absent".\n' >&2
      exit 2
      ;;
    *)
      printf 'aborting: unexpected issue_exists output: %s\n' "$state" >&2
      exit 2
      ;;
  esac
  "$GH_BIN" issue create \
    --repo "$EXPECTED_REPO" \
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

**Helm chart path (per parent spec FR-010).** The chart lives at \`scripts/templates/infra/orchestrator/\` — NOT under \`scripts/templates/infra/module_wrappers/\`. The \`module_wrappers/\` subdirectory is reserved for Terraform module wrappers around STACKIT-managed services (\`dns\`, \`kms\`, \`secrets-manager\`, \`observability\`, etc.). The orchestrator is a cluster-resident Python Deployment, not a Terraform wrapper around a managed service — it is a sibling concept under \`infra/\`, not nested inside \`module_wrappers/\`.

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

**C3 matrix schema change (per parent spec FR-012).** This child is the first to introduce a non-\`none\` predicate value, and MUST therefore extend the design-contracts.md § C3 matrix table with a 6th column \`Predicate\` (after \`Convergence mode\`). For all 8 pre-existing rows authored at \`#339\` intake, fill the new column with the literal string \`none\`. For the new \`ux-ui-designer\` rows at step01/04/05/08, fill it with the predicate identifier consumed by \`#361.1\`'s \`PredicateRegistry\` (the first predicate is \`has-user-facing-flow\`). This schema change lands in this PR alongside the matrix-row additions.

## Blocked by

- #361.1 — depends on the predicate-registry mechanism the matrix row references.

## Notes for intake

Per parent spec § Notes for Child Intake: the 9-vs-8 expert-ceiling exception MUST be authored as an ADR amendment, NOT informal PERSONA.md front-matter prose. Choose EXACTLY ONE OF: (a) a \`Status: amended\` note on \`ADR-issue-364-expert-persona-model.md\` with an Amendments section, OR (b) a new narrowly-scoped \`ADR-issue-361.5-ux-ui-designer-ceiling-exception.md\`. The PERSONA.md front-matter cites the chosen ADR by path; the ADR carries the normative rationale.

Reviewers: Architecture + Product.

## Closing

Per parent spec FR-017: the PR body for this child MUST cite parent #361 as \`Tracks #361\` (informational). It MUST NOT use any GitHub auto-close keyword targeting #361 (\`Closes\` / \`Fixes\` / \`Resolves\` / etc.). Parent close is a deliberate human action after all 5 children merge AND the Contract C4 Integration AC checkboxes are ticked — never a side-effect of a child PR merge.

The #361.5 PR body MUST include the literal line \`Closes #369\` — this is the SINGLE permitted auto-close keyword in the entire #361 decomposition. #369 is a different issue (the ux-ui-designer expert addition tracked in AGENTS.backlog.md) that this child legitimately resolves. Omitting \`Closes #369\` leaves #369 open after merge — a known failure mode flagged at parent intake. The corresponding AGENTS.backlog entry MUST be marked \`(incorporated: issue-361.5)\` in the same PR.
EOF
}

main() {
  check_preconditions
  file_child '1' 'dispatch matrix loader + convergence engine + schema validator + predicate-registry mechanism' "$(body_361_1)"
  file_child '2' 'C7 emitter + bus publisher + reviewer-rotation picker' "$(body_361_2)"
  file_child '4' 'Helm chart + NetworkPolicy + ESO + ServiceAccount' "$(body_361_4)"
  file_child '5' 'ux-ui-designer PERSONA.md + C3 matrix wiring + #369 closure' "$(body_361_5)"
}

main "$@"
