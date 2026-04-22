# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: two new files (Python core + shell wrapper) plus make target registration; no new abstractions or shared libraries.
- Anti-abstraction gate: `_parse_backlog`, `_query_issue_state`, `_build_report` are standalone pure functions; no wrapper classes.
- Integration-first testing gate: `BacklogParsingTests`, `QueryIssueStateTests`, and `BuildReportTests` define boundary behavior before integration tests.
- Positive-path filter/transform test gate: `test_unchecked_markdown_link_is_detected` asserts a matching unchecked line returns one entry with the correct issue ID; `test_closed_issue_with_unresolved_lines_classified_as_required` asserts the full classification path end-to-end.
- Finding-to-test translation gate: no reproducible pre-PR smoke findings; command is additive and cannot regress existing behavior.

## Delivery Slices
1. Slice 1 - Python core and tests: `scripts/lib/blueprint/uplift_status.py` + `tests/blueprint/test_uplift_status.py` (27 tests)
2. Slice 2 - shell wrapper, make target, and docs: `scripts/bin/blueprint/uplift_status.sh`, makefile template and generated file, `test_pyramid_contract.json`, `core_targets.generated.md`, ADR, SDD artifacts

## Change Strategy
- Migration/rollout sequence: additive; generated-consumer repos gain the new make target on the next `make blueprint-upgrade-consumer` cycle.
- Backward compatibility policy: no existing targets or APIs are modified; `blueprint/repo.init.env` variables `BLUEPRINT_GITHUB_ORG` and `BLUEPRINT_GITHUB_REPO` are already present in all generated-consumer repos.
- Rollback plan: revert the commit; no persistent state beyond the JSON artifact is introduced.

## Validation Strategy (Shift-Left)
- Unit checks: 27 pytest unit tests covering parsing, query, classification, strict mode, integration paths; all pass locally.
- Contract checks: `make infra-contract-test-fast` green; `make infra-validate` green.
- Integration checks: `make quality-hooks-fast` green on SDD branch.
- E2E checks: none required; command is additive with no runtime infra dependency.

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
- Notes: command is blueprint-governance tooling, not an app-layer change.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/reference/generated/core_targets.generated.md` — new `blueprint-uplift-status` entry added.
- Consumer docs updates: none required; make target help text is self-documenting and shell wrapper `--help` covers env vars.
- Mermaid diagrams updated: ADR architecture diagram added.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable: no HTTP routes, query/filter logic, or API endpoints touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `log_metric` lines emitted for `tracked_total`, per-state counts, `action_required_count`, `query_failures`; JSON artifact at `artifacts/blueprint/uplift_status.json`.
- Alerts/ownership: no alerts required; command is on-demand.
- Runbook updates: none; `--help` on the shell wrapper is the runbook.

## Risks and Mitigations
- Risk 1: `BLUEPRINT_UPLIFT_REPO` defaults to `BLUEPRINT_GITHUB_ORG/BLUEPRINT_GITHUB_REPO` which may be placeholder values in freshly initialized consumers -> mitigation: shell wrapper validates the resolved value is non-empty; `query_failures` surfaces the problem in the artifact and metrics.
