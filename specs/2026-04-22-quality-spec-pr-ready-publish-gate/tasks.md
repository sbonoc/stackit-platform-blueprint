# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Create `scripts/bin/quality/check_spec_pr_ready.py` with `_check_tasks`, `_check_plan`, `_check_hardening_review`, `_check_pr_context`, `_resolve_spec_dir`, and `main`
- [x] T-002 Add `quality-spec-pr-ready` make target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and regenerate `make/blueprint.generated.mk` via `make blueprint-render-makefile`
- [x] T-003 Wire `quality-spec-pr-ready` into `scripts/bin/quality/hooks_fast.sh` with branch-pattern guard (`codex/[0-9]{4}-[0-9]{2}-[0-9]{2}-`) and spec-dir existence check
- [x] T-004 Create ADR at `docs/blueprint/architecture/decisions/ADR-20260422-quality-spec-pr-ready-publish-gate.md`

## Test Automation
- [x] T-101 Create `tests/blueprint/test_spec_pr_ready.py` with positive-path test (fully-filled spec dir exits 0)
- [x] T-102 Add per-file negative-path tests: each scaffold placeholder type fails with correct `[quality-spec-pr-ready]` message
- [x] T-103 No filter/payload-transform logic introduced; gate not applicable
- [x] T-104 Triggering incident (issue-118-137 shipped all-placeholder publish-gate files) translated into per-file negative-path tests covering each placeholder variant
- [x] T-105 Add branch-resolution and missing-spec-dir test cases

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-docs-sync-all`, `make infra-contract-test-fast`
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale TODOs/dead code/drift
- [x] T-204 Run `make docs-build` and `make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
