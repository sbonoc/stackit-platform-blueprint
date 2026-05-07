# PR Context

## Summary
- Work item: Generalize Consumer-Seeded Feature Gates (2026-05-07)
- Objective: Replace the bespoke `claude_ai_integration` gate wiring with a generic `consumer_seeded_feature_gates` contract list so future optional seeded files follow the same schema and resolver without requiring new Python code. Adds `make blueprint-seed-feature` for post-init adoption by existing consumers. Adds `make blueprint-feature-gate-status` so consumers and coding agents automatically discover and adopt new optional features after upgrades via machine-readable `AGENTS.backlog.md` entries.
- Scope boundaries: Blueprint source tooling only (`blueprint/contract.yaml`, `init_repo_contract.py`, `validate_contract.py`, `seed_feature.py`, `feature_gate_status.py`, make targets, `upgrade_consumer_postcheck.sh`, `blueprint-consumer-upgrade/SKILL.md`). No STACKIT runtime resources, no backend app changes, no infra Terraform changes.

## Requirement Coverage
- Requirement IDs covered: REQ-001–REQ-015, NFR-001–NFR-005, AC-001–AC-013
- Acceptance criteria covered: all AC-001–AC-013 (see `traceability.md`)
- Contract surfaces changed: `blueprint/contract.yaml` (new `consumer_seeded_feature_gates` section, two new `consumer_seeded_paths`, two new `required_files`, one new `toggles` entry); `scripts/lib/quality/test_pyramid_contract.json` (three new unit test files registered); `make/blueprint.generated.mk` (two new targets: `blueprint-seed-feature`, `blueprint-feature-gate-status`); `upgrade_consumer_postcheck.sh` (non-blocking `feature_gate_status.py` call added after metrics emission); `.agents/skills/blueprint-consumer-upgrade/SKILL.md` (new Step 6 and backlog entry format documentation)

## Key Reviewer Files
- Primary files to review first:
    - `scripts/lib/blueprint/init_repo_contract.py` — resolver + seeding prune step
    - `scripts/bin/blueprint/validate_contract.py` — `_validate_consumer_seeded_feature_gates` + wiring
    - `blueprint/contract.yaml` — `consumer_seeded_feature_gates` block, new paths, toggle
    - `scripts/bin/blueprint/seed_feature.py` — new CLI for post-init adoption
    - `scripts/bin/blueprint/feature_gate_status.py` — new discovery + backlog upsert CLI
    - `scripts/bin/blueprint/upgrade_consumer_postcheck.sh` — non-blocking gate status call added
    - `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — updated workflow (Step 6) + backlog entry docs
- High-risk files: `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files` — the pruning loop appends to an existing function; risk of path escaping mitigated by using `remove_path` (existing safe wrapper). `upgrade_consumer_postcheck.sh` wiring uses `|| true` to ensure non-blocking semantics.

## Validation Evidence
- Required commands executed: `make infra-validate`, `make quality-hooks-run`, full pytest suite
- Result summary: `infra-validate` passes; `quality-hooks-run` passes all hooks except pre-existing `infra-contract-test-fast` yaml-dep failure (confirmed pre-existing on commit `1d7b98e`, unrelated to this PR); Slices 1–4 (22 tests) pass green with homebrew Python; Slices 5+8 (10 tests) pass green with pyenv Python 3.14.3; Slice 8 T-048–T-052 confirmed red → green
- Artifact references: `traceability.md` (this spec dir), `tasks.md` (all T-001–T-060 checked)

## Risk and Rollback
- Main risks: (1) A consumer repo with `CLAUDE_AI_ENABLED` absent will have `.github/workflows/claude.yml` removed on next `make blueprint-init-repo` if the file was previously seeded manually — this is the intended behavior but may surprise consumers who did not opt in via the env var. (2) The `seed_feature.py` requires `BLUEPRINT_UPGRADE_SOURCE` at runtime; missing env var results in a failed git clone with a clear error message. (3) `feature_gate_status.py` runs non-blocking in postcheck — if it crashes silently, the backlog is not updated; the `|| true` guard ensures postcheck result is never affected.
- Rollback strategy: Revert the PR. The `consumer_seeded_feature_gates` YAML section is purely additive; reverting restores the prior behavior. No consumer data is lost (file removal only occurs when the consumer explicitly runs init with the gate disabled). `AGENTS.backlog.md` entries from `feature_gate_status.py` are harmless if left behind after rollback.

## Deferred Proposals
- none
