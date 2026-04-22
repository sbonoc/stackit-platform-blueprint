# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - The classification fix in `upgrade_consumer.py` is a filter/classification logic change. At least one unit test MUST assert that a baseline-absent additive file with matching source/target content is classified as `skip` (positive-path: matching content returns a record with `action=skip`).
  - Empty-result-only or error-path-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Issue #104 is a reproducible finding: translate the described preflight output (additive file in `conflicts`) into a failing test first, then fix.
  - Issues #106/#107 are reproducible failures: translate the missing-helper error into a failing guard test first, then fix.

## Delivery Slices

### Slice 1 — Additive-file classification fix (#104)
1. Add failing unit tests in `tests/blueprint/` covering:
   - baseline-absent + source==target → `action=skip`
   - baseline-absent + source!=target → `action=merge-required`
   - baseline-present + conflict markers → `action=conflict` (regression guard)
2. Fix `_classify_entries` in `scripts/lib/blueprint/upgrade_consumer.py`: when `baseline_content is None` and both source and target exist, compare source vs target content and emit `ACTION_SKIP` or `ACTION_MERGE_REQUIRED` accordingly.
3. Run tests green.

### Slice 2 — Helper relocation + caller updates (#106/#107)
1. Add failing guard test in `tests/infra/test_tooling_contracts.py` (or `check_infra_shell_source_graph.py` test suite) asserting that `scripts/bin/platform/apps/smoke.sh` and `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` reference existing helper paths.
2. Move `scripts/lib/platform/apps/runtime_workload_helpers.py` → `scripts/lib/infra/runtime_workload_helpers.py`.
3. Move `scripts/lib/platform/auth/argocd_repo_credentials_json.py` → `scripts/lib/infra/argocd_repo_credentials_json.py`.
4. Update `scripts/bin/platform/apps/smoke.sh` helper path reference.
5. Update `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` helper path reference.
6. Extend `scripts/bin/quality/check_infra_shell_source_graph.py` to detect missing `python3 "$ROOT_DIR/scripts/lib/..."` references in `scripts/bin/platform/**`.
7. Run tests green; run `make quality-infra-shell-source-graph-check`.

### Slice 3 — ADR, decisions log, backlog, and publish
1. Write ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-104-106-107-upgrade-additive-file-helper-gaps.md`.
2. Update `AGENTS.decisions.md` with classification fix and helper relocation rationale.
3. Update `AGENTS.backlog.md`: mark #104/#106/#107 items done.
4. Run `make quality-hooks-fast` and `make infra-validate`.
5. Complete `pr_context.md` and `hardening_review.md`.

## Change Strategy
- Migration/rollout sequence: Slice 1 → Slice 2 → Slice 3 (sequential; each slice must be green before the next)
- Backward compatibility policy: classification fix is additive-safe (fewer conflicts, never more); helper relocation requires callers to be updated in the same commit so no partial state exists
- Rollback plan: revert the classification fix commit independently of the relocation; both changes are isolated

## Validation Strategy (Shift-Left)
- Unit checks: `python3 -m pytest tests/blueprint/ -q -k "additive"` (new classification tests); `python3 -m pytest tests/infra/test_tooling_contracts.py -q -k "platform_helper"` (new guard tests)
- Contract checks: `make infra-contract-test-fast`; `make quality-infra-shell-source-graph-check`
- Integration checks: `make infra-validate`
- E2E checks: not required (no runtime execution path changed)

## App Onboarding Contract (Normative)
- Required minimum make targets (all unaffected by this work item):
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
- Notes: no app delivery scope affected; all targets above remain functional

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-104-106-107-upgrade-additive-file-helper-gaps.md`; `AGENTS.decisions.md`
- Consumer docs updates: none (internal tooling change; existing upgrade docs cover behavior)
- Mermaid diagrams updated: none
- Docs validation commands:
  - `make quality-hooks-fast`
  - `make infra-validate`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP route/filter/endpoint scope)
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-009, AC-001–AC-007)
  - include key reviewer files (`upgrade_consumer.py`, `check_infra_shell_source_graph.py`, helper file moves, caller updates)
  - include validation evidence (test run output, `make quality-hooks-fast` pass)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: upgrade entries for reclassified paths will emit `action=skip` or `action=merge-required` instead of `action=conflict`; no new metrics required
- Alerts/ownership: none
- Runbook updates: none (existing upgrade runbook covers manual-merge guidance)

## Risks and Mitigations
- Risk 1 (stale helper copies in consumer repos) → mitigation: document in PR description that old `scripts/lib/platform/apps/runtime_workload_helpers.py` and `scripts/lib/platform/auth/argocd_repo_credentials_json.py` copies can be safely deleted after upgrade
- Risk 2 (guard false-positives) → mitigation: scope guard to `python3 "$ROOT_DIR/scripts/lib/..."` pattern only; exclude comment lines and conditional blocks where the file may not exist at guard-check time
