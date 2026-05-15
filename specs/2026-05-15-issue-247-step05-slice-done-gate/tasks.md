# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Update SKILL.md
- [ ] T-001 Add Guardrail #13 (API response field coverage) to SKILL.md Guardrails section after existing #12
- [ ] T-002 Add Guardrail #14 (Vue component test per rendering branch) to SKILL.md Guardrails section after #13
- [ ] T-003 Add Guardrail #15 (Pact consumer + provider) to SKILL.md Guardrails section after #14
- [ ] T-004 Update "After All Slices Complete — Minimum validation bundle" table: add REQUIRED row for HTTP scope and REQUIRED row for HTTP+UI rendering scope
- [ ] T-005 Add numbered workflow step "3. Local smoke gate (HTTP and UI-rendering scope)" to SKILL.md main workflow (before "After All Slices Complete"); remove the now-duplicated HTTP block from "Special cases"

### Slice 2 — Create checklist file
- [ ] T-006 Create `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` with four per-slice checklist items (FR-006)

## Test Automation
- [ ] T-101 N/A — docs-only change; no automated test suite applicable. Verification is `make quality-hooks-run` (see T-201).

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [ ] T-A02 N/A — no UI changes
- [ ] T-A03 N/A — no UI changes
- [ ] T-A04 N/A — no UI changes
- [ ] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [ ] T-201 Run governance/docs validation bundle: `make quality-hooks-run` and `make infra-validate`
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; no app delivery workflow impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; no app delivery workflow impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; no app delivery workflow impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; no app delivery workflow impact
