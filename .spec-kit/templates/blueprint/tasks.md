# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Update contract/governance surfaces
- [ ] T-002 Implement runtime/code changes
- [ ] T-003 Update blueprint docs/diagrams
- [ ] T-004 Update consumer-facing docs/diagrams when contracts/behavior change

## Test Automation
- [ ] T-101 Add or update unit tests
- [ ] T-102 Add or update contract tests
- [ ] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists (matching fixture value returns record and output fields remain intact); capture evidence in `pr_context.md`
- [ ] T-104 Translate any reproducible pre-PR smoke/`curl`/deterministic-check finding into a failing automated test first, then turn it green with the fix in the same work item (or document deterministic exception in publish artifacts)
- [ ] T-105 Add boundary/integration tests where required

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 Confirm NFR-A11Y-001 compliance scope is declared in `spec.md` (or explicitly written as "N/A — <reason>")
- [ ] T-A02 Run axe-core WCAG 2.1 AA scan using `runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa'] }` and `attachTo: document.body`; zero violations at configured fail-impact threshold
- [ ] T-A03 Verify keyboard operability: all interactive elements reachable and operable by keyboard (Tab / Shift-Tab / Enter / Space / Escape)
- [ ] T-A04 Verify focus indicator visible on all focused interactive elements (SC 2.4.7)
- [ ] T-A05 Verify all non-text content (images, icons, form controls) has a programmatic label (SC 4.1.2 — Name, Role, Value)

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
