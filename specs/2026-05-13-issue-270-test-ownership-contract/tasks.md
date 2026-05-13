# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 0 (Audit, no commit)

- [x] T-000 Run classification audit on all 16 consumer-delivered `tests/infra/test_*.py` files; record final blueprint-author / consumer-runtime / mixed classification per file and per class in `architecture.md`

## Implementation — Slice 1 (RED)

- [x] T-001 Add `test_required_seed_files_contain_no_blueprint_module_refs` to `tests/blueprint/test_quality_contracts.py` — assert no file in `required_seed_files` matching `tests/infra/test_*.py` contains `blueprint/modules/` (expected: FAIL before relocation)
- [x] T-002 Run `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "blueprint_module_refs"` — confirm RED

## Implementation — Slice 2 (GREEN)

- [x] T-003 Move each "entirely blueprint-author" file to `tests/blueprint/test_<name>.py`; update imports if needed
- [x] T-004 Remove fully-relocated paths from `required_seed_files` in `blueprint/contract.yaml`
- [x] T-005 For each "mixed" file: extract blueprint-author test classes to `tests/blueprint/`, remove from original `tests/infra/` file
- [x] T-006 Update `required_seed_files` to reflect split state (keep `tests/infra/` paths with remaining consumer-runtime content)
- [x] T-007 Run `uv run python3 -m pytest tests/blueprint/ -v` — confirm all tests GREEN including new contract assertion
- [x] T-008 Run `uv run python3 -m pytest tests/infra/ -v` — confirm consumer-runtime tests still GREEN
- [x] T-009 Run `make infra-validate` — confirm `blueprint/contract.yaml` valid after `required_seed_files` update

## Implementation — Slice 3 (Docs)

- [ ] T-010 Update `docs/blueprint/governance/ownership_matrix.md` (or equivalent) with normative taxonomy rule for `tests/blueprint/` vs `tests/infra/`
- [ ] T-011 Run `python3 scripts/lib/docs/sync_blueprint_template_docs.py` — sync to bootstrap template mirrors
- [ ] T-012 Run `make quality-docs-check-changed` — confirm PASS

## Accessibility Testing (Normative — N/A)
- [ ] T-A01 N/A — blueprint tooling only; no UI components (NFR-A11Y-001)

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast` — confirm zero violations
- [ ] T-202 Run `make infra-validate` — confirm no contract violations
- [ ] T-203 Confirm `required_seed_files` count is reduced vs pre-change baseline
- [ ] T-204 Run `make docs-build` and `make docs-smoke` — confirm no docs build failures
- [ ] T-205 Run `make quality-hardening-review` — complete hardening review

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` — N/A: no app delivery workflow scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A: no-impact
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A: no-impact
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A: no-impact
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A: no-impact
