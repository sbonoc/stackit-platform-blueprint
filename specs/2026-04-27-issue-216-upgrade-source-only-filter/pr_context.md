# PR Context

## Summary
- Work item: issue-216 — Fix resolve_contract_upgrade Stage 3 source_only wholesale copy bug
- Objective: Restore `_filter_source_only` Phase 1+2 semantics so consumers with `specs/`, `CLAUDE.md`, etc. no longer fail `infra-validate` with "file must be absent" errors after an upgrade.
- Scope boundaries: Python script fix only — `scripts/lib/blueprint/resolve_contract_upgrade.py`; new test file `tests/blueprint/test_resolve_contract_upgrade.py`; test pyramid registration in `scripts/lib/quality/test_pyramid_contract.json`.

## Requirement Coverage
- Requirement IDs covered: FR-009
- Acceptance criteria covered: AC-001 (Phase 1 drop specs/), AC-002 (Phase 1 drop CLAUDE.md), AC-003 (Phase 2 carry-forward consumer additions on disk), AC-005 (no-conflict regression guard)
- Contract surfaces changed: `ContractResolveResult` dataclass extended with `dropped_source_only` and `kept_consumer_source_only` fields (additive, backward-compatible); `contract_resolve_decisions.json` gains two new keys.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/resolve_contract_upgrade.py` — `_filter_source_only` function (new) and FR-009 wiring inside `resolve_contract_conflict`
  - `tests/blueprint/test_resolve_contract_upgrade.py` — 4 regression tests
- High-risk files: none (pure additive change to an isolated helper; no external dependencies; no HTTP or Makefile scope)

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/blueprint/test_resolve_contract_upgrade.py -v`, `python3 -m pytest tests/blueprint/ -q`, `make quality-sdd-check`, `make quality-hooks-run`
- Result summary: 4/4 new tests green; full suite 623 passed 2 pre-existing failures (unrelated template FileNotFoundError); `quality-sdd-check` clean; `quality-hooks-run` clean.
- Artifact references: test output confirmed in CI; `contract_resolve_decisions.json` schema extended for observability.

## Risk and Rollback
- Main risks: consumers that previously relied on source `source_only` being passed wholesale (no such legitimate use case exists — the bug caused infra-validate failures); Phase 2 carry-forward only applies when file actually exists on disk.
- Rollback strategy: revert `resolve_contract_upgrade.py` to pre-PR state; the bug will reappear but `infra-validate` errors will make the regression visible immediately.

## Deferred Proposals
- none
