# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Additive-file classification fix (#104)
- [ ] T-101 Add failing unit tests covering baseline-absent + source==target → `action=skip` (positive-path: classification returns a record with `action=skip`)
- [ ] T-102 Add failing unit test covering baseline-absent + source!=target → `action=merge-required`
- [ ] T-103 Add regression guard test: baseline-present + 3-way conflict → `action=conflict` unchanged
- [ ] T-001 Fix `_classify_entries` in `scripts/lib/blueprint/upgrade_consumer.py`: compare source vs target when baseline is None; emit `ACTION_SKIP` or `ACTION_MERGE_REQUIRED` instead of `ACTION_CONFLICT`
- [ ] T-104 Confirm positive-path test (T-101) is green and `action=skip` entry contains correct `reason` and `baseline_content_available=false` fields

## Slice 2 — Helper relocation + guard (#106/#107)
- [ ] T-105 Add failing guard test: assert `scripts/bin/platform/apps/smoke.sh` references an existing helper path (will fail before relocation)
- [ ] T-106 Add failing guard test: assert `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` references an existing helper path (will fail before relocation)
- [ ] T-002 Move `scripts/lib/platform/apps/runtime_workload_helpers.py` → `scripts/lib/infra/runtime_workload_helpers.py`
- [ ] T-003 Move `scripts/lib/platform/auth/argocd_repo_credentials_json.py` → `scripts/lib/infra/argocd_repo_credentials_json.py`
- [ ] T-004 Update helper path in `scripts/bin/platform/apps/smoke.sh`
- [ ] T-005 Update helper path in `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh`
- [ ] T-006 Extend `scripts/bin/quality/check_infra_shell_source_graph.py` to detect missing `python3 "$ROOT_DIR/scripts/lib/..."` references in `scripts/bin/platform/**`
- [ ] T-107 Confirm T-105 and T-106 guard tests are green after relocation and caller update

## Slice 3 — ADR, governance, publish
- [ ] T-007 Write ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-104-106-107-upgrade-additive-file-helper-gaps.md`
- [ ] T-008 Update `AGENTS.decisions.md` with classification fix and helper relocation rationale
- [ ] T-009 Update `AGENTS.backlog.md`: mark #104, #106, #107 items done

## Validation and Release Readiness
- [ ] T-201 Run `make infra-contract-test-fast` — green
- [ ] T-202 Run `make quality-infra-shell-source-graph-check` — green
- [ ] T-203 Run `make quality-hooks-fast` — green
- [ ] T-204 Run `make infra-validate` — green
- [ ] T-205 Attach test output evidence to `traceability.md`
- [ ] T-206 Run `make quality-hardening-review`

## Publish
- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md` with FR/AC coverage, key reviewer files, validation evidence, rollback notes
- [ ] P-003 PR description follows repository template; references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected
