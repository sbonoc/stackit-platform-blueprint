# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `check_sdd_assets.py` previously enforced a uniform 10-artifact SDD contract for all change types, forcing non-feature work into governance theater (10 stub artifacts) or ungoverned shortcuts (no spec). Fixed by adding a field-gated bypass track: `SPEC_READY_EXCEPTION` + `authorized-by` reduce the required artifact set to `{spec.md, pr_context.md}` while preserving the audit trail in git history and CI metric output.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: bypass path emits `[METRIC] name=sdd_exception_gate_total value=1 type=<type> authorized_by=<handle>` to stdout following the existing blueprint structured log format (`[TIMESTAMP] [blueprint] [METRIC] ...`). No parser changes required. Visible in CI job logs.
- Operational diagnostics updates: none — no new runbooks required. `AGENTS.md §Lightweight SDD Bypass Track` is the operator-facing guide.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: bypass logic is a direct conditional inserted at the top of the existing work-item loop in `check_sdd_assets.py`. No new class, no wrapper, no strategy pattern. Two module-level frozenset constants (`_BYPASS_ALLOWED_VALUES`, `_BYPASS_OPTIONAL_DOCS`) are the only new module-level state. Pre-flight spec.md read is guarded with a try/except to remain non-fatal if spec.md is malformed before the readiness section is parsed.
- Test-automation and pyramid checks: 5 new unit tests in `tests/blueprint/test_sdd_bypass_track.py` registered in `test_pyramid_contract.json` unit scope. All 5 pass; 1014 total unit tests pass with no regressions. Test isolation: each test uses a `tempfile.TemporaryDirectory` with synthetic fixtures — no live cluster or CI runner required.
- Documentation/diagram/CI/skill consistency checks: `AGENTS.md §Lightweight SDD Bypass Track` added; `ADR-issue-275-sdd-bypass-track.md` approved; `architecture.md` flowchart accurately reflects the gate evaluation decision tree; `.spec-kit/templates/blueprint/spec.md` scaffold updated with `SPEC_READY_EXCEPTION: none` and `authorized-by: none` defaults.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI surfaces introduced or modified
- [x] SC 2.1.1 (Keyboard): N/A — no UI surfaces introduced or modified
- [x] SC 2.4.7 (Focus Visible): N/A — no UI surfaces introduced or modified
- [x] SC 1.4.1 (Use of Color): N/A — no UI surfaces introduced or modified
- [x] SC 3.3.1 (Error Identification): N/A — no UI surfaces introduced or modified
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI surfaces introduced or modified

## Proposals Only (Not Implemented)
- Proposal 1 (parked): add `SPEC_READY_EXCEPTION: chore` + active `AGENTS.decisions.md` validation as a machine-verifiable chore governance gate (Q-1 Option B). Parked — surfaces on-scope: quality. Rationale: Option B requires the checker to know the current branch/PR context, introducing tight CI-environment coupling and making the script non-deterministic in local runs; convention + code review is sufficient.
