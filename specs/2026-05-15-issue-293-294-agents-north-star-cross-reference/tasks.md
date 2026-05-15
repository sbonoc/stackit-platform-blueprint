# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — AGENTS.md template update (closes #293)

### Implementation
- [ ] T-001 Add "Architecture Invariants — Pointers" section to `scripts/templates/consumer/init/AGENTS.md.tmpl` with anti-duplication statement, placeholder pointers table (≥1 example domain row), and "add to north_star.md/ADR only" instruction
- [ ] T-002 Add new Mandatory Workflow rule to `AGENTS.md.tmpl` requiring agent to read north_star.md section + ADR before touching a covered domain, prohibiting AGENTS.md content duplication

### Test Automation
- [ ] T-101 Write unit tests asserting `AGENTS.md.tmpl` contains the "Architecture Invariants — Pointers" section header (AC-001)
- [ ] T-102 Write unit tests asserting `AGENTS.md.tmpl` contains the anti-duplication Mandatory Workflow rule (AC-002)

## Slice 2 — Cross-reference quality hook (closes #294)

### Implementation
- [ ] T-201 Write failing unit tests for AC-003 through AC-007 (heading detection, Pointers-table exemption, allowlist, graceful skip) — red phase
- [ ] T-202 Implement `scripts/bin/quality/check_docs_cross_reference.py`: heading extraction from `##`/`###` markdown lines, normalization, Pointers-table exemption, allowlist loading, violation output, exit code semantics
- [ ] T-203 Add `quality-docs-cross-reference-check` make target to `make/blueprint.generated.mk` with consistent comment/formatting matching existing `quality-docs-*` targets
- [ ] T-204 Wire `quality-docs-cross-reference-check` into `scripts/bin/quality/hooks_fast.sh` in the `quality-docs-check-changed` group alongside existing `quality-docs-check-changed` invocation
- [ ] T-205 Turn all slice-2 tests green

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 N/A — tooling-only change; no UI or frontend involved (see NFR-A11Y-001 in spec.md)

## Validation and Release Readiness
- [ ] T-301 Run `make quality-hooks-fast` — confirm hook chain passes including new `quality-docs-cross-reference-check`
- [ ] T-302 Run `make infra-contract-test-fast` — confirm make target list contract is satisfied
- [ ] T-303 Attach evidence to traceability document
- [ ] T-304 Confirm no stale TODOs/dead code/drift
- [ ] T-305 Run `make docs-build` and `make docs-smoke`
- [ ] T-306 Run `make quality-hardening-review`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; tooling-only change does not modify app delivery targets
- [ ] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — no-impact
- [ ] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — no-impact
- [ ] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — no-impact
- [ ] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — no-impact
