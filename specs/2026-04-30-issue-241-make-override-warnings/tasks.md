# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes applicable `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Contract test assertions (red phase)
- [ ] T-101 Add `test_blueprint_generated_mk_template_exposes_override_point_variables` to `tests/blueprint/test_quality_contracts.py` asserting `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` and `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` are present in the template file
- [ ] T-102 Add `test_generated_makefile_exposes_override_point_variables` asserting the same strings are present in `make/blueprint.generated.mk`
- [ ] T-103 Confirm both new tests FAIL before template edits (red phase verified)

## Slice 2 — Template and generated file update (green phase)
- [ ] T-001 In `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`: add `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` before the `spec-scaffold` target
- [ ] T-002 In the `spec-scaffold` recipe, replace the hardcoded `blueprint` in `$(or $(SPEC_TRACK),blueprint)` with `$(SPEC_SCAFFOLD_DEFAULT_TRACK)`
- [ ] T-003 In `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`: add `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` before the `blueprint-uplift-status` target
- [ ] T-004 In the `blueprint-uplift-status` recipe, replace `@scripts/bin/blueprint/uplift_status.sh` with `@$(BLUEPRINT_UPLIFT_STATUS_SCRIPT)`
- [ ] T-005 Run `make blueprint-render-makefile` and verify `make/blueprint.generated.mk` is updated with matching changes
- [ ] T-106 Run `make test-unit-all` — confirm T-101 and T-102 now PASS (green phase verified)

## Slice 3 — ADR and docs
- [x] T-201 Write `docs/blueprint/architecture/decisions/ADR-20260430-issue-241-make-override-warnings.md` — done during intake; Status: approved (sign-offs recorded in Step 03)
- [ ] T-202 Run `make quality-docs-sync-core-targets` and verify no content change in `docs/reference/generated/core_targets.generated.md`
- [ ] T-203 Run `make quality-sdd-check` — must pass clean post-implementation

## Validation and Release Readiness
- [ ] T-204 Run `make infra-contract-test-fast` — confirm all contract tests pass
- [ ] T-205 Run `make quality-hooks-fast` — confirm no violations
- [ ] T-206 Attach evidence to traceability document
- [ ] T-207 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-208 Run hardening review validation bundle (`make quality-hardening-review`)

## App Onboarding Minimum Targets (Normative)
- No-impact declared in `plan.md` — app delivery workflows are not affected by this tooling-only change.
- [ ] A-001 Confirm `apps-bootstrap` and `apps-smoke` are operational and unaffected
- [ ] A-002 Confirm `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are operational and unaffected
- [ ] A-003 Confirm `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are operational and unaffected
- [ ] A-004 Confirm `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are operational and unaffected
- [ ] A-005 Confirm `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are operational and unaffected

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
