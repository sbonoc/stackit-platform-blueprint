# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Slice 1 — AGENTS.md `§ Mandatory Workflow` adds mandatory-gate clause + exempt-track list (FR-001, AC-010)
- [x] T-002 Slice 2 — `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` AC authoring rule + rejection of label-only ACs (FR-004, AC-006)
- [x] T-002b Slice 2 — `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` Discover-phase canonical AC authoring guidance + `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` AC placeholder seeded in canonical form (FR-012, AC-011)
- [x] T-003 Slice 3 — `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` four new guardrails + per-profile examples table (FR-005..FR-010, AC-007, AC-008, AC-009)
- [x] T-004 Slice 4 — `scripts/bin/quality/check_sdd_assets.py` `_check_step03_complete_event` function + wiring into implementation-ready validator path (FR-002, FR-003, NFR-OBS-001, AC-001..AC-005)
- [x] T-005 Slice 5 — FR-011 forward-only merge-date constant (`_SPEC_COMPLETE_GATE_SINCE = "2026-06-01"`) in check_sdd_assets.py; no `sdd-policy-snapshot` make target exists
- [x] T-006 Cross-skill update — verified `CLAUDE.md` skill table caption text; no changes needed
- [x] T-007 Generated SDD policy snapshot — no snapshot make target; AGENTS.md snapshot unchanged (gate is implementation detail not surfaced in snapshot)

## Test Automation
- [x] T-101 Slice 4 pytest cases — AC-001 happy path (spec-complete event present → exit 0)
- [x] T-102 Slice 4 pytest cases — AC-002 missing event (exit non-zero, metric emitted, slug in stderr)
- [x] T-103 Slice 4 pytest cases — AC-003 upgrade exemption (SPEC_READY_EXCEPTION=upgrade → exit 0)
- [x] T-104 Slice 4 pytest cases — AC-004 chore-no-specs exemption (no specs/ subdir → exit 0)
- [x] T-105 Slice 4 pytest cases — AC-005 c7-emission-opted-out event does NOT satisfy gate (exit non-zero for non-exempt work item)
- [x] T-201 Slice 2 pytest case — AC-006 step03 SKILL.md AC authoring rule + rejection text present
- [x] T-202 Slice 3 pytest case — AC-007 step05 SKILL.md four numbered guardrails present
- [x] T-203 Slice 3 pytest case — AC-008 per-profile examples table contains TS/Python/Kotlin/Go rows
- [x] T-204 Slice 3 pytest case — AC-009 FR-009 Vitest Browser Mode satisfaction + Playwright escalation rule present
- [x] T-205 Slice 1 pytest case — AC-010 AGENTS.md mandatory-gate phrase + exempt-track tokens present
- [x] T-206 Slice 2 pytest case — AC-011 step01 SKILL.md canonical-form guidance present AND both scaffold templates seed AC-001 placeholder in canonical form (FR-012)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 N/A — governance change with no UI surface (per NFR-A11Y-001)
- [ ] T-A02 N/A — governance change with no UI surface
- [ ] T-A03 N/A — governance change with no UI surface
- [ ] T-A04 N/A — governance change with no UI surface
- [ ] T-A05 N/A — governance change with no UI surface

## Validation and Release Readiness
- [ ] T-301 Run `make quality-sdd-check` against this work item's own `specs/` directory — MUST pass after slice 5
- [ ] T-302 Run `make quality-hooks-fast` at each slice boundary; capture pass/fail in `pr_context.md`
- [ ] T-303 Run `make docs-build` and `make docs-smoke`
- [ ] T-304 Confirm no stale TODOs/dead code/drift
- [ ] T-305 Run `make quality-hardening-review`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
<!-- App onboarding impact: no-impact per plan.md. Literal make-target tokens preserved
     below so the SDD asset checker recognizes the section; no new make-target wiring is
     produced by this work item. -->
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact)
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact)
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact)
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact)
