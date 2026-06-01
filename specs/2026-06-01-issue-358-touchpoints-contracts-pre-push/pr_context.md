# PR Context

## Summary
- Work item: issue #358 — add touchpoints-test-unit-pre-push, touchpoints-test-contracts-pre-push, backend-test-unit-pre-push hooks to blueprint bootstrap template
- Objective: Seed three file-scoped pre-push gates into the template so consumers automatically gain Vitest unit, Pact contract, and pytest unit shift-left coverage after blueprint upgrade.
- Scope boundaries: Three YAML stanza additions to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` and root `.pre-commit-config.yaml` (drift sync); one pytest test file; one upgrade backport note. No make target changes, no contract.yaml changes, no Kubernetes runtime paths.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- Contract surfaces changed: none — `touchpoints-test-unit`, `touchpoints-test-contracts`, `backend-test-unit` make targets already in onboarding minimum contract; no new target introduced.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`
  - `tests/blueprint/test_pre_push_hooks.py`
- High-risk files: `.pre-commit-config.yaml` (root — drift-synced from template; hooks are no-ops in this repo due to `always_run: false` + file-scoped triggers)

## Validation Evidence
- Required commands executed: `make quality-validate-bootstrap-template-drift` (T-105), `make quality-sdd-check`, `make blueprint-test-unit`, `make touchpoints-test-unit` (T-004), `make touchpoints-test-contracts` (T-004), `make backend-test-unit` (T-004), `make quality-hooks-run` (strict phase all pass; fast phase `quality-spec-pr-ready` resolved before merge)
- Result summary: T-101 through T-104 — 31/31 assertions pass. T-105 drift check exit 0. T-004 — all three make targets exit 0 when test directory absent (no guards needed, T-106 contingency not triggered). Full blueprint suite 1158 passed. quality-sdd-check clean. Strict hooks all pass.
- Artifact references: `artifacts/c7/2026-06-01-issue-358-touchpoints-contracts-pre-push.jsonl` (intake, spec-complete, plan-slicer, implement events); `tests/blueprint/test_pre_push_hooks.py`; `docs/platform/consumer/consumer_quality_gates.md` (backport note)

## Risk and Rollback
- Main risks: (1) A regression injected via a dependency update (no source file touched) is not caught by any of these gates — accepted tradeoff per ADR D-2. (2) `backend-test-unit-pre-push` runs pytest on Python file changes; file-scoped trigger limits latency impact.
- Rollback strategy: Revert the three hook stanzas from both `.pre-commit-config.yaml` files and cut a patch blueprint release; consumers re-sync from the reverted template.

## Deferred Proposals
- Proposal 1 (not implemented): `backend-test-contracts-pre-push` — no active consumer postmortem for Pact provider test regressions slipping through pre-push; deferred per spec.
- Proposal 2 (not implemented): `touchpoints-test-integration-pre-push` — no current postmortem evidence; deferred per spec.
