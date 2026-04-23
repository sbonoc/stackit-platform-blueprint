# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: two additive guard blocks in existing functions; no new abstractions, no new files beyond the test and ADR.
- Anti-abstraction gate: guard uses `blueprint_path_is_consumer_seeded` directly (existing helper); no wrapper layer introduced.
- Integration-first testing gate: structural test added to `contract_refactor_scripts_cases.py` before any further integration work.
- Positive-path filter/transform test gate: no filter/payload-transform logic; gate not applicable to this shell guard fix.
- Finding-to-test translation gate: pre-PR finding (bootstrap recreates consumer-seeded paths) translated to `test_infra_bootstrap_does_not_recreate_consumer_seeded_files_in_generated_repos`, which asserts the guard exists in both functions.

## Delivery Slices
1. Slice 1 — Shell fix + test: add `blueprint_path_is_consumer_seeded` guard to `ensure_infra_template_file` and `ensure_infra_rendered_file` in `scripts/bin/infra/bootstrap.sh`; add `infra_bootstrap_consumer_seeded_skip_count` counter and metric; add structural assertion in `tests/blueprint/contract_refactor_scripts_cases.py`.

## Change Strategy
- Migration/rollout sequence: additive — existing behavior for init_managed and non-seeded paths is unchanged.
- Backward compatibility policy: fully backward-compatible; consumers without any `consumer_seeded` paths in `contract.yaml` are unaffected.
- Rollback plan: revert the commit; no persistent state introduced.

## Validation Strategy (Shift-Left)
- Unit checks: `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k infra_bootstrap -v`
- Contract checks: no new make targets or env vars; no contract surfaces changed.
- Integration checks: `make quality-hooks-fast` exercises the full fast-lane gate.
- E2E checks: not applicable (no cluster state changed).

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
- App onboarding impact: no-impact — blueprint governance tooling only; no app lane behavior changes.
- Notes: `make infra-bootstrap` behavior is extended non-destructively; repos without consumer_seeded declarations are unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — no consumer-facing contract changes; the `contract.yaml` `consumer_seeded` path class is already documented.
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP route/filter changes).
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `infra_consumer_seeded_skip_count` metric; `log_info` diagnostic per skipped path.
- Alerts/ownership: no new alerts; existing bootstrap failure alerts cover the unchanged non-seeded paths.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1 (consumer declares a path as consumer_seeded that should actually be template-managed) → mitigation: explicit declaration in `contract.yaml` is intentional; the consumer owns the decision. No silent behavior change.
