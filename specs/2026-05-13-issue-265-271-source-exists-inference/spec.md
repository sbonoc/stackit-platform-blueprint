# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-265-271-source-exists-inference.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-009 (secrets/credentials in hooks): N/A — no secret or credential surface
  - SDD-C-010 (observability): N/A — no runtime observability surface; upgrade engine tooling only
  - SDD-C-013 (STACKIT managed services): N/A — no runtime capability changes
  - SDD-C-014 (local-first runtime baseline): N/A — no local Kubernetes provisioning scope
  - SDD-C-015 (app onboarding make targets): N/A — no app delivery workflow scope
  - SDD-C-018 (blueprint upstream defect escalation): N/A — planned capability addition
  - SDD-C-022 (HTTP route/filter smoke): N/A — no HTTP route or filter logic
  - SDD-C-023 (positive-path filter/transform test): N/A — no filter or payload-transform logic

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none — no frontend components; upgrade engine tooling only
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no runtime provisioning scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A — no local runtime provisioning; upgrade engine changes only

## Objective
- Business outcome: Reduce the number of `human_required` conflict rows in `upgrade_triage.json` for `blueprint-managed` catch-all files where the file genuinely exists in the blueprint source (`source_exists=True`). Before issue #270, this inference was unsafe because consumer-created test files in blueprint-tracked directories (e.g. `tests/infra/test_*.py`) could appear with `source_exists=True` yet be consumer-owned. Issue #270 eliminated that case: all blueprint-author test files are now in `tests/blueprint/` (source_only, never in consumer repos), and the remaining `tests/infra/` files are pure consumer-runtime. The inference is now safe.
- Success metric: (1) A `blueprint-managed` conflict entry with `source_exists=True` produces `recommended_action: take_source` in `upgrade_triage.json`. (2) A `blueprint-managed` conflict entry with `source_exists=False` retains `recommended_action: human_required`. (3) The `source_exists` field is present in every conflict entry in `upgrade_triage.json`. (4) All existing `take_source`/`take_target` rows for other ownership classes are unaffected.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001: For each `blueprint-managed` catch-all conflict entry where `UpgradeEntry.source_exists` is `True`, the `_write_upgrade_triage()` function MUST assign `recommended_action: take_source` in `upgrade_triage.json`.

- FR-002: For each `blueprint-managed` catch-all conflict entry where `UpgradeEntry.source_exists` is `False`, the `_write_upgrade_triage()` function MUST assign `recommended_action: human_required` (file exists only in the consumer repo; cannot be safely inferred as blueprint-owned).

- FR-003: The `upgrade_triage.json` conflict entry MUST include a `source_exists` boolean field populated from `UpgradeEntry.source_exists`, so the basis for the inference is present in the audit artifact.

- FR-004: The `reason` field for entries where the source_exists inference promotes `blueprint-managed` to `take_source` MUST contain a note identifying the inference basis (e.g. `"source_exists=True; blueprint-managed ownership inferred"`).

- FR-005: The `upgrade_triage.schema.json` MUST be updated to declare `source_exists` as an optional boolean property on each conflict entry (non-required, backward-compatible with schema version 1).

- FR-006: All other `ownership_class` values (`blueprint-managed-root`, `required-file`, `init-managed`, `conditional-scaffold`, `consumer-seeded`) MUST retain their existing `recommended_action` mapping unchanged.

### Non-Functional Requirements (Normative)

- NFR-REL-001: The change MUST be backward-compatible: consumers running `blueprint-upgrade-consumer-resolve` after this change receive at most the same number of `human_required` rows as before — never more.

- NFR-REL-002: `upgrade_triage.json` schema version MUST remain `1`; the `source_exists` addition is a non-required property and does not break existing schema consumers.

- NFR-OPS-001: The change MUST be documented in the ADR Consequences section, referencing issue #270 as the prerequisite that made the inference safe.

- NFR-A11Y-001: N/A — no UI components.

## Acceptance Criteria (Normative)

- AC-001: A `blueprint-managed` conflict entry where `source_exists=True` produces `recommended_action: take_source` in `upgrade_triage.json`.

- AC-002: A `blueprint-managed` conflict entry where `source_exists=False` produces `recommended_action: human_required` in `upgrade_triage.json`.

- AC-003: `blueprint-upgrade-consumer-resolve` auto-applies a `blueprint-managed` / `source_exists=True` entry without user interaction (treated identically to `take_source` from any other ownership class).

- AC-004: Each conflict entry in `upgrade_triage.json` includes a `source_exists` boolean field.

- AC-005: All existing ownership class mappings (`blueprint-managed-root`, `required-file`, `init-managed`, `conditional-scaffold`, `consumer-seeded`) are unaffected.

- AC-006: `upgrade_triage.schema.json` declares `source_exists` as an optional boolean property; schema validation passes for both old (without `source_exists`) and new (with `source_exists`) triage files.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — planned capability addition, not a defect fix
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Informative Notes (Non-Normative)
- Context: Parked as Option B in ADR-issue-265-271-conflict-resolution-ux. The ADR explicitly stated: "This will be revisited when Issue #270 ships explicit consumer test ownership markers." Issue #270 (PR #290) shipped 2026-05-13 and eliminated the unsafe case.
- The inference condition (`source_exists=True` AND `ownership_class=blueprint-managed`) is now reliable: all blueprint-author files that were in `tests/infra/` have been moved to `tests/blueprint/` (source_only), so any remaining file in a blueprint-managed directory with `source_exists=True` is genuinely blueprint-owned.
- Tradeoffs: Strictly more aggressive than the current conservative behaviour. The remaining risk is if a consumer creates a file under a `blueprint_managed_roots` path that coincidentally also exists in the blueprint source with the same relative path — that file would be auto-overwritten. This risk is mitigated by the intent of `blueprint_managed_roots` being blueprint-exclusive directories.
