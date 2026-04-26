# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
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
- IMPL T-104: Add or extend upgrade planner test to verify AC-004 (consumer-renamed manifests not created back) and AC-005 (original seed names skipped as source-only, not updated)
- IMPL T-105: Verify `audit_source_tree_coverage` passes with 4 paths moved to source_only (no uncovered-file regression)

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
This is a spec-only deliverable. All implementation tasks (T-001–T-004, T-101–T-105, T-201–T-205, P-001–P-003, A-001–A-005) are left unchecked intentionally — they are deferred to the implementation work item that consumes this spec. The gate checks (G-001–G-005) are complete: the spec is ready for implementation.
