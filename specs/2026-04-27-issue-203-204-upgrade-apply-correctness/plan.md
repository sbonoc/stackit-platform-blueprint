# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: both fixes add one predicate function each; no new abstractions or wrapper layers
- Anti-abstraction gate: direct `yaml.safe_load` and `re` usage; no new base classes or protocols
- Integration-first testing gate: unit tests for `_is_kustomization_referenced` and `_tf_deduplicate_blocks` are defined before implementation; positive-path assertions required for both
- Positive-path filter/transform test gate: AC-001 and AC-002 assert that a matching kustomization ref returns a non-delete classification with a non-empty ownership field; AC-004 asserts that a byte-identical duplicate block produces a deduplicated file with correct content
- Finding-to-test translation gate: both bugs are reproducible — test fixtures replicate the exact dhe-marketplace scenario (rename + prune; duplicate variable block after merge)

## Delivery Slices

### Slice 1 — Kustomization-ref prune guard (REQ-001, REQ-002, REQ-003, NFR-SEC-001, NFR-REL-001, AC-001–AC-003, AC-006)
Red→green TDD order:
1. Write failing tests: `_is_kustomization_referenced` returns True for a file in `resources:`, True for `patches:`, False when not referenced, False + warning when kustomization is malformed.
2. Write failing classification test: file absent in source, referenced in kustomization.yaml, `allow_delete=True` → `consumer-kustomization-ref / skip / none`.
3. Implement `_is_kustomization_referenced` in `upgrade_consumer.py`.
4. Wire into `_classify_entries` after `_is_consumer_owned_workload` check.
5. All Slice 1 tests green.

### Slice 2 — Terraform block deduplication (REQ-004, REQ-005, REQ-006, NFR-OBS-001, AC-004, AC-005)
Red→green TDD order:
1. Write failing tests: `_tf_deduplicate_blocks` returns deduplicated content + removed-block list for byte-identical duplicates; returns non-identical-duplicate signal for differing content.
2. Write failing apply-loop test: clean merge of `.tf` file with byte-identical duplicate variable block → `result="merged-deduped"`, file on disk has one copy.
3. Write failing apply-loop test: clean merge of `.tf` file with non-identical duplicate variable block → `result="conflict"`, conflict artifact written, file not modified.
4. Implement `_tf_deduplicate_blocks`.
5. Wire into apply loop after `_three_way_merge` for `.tf` paths.
6. All Slice 2 tests green.

### Slice 3 — Apply artifact counters (NFR-OPS-001)
1. Add `consumer_kustomization_ref_count` and `tf_dedup_count` to apply artifact JSON.
2. Add `deduplication_log` array to apply artifact JSON.
3. Update apply artifact contract test to assert new fields present.

### Slice 4 — Bridge guard comment update (housekeeping)
1. Update `_is_consumer_owned_workload` docstring to remove the "see issue #203 for general unification" note; the general fix now exists.

## Change Strategy
- Migration/rollout sequence: all changes in `upgrade_consumer.py` and `test_upgrade_consumer.py`; no consumer-facing API or contract changes
- Backward compatibility policy: fully backward compatible — new classification only fires when a file is kustomization-referenced; Terraform dedup only activates on `.tf` files after a clean merge
- Rollback plan: revert the two functions and their call sites; no schema migrations or data files affected

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_upgrade_consumer.py`
- Contract checks: apply artifact JSON schema (additive fields); existing postcheck tests confirm no regression
- Integration checks: `make quality-hooks-fast`, `make infra-validate`
- E2E checks: `make blueprint-template-smoke`

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
- Notes: script-only change in the upgrade pipeline; no app onboarding targets modified

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-issue-203-204-upgrade-apply-correctness.md` (created in intake)
- Consumer docs updates: none — behavior is additive; consumers benefit automatically
- Mermaid diagrams updated: flowchart in ADR (included)
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes touched
- Publish checklist:
  - include AC-001–AC-006 test evidence
  - include apply artifact JSON schema diff
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `consumer_kustomization_ref_count` and `tf_dedup_count` in apply artifact; `deduplication_log` array for Terraform events
- Alerts/ownership: non-zero `tf_dedup_count` warrants consumer review of `deduplication_log`
- Runbook updates: none required

## Risks and Mitigations
- Risk 1: kustomization.yaml parse errors could mask a genuine prune-protection need → mitigated by NFR-REL-001 (default False + stderr warning)
- Risk 2: regex-based Terraform block scanner misses an edge case → mitigated by emitting conflict artifact rather than writing potentially corrupted content
