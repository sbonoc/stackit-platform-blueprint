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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260418-upgrade-validation-required-file-reconciliation.md
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
- Business outcome: post-upgrade validation and preflight MUST make missing required surfaces explicit and blocking, with deterministic remediation guidance.
- Success metric: upgrades with missing required files or coupled generated-doc drift MUST fail in `blueprint-upgrade-consumer-validate` and be visible in structured artifacts before merge.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST derive required files from `blueprint/contract.yaml` using active `repo_mode` gating and write a machine-readable manifest to `artifacts/blueprint/upgrade/required_files_status.json`.
- FR-002 MUST fail `upgrade_consumer_validate` when at least one required file for the active `repo_mode` is missing and MUST include path-specific remediation (`render`, `sync`, `restore`, `manual-review`).
- FR-003 MUST evaluate `docs/reference/generated/core_targets.generated.md` and `docs/reference/generated/contract_metadata.generated.md` as one coupled generated-reference contract in validate output.
- FR-004 MUST enrich preflight output with a required-surface reconciliation section and a deterministic `required_surfaces_at_risk` list when upgrade plan entries affect required files.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST keep all artifact/report paths repository-scoped and MUST reject path traversal via relative arguments.
- NFR-OBS-001 MUST expose required-file and generated-reference summary counts so wrapper metrics can emit deterministic observability signals.
- NFR-REL-001 MUST keep report entry ordering deterministic to preserve repeatable CI comparisons across runs.
- NFR-OPS-001 MUST emit actionable stderr diagnostics for missing required files and generated-reference contract failures.

## Normative Option Decision
- Option A: keep implicit required-file assumptions and rely only on existing make-target failures.
- Option B: add explicit repo-mode-aware required-file reconciliation and coupled generated-reference checks in validate/preflight artifacts.
- Selected option: OPTION_B
- Rationale: Option B provides deterministic failures and machine-readable diagnostics while preserving existing ownership boundaries.

## Contract Changes (Normative)
- Config/Env contract: `upgrade_consumer_validate.py` SHALL support `--required-files-status-path` (default `artifacts/blueprint/upgrade/required_files_status.json`).
- API contract: `upgrade_validate.json` MUST include `required_file_reconciliation` and `generated_reference_contract_check` sections with schema-enforced summary keys.
- Event contract:
- Make/CLI contract: `upgrade_consumer_validate.sh` MUST emit metrics for required-file expected/missing counters and generated-reference missing/failed counters.
- Docs contract: `upgrade_preflight.json` MUST include `required_surface_reconciliation` with `required_surfaces_at_risk`.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST be objectively testable: generated-consumer validate fails when a required file is missing and report includes remediation action.
- AC-002 MUST be objectively testable: repo-mode gating excludes source-only required files in generated-consumer mode and requires them in template-source mode.
- AC-003 MUST be objectively testable: preflight report exposes `required_surface_delta_count` and `required_surface_at_risk_count` based on required-file plan impact.
- AC-004 MUST be objectively testable: updated unit tests pass for validate/preflight/wrapper and schema assertions.

## Informative Notes (Non-Normative)
- Context: this slice closes Issue #129 and intentionally keeps ownership classes unchanged.
- Tradeoffs: validate/preflight each keep local repo-mode filtering helper logic to avoid cross-script coupling in this iteration.
- Clarifications: none.

## Explicit Exclusions
- No automatic file regeneration or auto-commit behavior is introduced.
- No ownership path class changes are introduced.
