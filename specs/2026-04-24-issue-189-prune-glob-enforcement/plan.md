# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: three files modified. One new function (~40 lines) in validate module. One new section read (~20 lines) in postcheck module. One required check step in skill runbook. No new modules, no new abstractions.
- Anti-abstraction gate: direct use of `pathlib.Path.rglob()` and existing `load_blueprint_contract()`. No new wrapper layers.
- Integration-first testing gate: failing integration tests (REQ-013, REQ-014) are added in Slice 1 (red) before the implementation in Slice 2 (green). Tests exercise the validate and postcheck modules end-to-end.
- Positive-path filter/transform test gate: REQ-010 unit test MUST assert that a file matching a prune glob is returned in `violations` and that `violation_count > 0`. Empty-result-only assertions do not satisfy this gate.
- Finding-to-test translation gate: real incident sbonoc/dhe-marketplace#40 (25 ADRs re-introduced) translates to AC-001 and the integration test in REQ-013: a file matching `docs/blueprint/architecture/decisions/ADR-*.md` present in the consumer working tree must cause validate to exit non-zero and list the violation. This test must fail red before Slice 2 and pass green after.

## Delivery Slices
1. Slice 1 — Failing tests (red): add unit tests (REQ-010, REQ-011, REQ-012) to `tests/blueprint/test_upgrade_consumer_validate.py` and integration tests (REQ-013, REQ-014) to the appropriate test modules. Run suite to confirm new tests FAIL.
2. Slice 2 — Implementation (green): implement `_scan_prune_glob_violations()` in `upgrade_consumer_validate.py`; call it in the main validate flow; append `prune_glob_check` to report JSON; update `summary.status` gate. Add `prune_glob_violations` section and `prune-glob-violations` to `blocked_reasons` in `upgrade_consumer_postcheck.py`. Run suite to confirm all tests PASS.
3. Slice 3 — Skill runbook: add required check step to `.agents/skills/blueprint-consumer-upgrade/SKILL.md` after the manual merge resolution step (REQ-009/AC-005), naming both canonical glob patterns by value.
4. Slice 4 — Docs: update `docs/blueprint/architecture/execution_model.md` to document the prune glob check in the validate phase. Sync bootstrap template docs. Run `make quality-docs-check-changed`.

## Change Strategy
- Migration/rollout sequence: blueprint fix shipped → consumers receive it on next `make blueprint-upgrade-consumer` run. No consumer-side migration needed.
- Backward compatibility policy: additive-only JSON schema changes. Prior validate reports without `prune_glob_check` cause postcheck to treat `violation_count` as 0 — no breaking change. Consumer repos with no prune glob violations are unaffected.
- Rollback plan: remove `_scan_prune_glob_violations()` call from validate module and `prune_glob_violations` section from postcheck module. No state, database, or external API to revert.

## Validation Strategy (Shift-Left)
- Unit checks: `python3 -m pytest tests/blueprint/test_upgrade_consumer_validate.py -v -k prune_glob` — covers REQ-010, REQ-011, REQ-012.
- Contract checks: `make quality-hooks-fast` (includes SDD check, docs-check-changed, spec-pr-ready).
- Integration checks: `python3 -m pytest tests/blueprint/ -v` — covers REQ-013, REQ-014 and full regression suite.
- E2E checks: `make test-smoke-all-local` — not required; no HTTP route, no infra config change; scope is tooling-only Python module change.

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
- App onboarding impact: no-impact — tooling-only Python module change; no app onboarding surface modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/execution_model.md` — add prune glob check to validate phase description.
- Consumer docs updates: none.
- Mermaid diagrams updated: none — prose-only update.
- Docs validation commands:
  - `make quality-docs-check-changed`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not required — no HTTP route, query, filter, or new endpoint in scope.
- Publish checklist:
  - include REQ-001 through REQ-014 and NFR coverage
  - include AC-001 through AC-005 coverage
  - include test evidence (pytest output, unit + integration)
  - include rollback note

## Operational Readiness
- Logging/metrics/traces: one `stderr` line per violation (NFR-OBS-001). `remediation_hint` field in JSON report names exact files and re-run command (NFR-OPS-001). No new metrics.
- Alerts/ownership: no changes.
- Runbook updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` gains required check step (REQ-009). Gate log output and JSON report are self-describing.

## Risks and Mitigations
- Risk 1: `pathlib.Path.rglob()` follows symlinks by default in Python < 3.13. Mitigation: filter collected paths with a `path.resolve().is_relative_to(repo_root)` check before adding to violations list to prevent traversal outside the repo root (NFR-SEC-001).
