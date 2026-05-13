# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (RED)

- [x] T-001 Add `test_opensearch_seed_values_allow_insecure_images` to `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py` — assert `parsed["global"]["security"]["allowInsecureImages"] is True` (expected: FAIL before YAML fix)
- [x] T-002 Add `test_opensearch_seed_values_sysctl_image_disabled` to `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py` — assert `parsed["sysctlImage"]["enabled"] is False` (expected: FAIL before YAML fix)
- [x] T-003 Run `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v` — confirm 2 new FAIL, all pre-existing GREEN

## Implementation — Slice 2 (GREEN)

- [x] T-004 Add `global.security.allowInsecureImages: true` and `sysctlImage.enabled: false` to `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`
- [x] T-005 Add same keys to `infra/local/helm/opensearch/values.yaml`
- [x] T-006 Add same keys to `artifacts/infra/rendered/opensearch.values.yaml`
- [x] T-007 Run `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v` — confirm all tests GREEN (47/47 passed)

## Accessibility Testing (Normative — N/A)
- [x] T-A01 N/A — infrastructure-only work item; no UI components (NFR-A11Y-001)

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast` — confirm zero violations
- [ ] T-202 Run `make infra-validate` — confirm no contract violations
- [ ] T-203 Review `docs/platform/modules/opensearch/README.md` and `scripts/templates/blueprint/bootstrap/docs/platform/modules/opensearch/README.md` for chart version compatibility note — add if absent
- [ ] T-204 Run `make docs-build` and `make docs-smoke` — confirm no docs build failures
- [ ] T-205 Run `make quality-hardening-review` — complete hardening review

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A: no app delivery workflow scope (no-impact; targets pre-existing and unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A: no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A: no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A: no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A: no-impact
