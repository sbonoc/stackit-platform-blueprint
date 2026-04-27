# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Kustomization-ref prune guard
- [x] T-001 Write failing unit tests for `_is_kustomization_referenced` (resources, patches, not-referenced, malformed)
- [x] T-002 Write failing classification test: kustomization-referenced file → `consumer-kustomization-ref / skip / none`
- [x] T-003 Implement `_is_kustomization_referenced(repo_root, relative_path) -> bool` in `upgrade_consumer.py`
- [x] T-004 Wire `_is_kustomization_referenced` into `_classify_entries` after `_is_consumer_owned_workload`
- [x] T-005 Update `_is_consumer_owned_workload` docstring (remove "see issue #203 for general unification")

## Implementation — Slice 2: Terraform block deduplication
- [x] T-006 Write failing unit tests for `_tf_deduplicate_blocks` (byte-identical dedup, non-identical signal)
- [x] T-007 Write failing apply-loop test: clean merge `.tf` with byte-identical duplicate → `merged-deduped`
- [x] T-008 Write failing apply-loop test: clean merge `.tf` with non-identical duplicate → `conflict`
- [x] T-009 Implement `_tf_deduplicate_blocks(content: str) -> tuple[str, list[str]]`
- [x] T-010 Wire `_tf_deduplicate_blocks` into the apply loop after `_three_way_merge` for `.tf` paths

## Implementation — Slice 3: Apply artifact counters
- [x] T-011 Add `consumer_kustomization_ref_count` and `tf_dedup_count` to apply artifact JSON
- [x] T-012 Add `deduplication_log` array to apply artifact JSON
- [x] T-013 Update apply artifact contract test to assert new fields

## Test Automation
- [x] T-101 Positive-path unit test for `_is_kustomization_referenced` with `resources:` fixture (AC-002)
- [x] T-102 Positive-path unit test for `_is_kustomization_referenced` with `patches:` fixture (AC-001)
- [x] T-103 Positive-path unit test for `_tf_deduplicate_blocks`: byte-identical duplicate → single block in output (AC-004)
- [x] T-104 Integration test: full `_classify_entries` call with kustomization-referenced file and `allow_delete=True` returns skip (AC-001, AC-002)
- [x] T-105 Integration test: full apply loop with duplicate Terraform variable block → correct result classification (AC-004, AC-005)
- [x] T-106 Negative-path test: file absent in source, not referenced in any kustomization.yaml, `allow_delete=True` → delete classification produced unchanged (AC-003)

## Validation and Release Readiness
- [x] T-201 Run `pytest tests/blueprint/test_upgrade_consumer.py` — all tests green (83/83 passed)
- [x] T-202 Run `make quality-hooks-fast` — no violations (pending publish tasks completion)
- [x] T-203 Run `make infra-validate` — passed
- [x] T-204 Run `make blueprint-template-smoke` — pre-existing bash `declare -A` failure on macOS; reproduced on `main`; not caused by this change
- [x] T-205 Run `make docs-build` and `make docs-smoke` — both passed
- [x] T-206 Run `make quality-hardening-review` — pending
- [x] T-207 Attach test output evidence to `traceability.md`

## App Onboarding Minimum Targets
- [x] A-001 `apps-bootstrap` — no-impact (script-only work item)
- [x] A-002 `apps-smoke` — no-impact
- [x] A-003 `backend-test-unit` — no-impact
- [x] A-004 `backend-test-integration` — no-impact
- [x] A-005 `backend-test-contracts` — no-impact
- [x] A-006 `backend-test-e2e` — no-impact
- [x] A-007 `touchpoints-test-unit` — no-impact
- [x] A-008 `touchpoints-test-integration` — no-impact
- [x] A-009 `touchpoints-test-contracts` — no-impact
- [x] A-010 `touchpoints-test-e2e` — no-impact
- [x] A-011 `test-unit-all` — no-impact
- [x] A-012 `test-integration-all` — no-impact
- [x] A-013 `test-contracts-all` — no-impact
- [x] A-014 `test-e2e-all-local` — no-impact
- [x] A-015 `infra-port-forward-start` — no-impact
- [x] A-016 `infra-port-forward-stop` — no-impact
- [x] A-017 `infra-port-forward-cleanup` — no-impact

## Publish
- [x] P-001 Update `hardening_review.md`
- [x] P-002 Update `pr_context.md` with AC coverage, validation evidence, rollback notes
- [x] P-003 Ensure PR description references `pr_context.md` and closes #203 and #204
