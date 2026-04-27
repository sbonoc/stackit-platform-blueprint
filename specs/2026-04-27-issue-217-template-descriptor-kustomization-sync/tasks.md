# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Extend `template_smoke_assertions.py:main()` with descriptor-kustomization cross-check assertion (FR-001): parse seeded `apps/descriptor.yaml` with `yaml.safe_load`, extract manifest filenames per component (handling convention-default paths), verify each against `app_manifest_names`; raise AssertionError per missing filename with descriptor path, kustomization path, and filename in message
- [ ] T-002 Verify template file consistency (FR-002): confirm `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` and `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` reference the same set of manifest filenames

## Test Automation
- [ ] T-101 Add unit tests in `tests/blueprint/test_template_smoke_assertions.py` (or equivalent): (a) consistent descriptor+kustomization pair returns without AssertionError, (b) descriptor referencing an absent filename raises AssertionError naming the missing file and both paths, (c) convention-default manifest path is handled correctly (no explicit `manifests:` block)
- [ ] T-102 Add template consistency test: reads both template files and asserts their filename sets are equal (FR-002/AC-003)
- [ ] T-103 Verify positive-path test for the assertion: a descriptor+kustomization pair where all 4 filenames agree passes without error
- [ ] T-104 Confirm pre-patch failure scenario (descriptor referencing 4 filenames with kustomization listing only 1) is covered by a failing test that the assertion implementation makes green
- [ ] T-105 Run `make blueprint-template-smoke` with current consistent templates and confirm exit 0

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check` and `make quality-hooks-fast`
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

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
