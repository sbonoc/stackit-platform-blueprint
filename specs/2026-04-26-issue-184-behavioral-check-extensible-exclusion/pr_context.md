# PR Context

## Summary
- Work item: 2026-04-26-issue-184-behavioral-check-extensible-exclusion
- Objective: Make the shell behavioral check symbol exclusion set extensible via `blueprint/contract.yaml` so consumers can suppress project-specific false-positive unresolved-symbol warnings without patching blueprint-managed code.
- Scope boundaries: Python and YAML changes only. No HTTP routes, managed services, or external APIs touched. Changes are entirely within the upgrade pipeline bounded context.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: `blueprint/contract.yaml` gains optional `spec.upgrade.behavioral_check.extra_excluded_tokens` array field (absent = empty list, no breaking change)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `extra_excluded_tokens` param, `extra_excluded_count` field, `_find_unresolved_call_sites` excluded kwarg
  - `scripts/lib/blueprint/contract_schema.py` — `BehavioralCheckUpgradeContract`, `UpgradeContract` dataclasses, `BlueprintContract.upgrade` field, loader
  - `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — reads contract field, passes to `run_behavioral_check`
  - `tests/blueprint/test_upgrade_shell_behavioral_check.py` — `TestExtraExcludedTokens` (AC-001–AC-007), `TestPostcheckReadsExtraTokensFromContract`
- High-risk files:
  - `scripts/lib/blueprint/contract_schema.py` — hand-rolled YAML parser; new optional `spec.upgrade` key must not break existing contract loading. Validated by 516 blueprint suite tests passing.

## Validation Evidence
- Required commands executed: `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py`, `pytest tests/blueprint/`, `make quality-sdd-check`, `make quality-hooks-run`
- Result summary: 27 behavioral-check tests pass (7 new); 516 blueprint suite tests pass, zero regressions; `make quality-sdd-check` passes; `make quality-hooks-run` passes
- Artifact references: none — this work item emits no new runtime artifacts

## Risk and Rollback
- Main risks: `contract_schema.py` hand-rolled YAML parser must handle absent `spec.upgrade` key — mitigated by `spec.get("upgrade") or {}` defensive read and confirmed by `test_absent_key_yields_empty_frozenset`. Token values are never executed (NFR-SEC-001 — only used for set membership check).
- Rollback strategy: revert `upgrade_consumer_postcheck.py` to remove the `extra_excluded: frozenset` block (9 lines); the `run_behavioral_check` signature change is backward-compatible so no other callers break. `contract_schema.py` revert removes the two new dataclasses and the `upgrade` field from the loader.

## Deferred Proposals
- None — all requirements are fully implemented in this work item.
