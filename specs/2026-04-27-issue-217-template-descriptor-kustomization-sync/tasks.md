# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Extend `template_smoke_assertions.py:main()` with descriptor-kustomization cross-check assertion (FR-001): parse seeded `apps/descriptor.yaml` with `yaml.safe_load`, extract manifest filenames per component (handling convention-default paths), verify each against `app_manifest_names`; raise AssertionError per missing filename with descriptor path, kustomization path, and filename in message
- [x] T-002 Verify template file consistency (FR-002): confirm `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` and `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` reference the same set of manifest filenames

## Test Automation
- [x] T-101 Add unit tests in `tests/blueprint/test_template_smoke_assertions.py` (or equivalent): (a) consistent descriptor+kustomization pair returns without AssertionError, (b) descriptor referencing an absent filename raises AssertionError naming the missing file and both paths, (c) convention-default manifest path is handled correctly (no explicit `manifests:` block)
- [x] T-102 Add template consistency test: reads both template files and asserts their filename sets are equal (FR-002/AC-003)
- [x] T-103 Verify positive-path test for the assertion: a descriptor+kustomization pair where all 4 filenames agree passes without error
- [x] T-104 Confirm pre-patch failure scenario (descriptor referencing 4 filenames with kustomization listing only 1) is covered by a failing test that the assertion implementation makes green
- [x] T-105 Run `make blueprint-template-smoke` with current consistent templates — pre-existing macOS `declare -A` failure is a known out-of-scope exception on macOS (bash v3); templates are consistent as confirmed by T-102/T-103

## Validation and Release Readiness
- [x] T-201 Run `make quality-sdd-check` and `make quality-hooks-fast`
- [x] T-202 Attach evidence to traceability document — validation evidence captured in `pr_context.md` (7 new tests green, 626/628 full regression pass, quality-sdd-check pass)
- [x] T-203 Confirm no stale TODOs/dead code/drift — no TODOs introduced; helper is module-private; no dead code
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`) — tooling-only change; no docs content affected; validation commands confirmed no-op for this scope
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`) — `hardening_review.md` updated with findings, observability, architecture, and proposals sections

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — not impacted; tooling-only change, no app delivery workflow paths changed
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not impacted; no backend app lane changes
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not impacted; no frontend app lane changes
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not impacted; aggregate gates unchanged
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not impacted; port-forward wrappers unchanged
