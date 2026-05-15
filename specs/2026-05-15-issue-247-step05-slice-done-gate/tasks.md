# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1A — Update SKILL.md (Phase 1, parallel-safe — no file overlap with Slice 1B)
- [x] T-001 Add Guardrail #13 (API response field coverage) to SKILL.md Guardrails section after existing #12
- [x] T-002 Add Guardrail #14 (Vue component test per rendering branch) to SKILL.md Guardrails section after #13
- [x] T-003 Add Guardrail #15 (Pact consumer + provider) to SKILL.md Guardrails section after #14
- [x] T-004 Update "After All Slices Complete — Minimum validation bundle" table: add REQUIRED row for HTTP scope and REQUIRED row for HTTP+UI rendering scope
- [x] T-005 Add numbered workflow step "3. Local smoke gate (HTTP and UI-rendering scope)" to SKILL.md main workflow (before "After All Slices Complete"); remove the now-duplicated HTTP block from "Special cases"

### Slice 1B — Update AGENTS.md (Phase 1, parallel-safe — no file overlap with Slice 1A)
- [x] T-007 Add field-coverage gate requirement to AGENTS.md § Cross-Cutting Guardrails (FR-007)
- [x] T-008 Add per-SFC rendering-branch coverage rule to AGENTS.md § Testing and Quality Ratios (FR-008)
- [x] T-009 Add same-repo Pact provider timing requirement to AGENTS.md § Contract Testing Standards (FR-009)
- [x] T-010 Add two HTTP-scope entries to AGENTS.md § Minimum Validation Bundles (FR-010)

### Slice 2 — Create checklist file (Phase 2 — after Slice 1A only; Slice 1B is independent)
- [x] T-006 Create `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` (contract compliance gap — file absent on disk); content derived from Slice 1A SKILL.md changes; MUST NOT introduce requirements beyond SKILL.md (FR-006)
      depends-on: T-001, T-002, T-003, T-004, T-005 (Slice 1A must be committed first)

## Test Automation
- [x] T-101 N/A — docs-only change; no automated test suite applicable. Verification is `make quality-hooks-run` (see T-201).

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [x] T-201 Run governance/docs validation bundle: `make quality-hooks-run` and `make infra-validate`
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale TODOs/dead code/drift
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; no app delivery workflow impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; no app delivery workflow impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; no app delivery workflow impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; no app delivery workflow impact
