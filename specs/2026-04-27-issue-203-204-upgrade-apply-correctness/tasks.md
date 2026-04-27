# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Kustomization-ref prune guard
- [ ] T-001 Write failing unit tests for `_is_kustomization_referenced` (resources, patches, not-referenced, malformed)
- [ ] T-002 Write failing classification test: kustomization-referenced file → `consumer-kustomization-ref / skip / none`
- [ ] T-003 Implement `_is_kustomization_referenced(repo_root, relative_path) -> bool` in `upgrade_consumer.py`
- [ ] T-004 Wire `_is_kustomization_referenced` into `_classify_entries` after `_is_consumer_owned_workload`
- [ ] T-005 Update `_is_consumer_owned_workload` docstring (remove "see issue #203 for general unification")

## Implementation — Slice 2: Terraform block deduplication
- [ ] T-006 Write failing unit tests for `_tf_deduplicate_blocks` (byte-identical dedup, non-identical signal)
- [ ] T-007 Write failing apply-loop test: clean merge `.tf` with byte-identical duplicate → `merged-deduped`
- [ ] T-008 Write failing apply-loop test: clean merge `.tf` with non-identical duplicate → `conflict`
- [ ] T-009 Implement `_tf_deduplicate_blocks(content: str) -> tuple[str, list[str]]`
- [ ] T-010 Wire `_tf_deduplicate_blocks` into the apply loop after `_three_way_merge` for `.tf` paths

## Implementation — Slice 3: Apply artifact counters
- [ ] T-011 Add `consumer_kustomization_ref_count` and `tf_dedup_count` to apply artifact JSON
- [ ] T-012 Add `deduplication_log` array to apply artifact JSON
- [ ] T-013 Update apply artifact contract test to assert new fields

## Test Automation
- [ ] T-101 Positive-path unit test for `_is_kustomization_referenced` with `resources:` fixture (AC-002)
- [ ] T-102 Positive-path unit test for `_is_kustomization_referenced` with `patches:` fixture (AC-001)
- [ ] T-103 Positive-path unit test for `_tf_deduplicate_blocks`: byte-identical duplicate → single block in output (AC-004)
- [ ] T-104 Integration test: full `_classify_entries` call with kustomization-referenced file and `allow_delete=True` returns skip (AC-001, AC-002)
- [ ] T-105 Integration test: full apply loop with duplicate Terraform variable block → correct result classification (AC-004, AC-005)
- [ ] T-106 Negative-path test: file absent in source, not referenced in any kustomization.yaml, `allow_delete=True` → delete classification produced unchanged (AC-003)

## Validation and Release Readiness
- [ ] T-201 Run `pytest tests/blueprint/test_upgrade_consumer.py` — all tests green
- [ ] T-202 Run `make quality-hooks-fast` — no violations
- [ ] T-203 Run `make infra-validate` — no violations
- [ ] T-204 Run `make blueprint-template-smoke` — passes
- [ ] T-205 Run `make docs-build` and `make docs-smoke`
- [ ] T-206 Run `make quality-hardening-review` — no violations
- [ ] T-207 Attach test output evidence to `traceability.md`

## App Onboarding Minimum Targets
- [ ] A-001 `apps-bootstrap` — no-impact (script-only work item)
- [ ] A-002 `apps-smoke` — no-impact
- [ ] A-003 `backend-test-unit` — no-impact
- [ ] A-004 `backend-test-integration` — no-impact
- [ ] A-005 `backend-test-contracts` — no-impact
- [ ] A-006 `backend-test-e2e` — no-impact
- [ ] A-007 `touchpoints-test-unit` — no-impact
- [ ] A-008 `touchpoints-test-integration` — no-impact
- [ ] A-009 `touchpoints-test-contracts` — no-impact
- [ ] A-010 `touchpoints-test-e2e` — no-impact
- [ ] A-011 `test-unit-all` — no-impact
- [ ] A-012 `test-integration-all` — no-impact
- [ ] A-013 `test-contracts-all` — no-impact
- [ ] A-014 `test-e2e-all-local` — no-impact
- [ ] A-015 `infra-port-forward-start` — no-impact
- [ ] A-016 `infra-port-forward-stop` — no-impact
- [ ] A-017 `infra-port-forward-cleanup` — no-impact

## Publish
- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md` with AC coverage, validation evidence, rollback notes
- [ ] P-003 Ensure PR description references `pr_context.md` and closes #203 and #204
