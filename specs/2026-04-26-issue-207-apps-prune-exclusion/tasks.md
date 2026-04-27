# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `_is_consumer_owned_workload()` predicate in `upgrade_consumer.py`
- [x] T-002 Add consumer-owned-workload guard in `_classify_entries()` before delete branch
- [x] T-003 Write ADR `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-207-apps-prune-exclusion.md`
- [x] T-004 No consumer-facing docs changes required (behavior fix, not contract change)

## Test Automation
- [x] T-101 Add `test_is_consumer_owned_workload_returns_true_for_consumer_manifest` to `test_upgrade_consumer.py`
- [x] T-102 Add `test_is_consumer_owned_workload_returns_false_for_kustomization` to `test_upgrade_consumer.py`
- [x] T-103 Add `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` — positive-path test translating the consumer finding into an automated assertion (FR-001, AC-001)
- [x] T-104 Reproduce finding as failing test before fix; fix turns it green in same work item
- [x] T-105 Add `test_kustomization_yaml_in_base_apps_is_not_protected` — boundary test (AC-002)

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-hardening-review`, `make test-unit-all`
- [x] T-202 Evidence attached to traceability document
- [x] T-203 No stale TODOs; no dead code; no drift from spec
- [x] T-204 `make docs-build` and `make docs-smoke` passed
- [x] T-205 `make quality-hardening-review` passed

## Publish
- [x] P-001 `hardening_review.md` updated with repository-wide findings fixed and proposals-only section
- [x] P-002 `pr_context.md` updated with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; targets unaffected by this change
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact
