# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (single-author mode)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (Tests first, red phase)
- [x] T-001 Add `tests/blueprint/test_template_smoke_assertions.py` with `test_extract_kustomization_resources_parses_resources_section`, `test_extract_kustomization_resources_empty_resources`
- [x] T-002 Extend `tests/blueprint/test_quality_contracts.py` with `test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates`
- [x] T-003 Confirm tests fail before any production code change (red phase)

## Implementation — Slice 2 (Python fix)
- [x] T-011 Add `_extract_kustomization_resources(text: str) -> list[str]` to `scripts/lib/blueprint/template_smoke_assertions.py`
- [x] T-012 Replace hardcoded `app_manifest_paths` list in `validate_app_runtime_conformance()` with dynamic derivation from consumer repo's `infra/gitops/platform/base/apps/kustomization.yaml`
- [x] T-013 Handle the case where the kustomization resources list is empty: raise `AssertionError` with descriptive message when `app_runtime_gitops_enabled=true`
- [x] T-014 Run `pytest tests/blueprint/test_template_smoke_assertions.py` → green (8/8 passed)

## Implementation — Slice 3 (Bash fix)
- [x] T-021 Replace four hardcoded `ensure_infra_template_file` calls in `bootstrap_infra_static_templates()` with `sed`-based `while` loop reading `$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml`
- [x] T-022 Run `pytest tests/blueprint/test_quality_contracts.py` (including new regression guard) → green

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast` → green
- [x] T-202 Run `make infra-validate` → green
- [x] T-203 Confirm no stale TODOs/dead code/drift in touched scope
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)
- [x] T-206 Attach evidence to `traceability.md`

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — not impacted; no app delivery workflow paths changed
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not impacted; no backend app lane changes
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not impacted; no frontend app lane changes
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not impacted; aggregate gates unchanged
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not impacted; port-forward wrappers unchanged
