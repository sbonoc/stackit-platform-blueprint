# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260418-upgrade-convergence-postcheck-gate.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: generated-consumer upgrades MUST produce deterministic ownership-aware reconciliation guidance and MUST fail postcheck when unresolved convergence blockers remain.
- Success metric: upgrade preflight, apply, and postcheck reports expose deterministic bucketed reconciliation outcomes with explicit remediation commands, and postcheck blocks merge on unresolved conflicts.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST emit `artifacts/blueprint/upgrade/upgrade_reconcile_report.json` from upgrade plan/apply execution with the exact file-level buckets `blueprint_managed_safe_to_take`, `consumer_owned_manual_review`, `generated_references_regenerate`, and `conflicts_unresolved`.
- FR-002 MUST include reconcile-report metadata for `repo_mode`, baseline ref, selected upgrade ref, resolved commit, and deterministic command plan.
- FR-003 MUST extend preflight output with merge-risk classification by bucket and deterministic remediation hints/next commands for each non-empty bucket.
- FR-004 MUST add `make blueprint-upgrade-consumer-postcheck` that runs validation and fails when unresolved merge markers exist or reconcile summary reports `conflicts_unresolved_count > 0`.
- FR-005 MUST keep repo-mode-aware behavior explicit: optional docs sync/check hooks in postcheck SHALL run in template-source mode and SHALL be skipped with explicit reason in generated-consumer mode.
- FR-006 MUST update bundled upgrade skill runbooks (source + consumer template fallback) to consume reconcile/postcheck artifacts and declare an explicit safe-to-continue vs blocked operator contract.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST keep report path resolution repository-scoped and MUST reject relative traversal outside repo root.
- NFR-OBS-001 MUST emit deterministic wrapper metrics for reconcile bucket counts and postcheck status/failure reasons.
- NFR-REL-001 MUST keep report ordering deterministic and postcheck failure reasons machine-readable.
- NFR-OPS-001 MUST log concise operator diagnostics with exact remediation commands and artifact paths.

## Normative Option Decision
- Option A: continue using only `required_manual_actions` plus generic validate output.
- Option B: add a first-class reconcile report artifact, preflight merge-risk bucketing, and a dedicated postcheck gate.
- Selected option: OPTION_B
- Rationale: Option B gives deterministic convergence visibility across preflight/apply/postcheck and eliminates ambiguous manual triage.

## Contract Changes (Normative)
- Config/Env contract:
  - `BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH` SHALL default to `artifacts/blueprint/upgrade/upgrade_reconcile_report.json`.
  - `BLUEPRINT_UPGRADE_POSTCHECK_PATH` SHALL default to `artifacts/blueprint/upgrade_postcheck.json`.
- API contract:
  - `upgrade_reconcile_report.json` SHALL include required buckets + deterministic summary counts + blocked status.
  - `upgrade_preflight.json` SHALL include `merge_risk_classification` with bucketed remediation hints.
  - `upgrade_postcheck.json` SHALL include validate status, merge-marker status, reconcile status, docs-hook checks, and summary.
- Event contract:
  - none
- Make/CLI contract:
  - New target `blueprint-upgrade-consumer-postcheck` SHALL be available in source and bootstrap template make surfaces.
  - `upgrade_consumer.sh` SHALL accept/pass `--reconcile-report-path`.
- Docs contract:
  - Upgrade command references and consumer quickstart/troubleshooting docs SHALL include postcheck and reconcile artifact usage.
  - Bundled skill docs SHALL include postcheck safe/blocked exit contract.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/128
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST be objectively testable: upgrade execution writes reconcile artifact with all required buckets and deterministic metadata in generated-consumer fixtures.
- AC-002 MUST be objectively testable: preflight report includes merge-risk classification with deterministic hints and bucket counts aligned with reconcile artifact.
- AC-003 MUST be objectively testable: postcheck fails when unresolved conflicts or merge markers exist and succeeds when both are clean.
- AC-004 MUST be objectively testable: repo-mode docs-hook behavior in postcheck is explicit (`executed` for template-source, `skipped` with reason for generated-consumer).
- AC-005 MUST be objectively testable: source + template skill runbooks reference reconcile/postcheck artifacts and safe/blocked contract.

## Informative Notes (Non-Normative)
- Context: this work item closes backlog priority P1 Issue #128 (upgrade convergence safety).
- Tradeoffs: preflight remains a report synthesizer and does not apply merges; postcheck is strict fail-fast to keep merge gating deterministic.
- Clarifications: none.

## Explicit Exclusions
- No automatic overwrite of consumer-owned files.
- No relaxation of dirty-worktree or delete safety defaults.
