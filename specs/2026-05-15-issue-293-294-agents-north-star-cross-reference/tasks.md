# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Stream A — Text governance (FR-001, FR-002, FR-007)
Exclusively owns: `scripts/templates/consumer/init/AGENTS.md.tmpl`, `AGENTS.md` (blueprint root)

### Implementation
- [ ] T-001 Add "Architecture Invariants — Pointers" section to `scripts/templates/consumer/init/AGENTS.md.tmpl` with anti-duplication statement, placeholder pointers table (≥1 example domain row), and "add to north_star.md/ADR only" instruction
- [ ] T-002 Add Mandatory Workflow rule to `AGENTS.md.tmpl` requiring agent to read north_star.md section + ADR before touching a covered domain, prohibiting AGENTS.md content duplication (FR-002)
- [ ] T-004 Add north_star.md MUST-read Mandatory Workflow rule to blueprint's own `AGENTS.md`, prohibiting architecture content duplication (FR-007)

### Validation
- [ ] Run `make quality-hooks-fast` — confirm no regression in existing hook chain

## Stream B — Duplication check script (FR-003, FR-004, FR-006)
Exclusively owns: `scripts/bin/quality/check_docs_cross_reference.py` (new file)

### Implementation
- [ ] T-202 Implement `scripts/bin/quality/check_docs_cross_reference.py`: heading extraction from `##`/`###` markdown lines, normalization, Pointers-table exemption, allowlist loading, violation output, exit code semantics

### Validation
- [ ] Manual invocation against temp markdown fixtures; `uv run python3 scripts/bin/quality/check_docs_cross_reference.py --help` (smoke)

## Stream C — Structure check script (FR-010)
Exclusively owns: `scripts/bin/quality/check_agents_md_structure.py` (new file)

### Implementation
- [ ] T-602 Implement `scripts/bin/quality/check_agents_md_structure.py`: scan for `## Architecture Invariants — Pointers` header and `north_star.md` reference within `## Mandatory Workflow` section; emit `[quality-docs-agents-md-structure-check]` violations; exit 0/1 semantics; graceful no-op when AGENTS.md absent

### Validation
- [ ] Manual invocation against temp AGENTS.md fixtures

---
## Gate 1 — Phase 1 complete (A, B, C push serially with `git pull --rebase`)
---

## Stream D — Cross-reference tests (AC-001–AC-007, AC-008)
Exclusively owns: `tests/blueprint/test_docs_cross_reference.py`
Depends on: Gate 1 (Stream A and Stream B merged)

### Test Automation
- [ ] T-101 Write unit tests asserting `AGENTS.md.tmpl` contains the "Architecture Invariants — Pointers" section header (AC-001)
- [ ] T-102 Write unit tests asserting `AGENTS.md.tmpl` contains the north_star.md anti-duplication Mandatory Workflow rule (AC-002)
- [ ] T-103 Write unit tests asserting blueprint's own `AGENTS.md` contains the north_star.md MUST-read Mandatory Workflow rule (AC-008)
- [ ] T-201 Write unit tests for AC-003 through AC-007: heading detection, Pointers-table exemption, allowlist, graceful skip, exit codes
- [ ] T-205 Verify all cross-reference tests pass: `uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py -v`

## Stream E — Structure check tests (AC-011, AC-012)
Exclusively owns: `tests/blueprint/test_agents_md_structure.py` (new file)
Depends on: Gate 1 (Stream C merged)

### Test Automation
- [ ] T-601 Write unit tests for AC-011 and AC-012: missing Pointers section → exit 1; missing north_star.md rule → exit 1; both missing → two violations; all present → exit 0; absent AGENTS.md → exit 0
- [ ] T-605 Verify all structure check tests pass: `uv run python3 -m pytest tests/blueprint/test_agents_md_structure.py -v`

---
## Gate 2 — Phase 2 complete (D, E push serially with `git pull --rebase`)
---

## Stream F — Infrastructure wiring (FR-005, FR-011)
Exclusively owns: `make/blueprint.generated.mk`, `scripts/bin/quality/hooks_fast.sh`
Depends on: Gate 2 (Streams D and E merged)

### Implementation
- [ ] T-203 Add `quality-docs-cross-reference-check` make target to `make/blueprint.generated.mk` with consistent comment/formatting matching existing `quality-docs-*` targets
- [ ] T-204 Wire `quality-docs-cross-reference-check` into `scripts/bin/quality/hooks_fast.sh` in the `quality-docs-check-changed` group
- [ ] T-603 Add `quality-docs-agents-md-structure-check` make target to `make/blueprint.generated.mk`
- [ ] T-604 Wire `quality-docs-agents-md-structure-check` into `scripts/bin/quality/hooks_fast.sh` in the `quality-docs-check-changed` group; confirm script propagation path to consumer repos

### Validation
- [ ] Run `make quality-hooks-fast` — confirm hook chain passes including both new checks
- [ ] Run `make infra-contract-test-fast` — confirm make target list contract is satisfied

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 N/A — tooling-only change; no UI or frontend involved (see NFR-A11Y-001 in spec.md)

## Validation and Release Readiness
- [ ] T-301 Run `make quality-hooks-fast` — confirm hook chain passes including new `quality-docs-cross-reference-check` and `quality-docs-agents-md-structure-check`
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
