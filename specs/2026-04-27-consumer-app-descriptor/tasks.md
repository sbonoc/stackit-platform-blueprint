# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Add `apps.yaml` to `consumer_seeded` in `blueprint/contract.yaml` and bootstrap mirror.
- [ ] T-002 Add `scripts/templates/consumer/init/apps.yaml.tmpl` with baseline app records.
- [ ] T-003 Implement descriptor schema, loader, and safe path derivation.
- [ ] T-004 Wire descriptor validation into app runtime GitOps contract validation.
- [ ] T-005 Wire descriptor records into app catalog rendering and smoke assertions.
- [ ] T-006 Emit descriptor ownership evidence in upgrade plan/postcheck diagnostics.
- [ ] T-007 Retire `_is_consumer_owned_workload()` bridge dependency when descriptor coverage is active.
- [ ] T-008 Update blueprint docs/diagrams.
- [ ] T-009 Update consumer-facing docs/diagrams when contracts/behavior change.

## Test Automation
- [ ] T-101 Add unit tests for descriptor schema and path validation.
- [ ] T-102 Add contract tests for `consumer_seeded` template parity and app runtime validation.
- [ ] T-103 Confirm no filter/payload-transform route is touched; record not-applicable evidence in `pr_context.md`.
- [ ] T-104 Translate deterministic descriptor validation findings into failing tests first, then make them green.
- [ ] T-105 Add renderer tests proving `apps/catalog/manifest.yaml` follows descriptor records.
- [ ] T-106 Add upgrade plan/postcheck tests for `consumer-app-descriptor` ownership diagnostics.

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check`.
- [ ] T-202 Run `make quality-hooks-run`.
- [ ] T-203 Run `make infra-validate`.
- [ ] T-204 Run `make apps-bootstrap`.
- [ ] T-205 Run `make apps-smoke`.
- [ ] T-206 Run `make blueprint-template-smoke`.
- [ ] T-207 Attach evidence to traceability document.
- [ ] T-208 Confirm no stale TODOs/dead code/drift.
- [ ] T-209 Run documentation validation (`make docs-build` and `make docs-smoke`).
- [ ] T-210 Run hardening review validation bundle (`make quality-hardening-review`).

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
