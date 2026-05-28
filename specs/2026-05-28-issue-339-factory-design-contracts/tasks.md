# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Create `docs/blueprint/autonomous-factory/` directory and author `design-contracts.md` with sections C1–C8, each ending in a `Referenced by:` line and any open decisions under `### Open Decisions`. C1–C4 written as identical conventions (FR-004 through FR-007). C5/C6/C7 written with the three required subsections `### Identical rule`, `### Blueprint instance`, `### Consumer overlay` (FR-008/FR-009/FR-010). C8 written with: four named surface categories from FR-013(a–d); per-item stability tier tags from FR-015; per-item extensibility tier tags from FR-017 (default `extensible`; FR-017(b) sealed list pinned exactly); LiteLLM external-service configuration shape per FR-014; FR-018 consumer-extension discovery convention with one worked example per artifact kind (persona shadow, skill add, SDD step add); FR-019 semver compatibility posture; FR-020 `upstream-candidate: true` front-matter convention.
- [ ] T-002 Author `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` (Status: proposed) with the `flowchart TD` Mermaid diagram including C8 node and Context D consumer-inheritance edge, and relative link to the deliverable.
- [ ] T-003 Update blueprint docs/diagrams — confirm the new autonomous-factory subdirectory appears in the rendered docs navigation; no edits to existing docs required.
- [ ] T-004 Update consumer-facing docs/diagrams — the design-contracts deliverable IS consumer-facing per Contract C8; verify it is reachable via the existing blueprint `contract.yaml` documentation surface that consumer repos already inherit; no per-consumer-repo edits in this work item.
- [ ] T-005 Resolve Q-4 (LiteLLM access configuration field name and location in `contract.yaml`) by recording the chosen field path in Contract C8 `### Open Decisions` resolution and updating `spec.md` Open clarification marker count accordingly; required before SPEC_READY can flip to true.
- [ ] T-006 Resolve Q-5 (issue number for the new Phase 1 factory-upgrade-process ticket) by filing the new GitHub issue with the agreed scope (semver compatibility posture, per-artifact versioning, extended `/blueprint-consumer-upgrade` for factory artifacts, first-adopter upgrade roundtrip AC on Epic #332), substituting the assigned issue number into Contract C8 `Referenced by:` lines for FR-019 and FR-020, and updating `spec.md` Open clarification marker count accordingly; required before SPEC_READY can flip to true.

## Test Automation
- [ ] T-101 Add or update unit tests — N/A (documentation-only change; no code units)
- [ ] T-102 Add or update contract tests — N/A (no API/event/Pact contracts added; the C7 schema definition is documentation, consumers ship their own contract tests)
- [ ] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists — N/A (no filter/transform logic)
- [ ] T-104 Translate any reproducible pre-PR smoke/curl/deterministic-check finding into a failing automated test first — N/A (no smoke/curl path; docs validation is `make docs-smoke`)
- [ ] T-105 Add boundary/integration tests where required — N/A (no integration boundaries introduced)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 Confirm NFR-A11Y-001 compliance scope is declared in `spec.md` — declared as `N/A — internal governance documentation. No UI surface is introduced or modified by this work item.`
- [ ] T-A02 Run axe-core WCAG 2.1 AA scan — N/A (no UI surface)
- [ ] T-A03 Verify keyboard operability — N/A (no UI surface)
- [ ] T-A04 Verify focus indicator visible on focused interactive elements — N/A (no UI surface)
- [ ] T-A05 Verify all non-text content has a programmatic label — N/A (no UI surface)

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles (`make quality-sdd-check`, `make docs-build`, `make docs-smoke`)
- [ ] T-202 Attach evidence to traceability document (`make quality-sdd-check` summary, `make docs-build` summary, `make docs-smoke` summary in `evidence_manifest.json`)
- [ ] T-203 Confirm no stale TODOs/dead code/drift — verify zero `TBD` tokens outside `### Open Decisions` subsections in the deliverable; verify no orphan tickets in `Referenced by:` lines
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — N/A (no app scope affected by this documentation-only work item)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — N/A (no app scope affected)
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — N/A (no app scope affected)
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — N/A (no app scope affected)
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — N/A (no app scope affected)
