# PR Context

## Summary
- Work item: 2026-04-27-issue-203-204-upgrade-apply-correctness (issues #203 and #204)
- Objective: Fix two correctness bugs in `make blueprint-upgrade-consumer`: (1) prune with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true` deleted consumer-renamed manifests referenced by kustomization.yaml outside `base/apps/`, breaking `kustomize build`; (2) clean 3-way merge of `.tf` files could emit byte-identical duplicate variable blocks, causing `terraform validate` failures.
- Scope boundaries: `scripts/lib/blueprint/upgrade_consumer.py` (new `_is_kustomization_referenced`, `_tf_deduplicate_blocks`, wiring); `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` (schema additions); `tests/blueprint/test_upgrade_consumer.py` (10 new tests). No contract.yaml changes, no infra changes, no CLI flag changes.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: `upgrade_apply.schema.json` — `result` enum adds `merged-deduped`; `summary` object adds `tf_dedup_count` and `consumer_kustomization_ref_count` required fields; `deduplication_log` optional top-level array added.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_is_kustomization_referenced` (new, near line 231), `_tf_deduplicate_blocks` (new, near line 1410), kustomization-ref classify branch (near line 650), apply-loop dedup branch (near line 1693)
  - `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — adds `merged-deduped` enum, `tf_dedup_count`, `consumer_kustomization_ref_count`, `deduplication_log`
- High-risk files: `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` (schema change affects all apply artifact consumers)

## Validation Evidence
- Required commands executed: `pytest tests/blueprint/test_upgrade_consumer.py`, `make infra-validate`, `make docs-build`, `make docs-smoke`; `make blueprint-template-smoke` skipped — pre-existing `declare -A` bash compatibility failure on macOS (reproduced identically on `main`; unrelated to this change)
- Result summary: 83/83 tests passed; `infra-validate` passed; `docs-build` passed; `docs-smoke` passed
- Artifact references: `traceability.md`, `hardening_review.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: (1) `_is_kustomization_referenced` adds filesystem reads per candidate-delete path; acceptable because upgrade runs infrequently and overlay kustomization.yaml files are small. (2) Schema addition to `summary` makes `tf_dedup_count` and `consumer_kustomization_ref_count` required — any consumer that parses the apply artifact JSON must tolerate new fields (additive only; no existing field removed). (3) `_tf_deduplicate_blocks` uses regex-based top-level block scanning; does not require Terraform on PATH; handles nested braces via brace-depth tracking.
- Rollback strategy: Revert the PR. No contract.yaml changes or data migrations involved; the upgrade script is idempotent and state-free.

## Deferred Proposals
- Terraform validate gate: Add `terraform validate` as a post-merge validation step (filed in backlog; requires Terraform on runner PATH and is provider-dependent — deferred).
- Consumer app descriptor (apps.yaml): Long-term principled solution for #203 prune safety; remains parked as noted in spec.
