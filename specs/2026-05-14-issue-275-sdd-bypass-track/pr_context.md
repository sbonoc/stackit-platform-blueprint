# PR Context

## Summary
- Work item: 2026-05-14-issue-275-sdd-bypass-track — Lightweight SDD bypass track via SPEC_READY_EXCEPTION field
- Objective: add a field-gated exception mechanism so non-feature changes (bug-fix, upgrade, refactor, chore) can complete governance with only `{spec.md, pr_context.md}` instead of all 10 SDD artifacts, eliminating governance theater and ungoverned shortcuts
- Scope boundaries: `check_sdd_assets.py` (bypass logic), `.spec-kit/templates/blueprint/spec.md` (scaffold defaults), `AGENTS.md` (policy documentation); out of scope: `check_spec_pr_ready.py`, CI YAML workflows, consumer-repo bootstrap-template propagation

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001 (N/A), NFR-A11Y-001 (N/A)
- Acceptance criteria covered: AC-001 (bypass skips artifact checks), AC-002 (no specs/ dir → exit 0), AC-003 (full-SDD path unaffected), AC-004 (metric emitted), AC-005 (missing authorized-by → violation), AC-006 (quality-sdd-check on own spec.md passes)
- Contract surfaces changed: `spec.md` Spec Readiness Gate section — two new optional fields (`SPEC_READY_EXCEPTION`, `authorized-by`) with backward-compatible `none` defaults; `check_sdd_assets.py` — bypass branch in work-item loop; no API, database, or event contract changes

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_sdd_assets.py` — bypass logic at the top of the work-item loop (search for `_BYPASS_ALLOWED_VALUES`)
  - `tests/blueprint/test_sdd_bypass_track.py` — AC-001 through AC-005 regression tests
  - `AGENTS.md §Lightweight SDD Bypass Track` — policy documentation for the bypass track
- High-risk files:
  - `scripts/bin/quality/check_sdd_assets.py` — any regression in the existing missing-docs check affects all spec validation; AC-003 regression guard covers the full-SDD path

## Validation Evidence
- Required commands executed: `uv run pytest tests/blueprint/test_sdd_bypass_track.py -v` · `make test-unit-all` · `make quality-sdd-check` · `make quality-sdd-check-all` · `make docs-build` · `make docs-smoke` · `make quality-hardening-review`
- Result summary: all 5 AC tests green; 1014 total unit tests pass; quality-sdd-check-all PASS
- Artifact references: `tests/blueprint/test_sdd_bypass_track.py` (5 tests); `scripts/bin/quality/check_sdd_assets.py` (bypass logic); `AGENTS.md §Lightweight SDD Bypass Track`

## Risk and Rollback
- Main risks: (1) Exception mechanism could be misused to bypass full SDD on feature work — mitigated by `authorized-by` requirement creating a visible accountability trail in git history and CI logs; code review provides the human gate. (2) `SPEC_READY_EXCEPTION: none` default means no existing spec is affected without opt-in.
- Rollback strategy: set `SPEC_READY_EXCEPTION: none` (or remove the field) in any `spec.md` to immediately restore full-SDD validation for that work item. Revert `check_sdd_assets.py` commit to remove the bypass branch for all specs. No database migration or data loss risk.

## Deferred Proposals
- Proposal 1 (parked): add `SPEC_READY_EXCEPTION: chore` + active `AGENTS.decisions.md` machine-verifiable validation (Q-1 Option B). Trigger: on-scope: quality. Rationale: Option B requires branch/PR context coupling in the checker, making it non-deterministic in local runs; passive pass + convention is sufficient.
