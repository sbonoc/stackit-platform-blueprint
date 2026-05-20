# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0` (Q-1 must be resolved or explicitly deferred)
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (red: failing tests)
- [x] T-001 Add `tests/infra/modules/workflows/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope (commit before creating the file)
- [x] T-002 Write `tests/infra/modules/workflows/test_contract.py` with ≥ 15 failing assertions

## Implementation — Slice 2 (green: verify against existing implementation)
- [x] T-003 Run `uv run python3 -m pytest tests/infra/modules/workflows/test_contract.py` — all ≥ 15 assertions MUST pass green against existing code; fix any real implementation gaps found
- [x] T-004 Run `make test-unit-all` — all existing tests remain green
- [x] T-005 Run `make quality-hooks-fast`

## Implementation — Slice 3 (docs)
- [x] T-006 Write `docs/platform/modules/workflows/README.md` replacing the generated stub with full documentation: provisioning lifecycle, Keycloak OIDC contract, DAG repository requirements, API contract approach, state file outputs, security note, troubleshooting, consumer usage examples

## Implementation — Slice 4 (validation gate)
- [x] T-007 Run `make infra-validate` — exit 0
- [x] T-008 Run `make docs-build && make docs-smoke` — exit 0
- [x] T-009 Run `make quality-hooks-run` — all hooks green
- [x] T-010 Run `make quality-hardening-review` — exit 0

## Test Automation
- [x] T-101 Confirm `test_contract.py` is registered in `test_pyramid_contract.json` under `unit` scope before creation (pre-commit pyramid gate must not block)
- [x] T-102 Confirm `test_contract.py` has ≥ 15 passing assertions after Slice 2
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 N/A — no reproducible pre-PR smoke/curl findings; existing implementation has been validated in agentic-graphrag
- [x] T-105 N/A — no boundary/integration tests required; state file contract is fully covered at unit level

## Accessibility Testing
- [x] T-A01 NFR-A11Y-001: N/A — no UI or frontend changes in this work item

## Validation and Release Readiness
- [x] T-201 Run `make test-unit-all` (all tests green including new `test_contract.py`)
- [x] T-202 Run `make infra-validate` (contract + make target consistency)
- [x] T-203 Run `make quality-hooks-run` (full pre-push gate)
- [x] T-204 Run `make docs-build && make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage (FR-001–FR-014, AC-001–AC-010), key reviewer files, validation evidence, risk/rollback notes
- [ ] P-003 Ensure PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change
