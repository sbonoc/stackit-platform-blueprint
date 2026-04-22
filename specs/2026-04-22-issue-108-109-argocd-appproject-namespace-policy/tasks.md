# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Guard test (red)
- [x] T-101 Add failing guard tests in `tests/infra/test_tooling_contracts.py` class `AppProjectNamespacePolicyTests`: assert `external-secrets` is present in destinations of all four overlay AppProject files and the bootstrap template copy

## Slice 2 — Manifest fix (green)
- [x] T-001 Add `external-secrets` destination to `infra/gitops/argocd/overlays/local/appproject.yaml`
- [x] T-002 Add `external-secrets` destination to `infra/gitops/argocd/overlays/dev/appproject.yaml`
- [x] T-003 Add `external-secrets` destination to `infra/gitops/argocd/overlays/stage/appproject.yaml`
- [x] T-004 Add `external-secrets` destination to `infra/gitops/argocd/overlays/prod/appproject.yaml`
- [x] T-005 Add `external-secrets` destination to `scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml`
- [x] T-102 Confirm guard tests pass after manifest fix

## Slice 3 — ADR, governance, publish
- [x] T-006 Write ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-108-109-argocd-appproject-namespace-policy.md`
- [x] T-007 Update `AGENTS.decisions.md`
- [x] T-008 Update `AGENTS.backlog.md`: mark #108, #109 items done

## Validation and Release Readiness
- [x] T-201 Run `make infra-contract-test-fast` — green (94 passed, 2 subtests passed)
- [x] T-202 Run `make quality-hooks-fast` — green
- [x] T-203 Run `make infra-validate` — green
- [x] T-204 Attach test output evidence to `traceability.md`
- [x] T-205 Run `make quality-hardening-review` — green

## Publish
- [x] P-001 Update `hardening_review.md`
- [x] P-002 Update `pr_context.md`
- [ ] P-003 Open PR referencing issues #108 and #109

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected
