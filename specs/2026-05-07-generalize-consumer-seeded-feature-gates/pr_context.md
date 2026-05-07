# PR Context

## Summary
- Work item: Generalize Consumer-Seeded Feature Gates (2026-05-07)
- Objective: Replace the bespoke `claude_ai_integration` gate wiring with a generic `consumer_seeded_feature_gates` contract list so future optional seeded files follow the same schema and resolver without requiring new Python code. Adds `make blueprint-seed-feature` for post-init adoption by existing consumers.
- Scope boundaries: Blueprint source tooling only (`blueprint/contract.yaml`, `init_repo_contract.py`, `validate_contract.py`, `seed_feature.py`, make target). No STACKIT runtime resources, no backend app changes, no infra Terraform changes.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, NFR-001–NFR-005, AC-001–AC-009
- Acceptance criteria covered: all AC-001–AC-009 (see `traceability.md`)
- Contract surfaces changed: `blueprint/contract.yaml` (new `consumer_seeded_feature_gates` section, two new `consumer_seeded_paths`, two new `required_files`, one new `toggles` entry); `scripts/lib/quality/test_pyramid_contract.json` (two new unit test files registered)

## Key Reviewer Files
- Primary files to review first:
    - `scripts/lib/blueprint/init_repo_contract.py` — resolver + seeding prune step
    - `scripts/bin/blueprint/validate_contract.py` — `_validate_consumer_seeded_feature_gates` + wiring
    - `blueprint/contract.yaml` — `consumer_seeded_feature_gates` block, new paths, toggle
    - `scripts/bin/blueprint/seed_feature.py` — new CLI
- High-risk files: `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files` — the pruning loop appends to an existing function; risk of path escaping mitigated by using `remove_path` (existing safe wrapper)

## Validation Evidence
- Required commands executed: `make infra-validate`, `make quality-hooks-run`, full pytest suite (351 tests)
- Result summary: `infra-validate` passes; `quality-hooks-run` passes all hooks except expected publish-artifact readiness checks (T-044–T-046 not yet signed); 351 blueprint tests pass (0 failures); Slice 5 T-028–T-031 pass green; Slice 1–4 T-002–T-013 pass green
- Artifact references: `traceability.md` (this spec dir), `tasks.md` (all T-001–T-043 checked)

## Risk and Rollback
- Main risks: (1) A consumer repo with `CLAUDE_AI_ENABLED` absent will have `.github/workflows/claude.yml` removed on next `make blueprint-init-repo` if the file was previously seeded manually — this is the intended behavior but may surprise consumers who did not opt in via the env var. (2) The `seed_feature.py` requires `BLUEPRINT_UPGRADE_SOURCE` at runtime; missing env var results in a failed git clone with a clear error message.
- Rollback strategy: Revert the PR. The `consumer_seeded_feature_gates` YAML section is purely additive; reverting restores the prior behavior. No consumer data is lost (file removal only occurs when the consumer explicitly runs init with the gate disabled).

## Deferred Proposals
- none
