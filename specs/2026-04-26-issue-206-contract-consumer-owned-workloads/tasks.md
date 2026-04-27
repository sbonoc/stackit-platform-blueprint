# Tasks

## Spec Readiness Gates
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved — Product (sbonoc), Architecture (sbonoc), Security (sbonoc), Operations (sbonoc) via PR #211 comments
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation (Deferred to Implementing Work Item)
- IMPL T-001: Remove the 4 seed manifest paths from `required_files` in `blueprint/contract.yaml`
- IMPL T-002: Add the 4 seed manifest paths to `source_only_paths` in `blueprint/contract.yaml`
- IMPL T-003: Remove the 4 seed manifest paths from `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`
- IMPL T-004: Write ADR (drafted at `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md` — update status to approved in implementing PR)

## Test Automation (Deferred to Implementing Work Item)
- IMPL T-101: Add `test_seed_manifest_paths_not_in_required_files` to contract test file
- IMPL T-102: Add `test_seed_manifest_paths_in_source_only_paths` to contract test file
- IMPL T-103: Add `test_app_runtime_required_paths_no_hardcoded_manifest_names` to contract test file (positive-path: verifies only directory and kustomization.yaml remain)
- IMPL T-104: Add upgrade planner test with new fixture at `tests/fixtures/upgrade_consumer_renamed_manifests/` (consumer-renamed manifests: `my-api-deployment.yaml`, `my-api-service.yaml`); assert AC-004 (no OPERATION_DELETE/CREATE for the 4 seed paths) and AC-005 (original seed names classified as source-only/skip)
- IMPL T-105: Verify `audit_source_tree_coverage` passes with 4 paths moved to source_only (no uncovered-file regression)
- IMPL T-106: Add fresh-init seeding regression test — run init fixture and assert the 4 seed manifest files are still created in `infra/gitops/platform/base/apps/` via `ensure_infra_template_file`, even though they are no longer in `required_paths_when_enabled`

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
This is a spec-only deliverable. SPEC_READY=true; all four sign-offs approved (sbonoc, PR #211). Spec publication validation complete (T-201–T-205, P-001–P-003, A-001–A-005). Feature implementation tasks (IMPL T-001–T-004, T-101–T-106) are deferred to the implementing work item that consumes this spec.
