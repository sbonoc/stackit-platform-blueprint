# Tasks

## Spec Readiness Gates
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved — Product (sbonoc), Architecture (sbonoc), Security (sbonoc), Operations (sbonoc) via PR #211 comments
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] IMPL T-001: Remove the 4 seed manifest paths from `required_files` in `blueprint/contract.yaml`
- [x] IMPL T-002: Add the 4 seed manifest paths to `source_only_paths` in `blueprint/contract.yaml`
- [x] IMPL T-003: Remove the 4 seed manifest paths from `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`
- [x] IMPL T-004: ADR at `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md` — status: approved

## Test Automation
- [x] IMPL T-101: `test_seed_manifest_paths_not_in_required_files` added to `tests/blueprint/test_upgrade_consumer.py`
- [x] IMPL T-102: `test_seed_manifest_paths_in_source_only_paths` added to `tests/blueprint/test_upgrade_consumer.py`
- [x] IMPL T-103: `test_app_runtime_required_paths_no_hardcoded_manifest_names` added to `tests/blueprint/test_upgrade_consumer.py`
- [x] IMPL T-104: `test_consumer_renamed_manifests_no_delete_or_create_for_seed_paths` (AC-004) and `test_original_seed_names_classified_as_source_only_skip` (AC-005) added to `tests/blueprint/test_upgrade_consumer.py`; `tests/blueprint/test_upgrade_fixture_matrix.py` updated to remove seed paths from `APP_RUNTIME_REQUIRED_FILES`
- [x] IMPL T-105: `audit_source_tree_coverage` passes — `make quality-hooks-fast` green with 4 paths in `source_only`
- [x] IMPL T-106: `test_seed_manifest_templates_exist_in_infra_bootstrap` added to `tests/blueprint/test_upgrade_consumer.py` — verifies 4 seed template files still present in `scripts/templates/infra/bootstrap/`

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-hardening-review`, `make test-unit-all` (all pass for spec artifact set; implementation validation deferred to implementing work item)
- [x] T-202 Attach evidence to traceability document (evidence_manifest.json with sha256 for all spec artifacts)
- [x] T-203 No stale TODOs; no dead code; no drift from spec (spec-only; no code changed)
- [x] T-204 `make docs-build` and `make docs-smoke` passed
- [x] T-205 `make quality-hardening-review` passed

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section (completed for spec-only deliverable)
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes (completed for spec-only deliverable)
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; targets unaffected by this spec
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact

## Implementation Status Note
SPEC_READY=true; all four sign-offs approved (sbonoc, PR #211). All implementation tasks complete (IMPL T-001–T-004, T-101–T-106). Validation bundles passed: `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-hardening-review`, `make test-unit-all` all green.
