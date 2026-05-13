# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1 (RED)

- [x] T-001 Add `test_consumer_ci_template_has_draft_pr_types_filter` to `QualityContractsTests` in `tests/blueprint/test_quality_contracts.py` — assert `types: [opened, synchronize, reopened, ready_for_review]` present in `ci.yml.tmpl` (expected: FAIL before template fix)
- [x] T-002 Add `test_consumer_ci_template_quality_fast_has_draft_pr_guard` to `QualityContractsTests` — assert `if: github.event_name == 'push' || github.event.pull_request.draft == false` present in `ci.yml.tmpl` (expected: FAIL before template fix)
- [x] T-003 Add `test_precommit_has_bootstrap_drift_hook` to `QualityContractsTests` — assert `.pre-commit-config.yaml` contains `id: quality-validate-bootstrap-template-drift` (expected: FAIL before hook added)
- [x] T-004 Add `test_precommit_template_has_bootstrap_drift_hook` to `QualityContractsTests` — assert `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` contains `id: quality-validate-bootstrap-template-drift` (expected: FAIL before hook added)
- [x] T-005 Add `test_make_template_has_quality_validate_bootstrap_drift_target` to `QualityContractsTests` — assert `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` contains `quality-validate-bootstrap-template-drift:` (expected: FAIL before target added)
- [x] T-006 Run `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "draft_pr or bootstrap_drift"` — confirm 5 new FAIL, all pre-existing GREEN

## Implementation — Slice 2 (GREEN)

- [x] T-007 Edit `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` — add `types: [opened, synchronize, reopened, ready_for_review]` on `pull_request:` trigger (FR-001)
- [x] T-008 Edit `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` — add `if: github.event_name == 'push' || github.event.pull_request.draft == false` on `quality-fast` job (FR-002)
- [x] T-009 Edit `scripts/bin/blueprint/validate_contract.py` — add `--bootstrap-drift-only` argument to `parse_args()` and fast path in `main()` calling `_validate_bootstrap_template_sync` (FR-005)
- [x] T-010 Edit `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — add `quality-validate-bootstrap-template-drift:` target (FR-003)
- [x] T-011 Regenerate `make/blueprint.generated.mk` to include the new target (verify `quality-validate-bootstrap-template-drift:` present in generated file)
- [x] T-012 Edit `.pre-commit-config.yaml` — add commit-stage `quality-validate-bootstrap-template-drift` hook with `files:` pattern (FR-004)
- [x] T-013 Edit `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — mirror the same hook (FR-004)
- [x] T-014 Run `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v` — confirm all tests GREEN (including 5 new)
- [x] T-015 Run `uv run python3 -m pytest tests/blueprint/ -v` — confirm all pre-existing tests remain GREEN

## Accessibility Testing (Normative — N/A)
- [x] T-A01 N/A — CI/quality tooling only; no UI components (NFR-A11Y-001)

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast` — confirm zero violations (only expected quality-spec-pr-ready failure for unfilled publish artifacts; all other checks pass)
- [x] T-202 Run `make infra-validate` — confirm no contract violations
- [x] T-203 Verify `make quality-validate-bootstrap-template-drift` exits 0 when `.pre-commit-config.yaml` is in sync with its template counterpart (AC-003; confirmed — new commit-stage hook fires and passes)
- [x] T-204 Run `make docs-build` and `make docs-smoke` — confirm no docs build failures
- [x] T-205 Run `make quality-hardening-review` — complete hardening review

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A: no app delivery workflow scope (no-impact; targets pre-existing and unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A: no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A: no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A: no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A: no-impact
