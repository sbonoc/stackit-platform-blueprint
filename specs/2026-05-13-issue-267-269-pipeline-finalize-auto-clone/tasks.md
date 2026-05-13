# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — red: auto-clone failing tests
- [x] T-101 Create `tests/infra/test_pipeline_auto_clone_issue_269.py` with failing tests: URL-form source causes Stage 1b/5 failure (regression doc); normalize_upgrade_source function behaviour (local vs. URL detection)

## Slice 2 — green: auto-clone implementation
- [x] T-001 Add URL normalization block to `upgrade_consumer_pipeline.sh` before Stage 1b: `! -d "$upgrade_source/.git"` guard → validate prefix → `git clone --depth 1` → EXIT trap registration
- [x] T-002 Add URL prefix allowlist validation (abort on non-safe prefix) to pipeline URL normalization block
- [x] T-003 Update `scripts/lib/blueprint/upgrade_consumer.py` to skip internal clone when `upgrade_source` is already a local `.git` directory
- [x] T-102 Verify Slice 1 tests turn green after Slice 2 implementation

## Slice 3 — red: finalize failing tests
- [x] T-103 Create `tests/infra/test_pipeline_finalize_issue_267.py` with failing tests: make target existence; sync-pass aggregation (no fail-fast); verify-pass fail-fast with summary banner; idempotency

## Slice 4 — green: finalize implementation + pipeline integration + docs
- [x] T-004 Create `scripts/bin/blueprint/upgrade_consumer_finalize.sh`: usage block, sync pass (aggregated failures), verify pass (fail-fast), per-step log lines
- [x] T-005 Add `blueprint-upgrade-consumer-finalize` target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`
- [x] T-006 Regenerate `make/blueprint.generated.mk` to include the new target
- [x] T-007 Replace Stage 8 and Stage 9 blocks in `upgrade_consumer_pipeline.sh` with `make blueprint-upgrade-consumer-finalize` invocation with appropriate log framing
- [x] T-008 Update `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: replace per-target post-apply list with single `make blueprint-upgrade-consumer-finalize` command
- [x] T-009 Update `upgrade_consumer_pipeline.sh` usage block: document auto-clone behaviour and finalize target
- [x] T-104 Verify Slice 3 tests turn green after Slice 4 implementation
- [x] T-105 Run `make infra-contract-test-fast` — confirm 0 new failures

## Accessibility Testing (Normative — N/A for this work item)
- [x] T-A01 NFR-A11Y-001 declared as N/A in spec.md — CLI tool with no browser-rendered UI surface
- [x] T-A02 N/A — no browser-rendered UI surface
- [x] T-A03 N/A — no browser-rendered UI surface
- [x] T-A04 N/A — no browser-rendered UI surface
- [x] T-A05 N/A — no browser-rendered UI surface

## Validation and Release Readiness
- [x] T-201 Run `make infra-contract-test-fast` and `make quality-hooks-fast` — confirm all pass
- [x] T-202 Attach evidence to traceability document
- [x] T-203 Confirm no stale TODOs/dead code/drift in modified files
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative — N/A for this work item)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; no app delivery scope; targets unchanged
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A; no backend app lanes touched
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A; no frontend app lanes touched
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A; no aggregate gates touched
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A; no port-forward targets touched
