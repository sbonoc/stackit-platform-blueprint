# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `touchpoints-test-unit-pre-push` hook stanza to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` (FR-001)
- [x] T-002 Add `touchpoints-test-contracts-pre-push` hook stanza to the same template (FR-002)
- [x] T-003 Add `backend-test-unit-pre-push` hook stanza to the same template (FR-003)
- [x] T-004 Verify all three make targets exit 0 when the relevant test directory is absent; add absent-directory guards if needed (NFR-REL-001, Risk 1)
- [x] T-005 Add backport note to blueprint upgrade documentation describing all three hooks, their `files` triggers, and the make targets (NFR-OPS-001)

## Test Automation
- [x] T-101 Write `tests/blueprint/test_pre_push_hooks.py` asserting `touchpoints-test-unit-pre-push` is present in the template YAML with correct `entry`, `language`, `pass_filenames`, `always_run`, `stages`, `files` values — written RED before Slice 2 (AC-001)
- [x] T-102 Assert `touchpoints-test-contracts-pre-push` is present in the template with correct field values including broader `files` pattern covering api-client source — written RED before Slice 3 (AC-002)
- [x] T-103 Assert `backend-test-unit-pre-push` is present in the template with correct field values — written RED before Slice 4 (AC-003)
- [x] T-104 Assert all three hook definitions set `always_run: false` and `stages: [pre-push]` only — confirming no commit-stage blocking (AC-004)
- [x] T-105 Assert `make quality-validate-bootstrap-template-drift` exits 0 after all three hooks are added — capture exit code as evidence in traceability (AC-005)
- [ ] T-106 Translate any reproducible pre-PR finding from T-004 (absent-directory exit-code checks) into failing automated tests first, then fix; document any deterministic exception in publish artifacts (SDD-C-024)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 N/A — NFR-A11Y-001 is declared N/A in spec.md (template modification only, no UI)

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check` — confirm all SDD gates pass; capture result in traceability
- [ ] T-202 Run `make quality-validate-bootstrap-template-drift` — capture pass/fail as T-103 evidence in traceability
- [ ] T-203 Confirm no stale scaffold tokens, dead code, or drift in modified files
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- App onboarding impact: no-impact — this work item adds a pre-push hook that invokes `touchpoints-test-contracts`, already in the minimum targets list; no new make target is introduced.
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
