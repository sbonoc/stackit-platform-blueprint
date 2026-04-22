# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `blueprint-uplift-status` make target to `blueprint.generated.mk.tmpl` and regenerate `make/blueprint.generated.mk`
- [x] T-002 Implement `scripts/lib/blueprint/uplift_status.py` (backlog parsing, gh query, classification, artifact write) and `scripts/bin/blueprint/uplift_status.sh` (shell wrapper with strict mode and metrics)
- [x] T-003 Add ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-131-blueprint-uplift-status.md`; update `docs/reference/generated/core_targets.generated.md`
- [x] T-004 No consumer-facing docs/diagrams changed beyond core targets reference

## Test Automation
- [x] T-101 Add 27 unit tests in `tests/blueprint/test_uplift_status.py` covering backlog parsing, query state, classification, strict mode, integration paths
- [x] T-102 No contract tests required; command is additive
- [x] T-103 `test_unchecked_markdown_link_is_detected` and `test_closed_issue_with_unresolved_lines_classified_as_required` provide positive-path coverage for parsing and classification
- [x] T-104 No reproducible pre-PR findings; command is additive
- [x] T-105 `MainIntegrationTests` covers the full main() path end-to-end with temp dirs and state override

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` green; `make infra-validate` green; `pytest tests/blueprint/test_uplift_status.py` 27/27 pass
- [x] T-202 Traceability matrix updated in `traceability.md`
- [x] T-203 No stale TODOs or dead code introduced
- [x] T-204 `make docs-build` and `make docs-smoke` pass
- [x] T-205 `make quality-hardening-review` pass

## Publish
- [x] P-001 `hardening_review.md` updated with findings and proposals
- [x] P-002 `pr_context.md` updated with requirement coverage, reviewer files, validation evidence, rollback notes
- [x] P-003 PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` verified unaffected — blueprint governance tooling only
- [x] A-002 Backend lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-003 Frontend lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` verified unaffected — blueprint governance tooling only
- [x] A-004 Aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` verified unaffected — blueprint governance tooling only
- [x] A-005 Port-forward wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` verified unaffected — blueprint governance tooling only
