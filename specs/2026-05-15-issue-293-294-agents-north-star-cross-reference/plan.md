# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Three focused deliverables — a template text change, a duplication-detection script, and a structure-check script. No shared abstractions, no new frameworks.
- Anti-abstraction gate: Use `pathlib`, `re`, and `sys` directly in each script. PyYAML for allowlist parsing (already a declared dependency). No wrapper classes around file I/O.
- Integration-first testing gate: Not applicable — no service boundary interactions. Unit tests drive detection logic; tests are written in Phase 2 against Phase 1 implementations (see multi-agent note below).
- Positive-path filter/transform test gate: Not applicable — no filter/payload-transform logic. The detection logic is heading-set intersection, not record filtering.
- Finding-to-test translation gate: The dhe-marketplace duplication pattern is the triggering finding. AC-003 translates it into a failing test (AGENTS.md heading matches north_star.md heading → violation). The fix turns it green.
- Multi-agent TDD note: In single-agent mode TDD is red → green within one stream. In multi-agent mode (this plan), Phase 1 streams deliver implementations; Phase 2 streams write and verify tests against merged Phase 1 code. Tests are still required and must pass; the red phase is omitted in Phase 2 because implementations already exist when tests are written.

## Delivery Streams

Work is organized into 6 streams across 3 phases. Each stream exclusively owns its files — no two streams in the same phase touch the same path. Gates between phases require all streams in the completed phase to push to the shared branch (serially, with `git pull --rebase` before each push) before the next phase begins.

### Phase 1 — Parallel (no dependencies)

**Stream A — Text governance (FR-001, FR-002, FR-007)**
- Owner: single agent in isolated worktree
- Exclusively owns: `scripts/templates/consumer/init/AGENTS.md.tmpl`, `AGENTS.md` (blueprint root)
- Delivers: Pointers section + north_star.md MUST-read rule in both files
- No test file involvement — tests for this stream are written in Phase 2 (Stream D)
- Validation: `make quality-hooks-fast` (smoke: no regression in existing hook chain)

**Stream B — Duplication check script (FR-003, FR-004, FR-006)**
- Owner: single agent in isolated worktree
- Exclusively owns: `scripts/bin/quality/check_docs_cross_reference.py` (new file)
- Delivers: heading extraction, normalization, Pointers-table exemption, allowlist loading, exit code semantics
- No test file involvement — formal tests written in Phase 2 (Stream D); run script manually against temp fixtures for sanity
- Validation: manual invocation against temp markdown fixtures; `uv run python3 scripts/bin/quality/check_docs_cross_reference.py --help` (smoke)

**Stream C — Structure check script (FR-010)**
- Owner: single agent in isolated worktree
- Exclusively owns: `scripts/bin/quality/check_agents_md_structure.py` (new file)
- Delivers: Pointers-section header detection, north_star.md reference detection in Mandatory Workflow section, exit code semantics, graceful no-op when file absent
- No test file involvement — formal tests written in Phase 2 (Stream E)
- Validation: manual invocation against temp AGENTS.md fixtures

### Gate 1 — Phase 1 complete
All three Phase 1 streams push to the branch before Phase 2 begins. Push order: any; each agent runs `git pull --rebase origin <branch>` before pushing. Conflict risk: zero (disjoint file sets).

### Phase 2 — Parallel (after Gate 1)

**Stream D — Cross-reference tests (AC-001–AC-007, AC-008)**
- Owner: single agent in isolated worktree
- Exclusively owns: `tests/blueprint/test_docs_cross_reference.py`
- Writes: T-101 (Pointers section assertion), T-102 (north_star.md rule assertion), T-103 (blueprint AGENTS.md assertion), T-201–T-205 (heading detection, Pointers-table exemption, allowlist, graceful skip, exit codes)
- Depends on: Gate 1 (A and B merged — implementations exist to test against)
- Must NOT modify: `AGENTS.md.tmpl`, `AGENTS.md`, `check_docs_cross_reference.py` (read-only dependencies)
- Validation: `uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py -v` — all tests green

**Stream E — Structure check tests (AC-011, AC-012)**
- Owner: single agent in isolated worktree
- Exclusively owns: `tests/blueprint/test_agents_md_structure.py` (new file)
- Writes: T-601–T-605 (missing Pointers section → exit 1; missing north_star.md rule → exit 1; both missing → two violations; all present → exit 0; absent AGENTS.md → exit 0)
- Depends on: Gate 1 (C merged — implementation exists to test against)
- Must NOT modify: `check_agents_md_structure.py` (read-only dependency)
- Validation: `uv run python3 -m pytest tests/blueprint/test_agents_md_structure.py -v` — all tests green

### Gate 2 — Phase 2 complete
Both Phase 2 streams push to the branch before Phase 3 begins. Push order: any; each agent runs `git pull --rebase origin <branch>` before pushing. Conflict risk: zero (D and E own different test files).

### Phase 3 — Serial (after Gate 2)

**Stream F — Infrastructure wiring (FR-005, FR-011)**
- Owner: single agent in isolated worktree
- Exclusively owns: `make/blueprint.generated.mk`, `scripts/bin/quality/hooks_fast.sh`
- Delivers: `quality-docs-cross-reference-check` make target, `quality-docs-agents-md-structure-check` make target, both wired into `hooks_fast.sh` `quality-docs-check-changed` group
- Must NOT create new Python files — scripts exist from Phase 1
- Bootstrap propagation: investigate and confirm how existing `check_*.py` scripts propagate to consumer repos (no `scripts/templates/blueprint/bootstrap/scripts/bin/quality/` directory found; propagation likely via existing drift-check mechanism)
- Validation: `make quality-hooks-fast`, `make infra-contract-test-fast`

## Change Strategy
- Migration/rollout sequence: Additive only. Slice 1 is a template text change; existing consumers are unaffected until they re-run init or explicitly pull the updated template. Slice 2 adds a new make target and hook invocation — existing consumers see the hook on blueprint upgrade; clean consumers pass immediately.
- Backward compatibility policy: No existing behavior is removed or modified. The new hook is an additive check. Consumers with pre-existing AGENTS.md ↔ north_star.md heading overlap will see violations on upgrade; the allowlist mechanism provides a structured escape hatch.
- Rollback plan: Revert `AGENTS.md.tmpl` text change (Slice 1). Remove `check_docs_cross_reference.py`, the make target from `make/blueprint.generated.mk`, and the `hooks_fast.sh` invocation (Slice 2). No consumer data affected.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py` — covers AC-003 through AC-007. Template assertions for AC-001 + AC-002 via content checks on the updated `AGENTS.md.tmpl`.
- Contract checks: `make infra-contract-test-fast` — validates make target list and hook wiring.
- Integration checks: `make quality-hooks-fast` — full fast hook suite including the new check against the blueprint repo itself.
- E2E checks: N/A — local tooling only; no runtime or service boundary involved.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: tooling-only change; no app delivery workflow targets are added or modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/decisions/ADR-issue-293-294-agents-north-star-cross-reference.md` — advance status from proposed to approved. `docs/blueprint/core_targets.md` will auto-update via `make quality-docs-sync-core-targets` once the new make target is added.
- Consumer docs updates: none required — the template update is self-documenting (the new section includes the instruction inline).
- Mermaid diagrams updated: architecture.md flowchart documents the detection flow; no consumer-facing diagram changes.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Violations printed to stdout with `[quality-docs-cross-reference-check]` prefix; exit code is the signal. No new metrics or traces owned by this tooling.
- Alerts/ownership: Blueprint maintainer owns the script. No alerting changes.
- Runbook updates: None required.

## Risks and Mitigations
- Risk 1: Consumers with existing AGENTS.md ↔ north_star.md heading overlap will see hook failures on blueprint upgrade -> mitigation: `.quality-docs-cross-reference-allowlist.yml` with required `justification` field provides a structured escape hatch; upgrade notes should flag the new hook.
- Risk 2: Pointers-table exemption requires exact heading text match -> mitigation: template instructions and ADR explicitly state that the Pointers-table domain name MUST match the north_star.md heading text exactly; mismatch means the author must either fix the row or add an allowlist entry.
