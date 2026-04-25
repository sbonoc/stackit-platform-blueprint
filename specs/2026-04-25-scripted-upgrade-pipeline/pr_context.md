# PR Context

## Summary
- Work item: 2026-04-25-scripted-upgrade-pipeline
- Objective: Replace the `blueprint-consumer-upgrade` runbook (30 open-interpretation decision points) with a deterministic 10-stage pipeline (`make blueprint-upgrade-consumer`) that resolves F-001–F-010 from the v1.0.0→v1.6.0 upgrade and requires no unguided agent judgment.
- Scope boundaries: Python orchestrator scripts (Stages 1, 3, 5, 6, 7, 10), Bash entry wrapper (Stage 2 wiring), Makefile target addition, SKILL.md reduction. No SDD lifecycle skills, no platform CI workflow, no consumer application code.

## Requirement Coverage
- Requirement IDs covered: FR-001–FR-019, NFR-SEC-001, NFR-REL-001, NFR-OPS-001, NFR-OBS-001
- Acceptance criteria covered: AC-001–AC-006
- Contract surfaces changed: new make targets `blueprint-upgrade-consumer` (pipeline entry) and `blueprint-upgrade-consumer-apply` (apply-only stage); new env var `BLUEPRINT_UPGRADE_ALLOW_DELETE` documented with default `true`; new artifact files `artifacts/blueprint/upgrade-residual.md` and `artifacts/blueprint/contract_resolve_decisions.json`.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — 10-stage pipeline entry wrapper with EXIT-trap guarantee for Stage 10
  - `scripts/lib/blueprint/resolve_contract_upgrade.py` — deterministic contract merge rules (FR-005–FR-008)
  - `scripts/lib/blueprint/upgrade_pipeline_preflight.py` — Stage 1 pre-flight checks (FR-001–FR-003)
  - `tests/blueprint/test_upgrade_pipeline.py` — 56 tests covering all FRs/NFRs/ACs
- High-risk files:
  - `make/blueprint.generated.mk` — `blueprint-upgrade-consumer` target redirected to new pipeline; `blueprint-upgrade-consumer-apply` added (additive, backward-compatible)
  - `scripts/lib/blueprint/resolve_contract_upgrade.py` — identity field preservation and required_files merge logic must be correct for all consumers

## Validation Evidence
- Required commands executed: python3 -m pytest tests/blueprint/test_upgrade_pipeline.py (56 new tests, all pass); python3 -m pytest tests/blueprint/ (470 total, 0 regressions, AC-006); make quality-hooks-fast (passes)
- Result summary: all tests green; quality-hooks-fast passes; no regressions in existing upgrade gate tests
- Artifact references: `tests/blueprint/test_upgrade_pipeline.py`, `tests/blueprint/fixtures/contract_resolver/basic_conflict.json`

## Risk and Rollback
- Main risks: contract resolver (Stage 3) must handle all known conflict JSON shapes; mitigated by fixture-driven unit tests. Stage 5 fetch depends on BLUEPRINT_UPGRADE_SOURCE being a valid local git clone; validated by Stage 1 pre-flight.
- Rollback strategy: fully additive — the `blueprint-upgrade-consumer-apply` target preserves the existing apply behavior. Remove `blueprint-upgrade-consumer-pipeline.sh`, the 5 new Python lib modules, and revert `blueprint-upgrade-consumer` target to call `upgrade_consumer.sh` directly. No existing targets, tests, or artifacts are removed.

## Deferred Proposals
- none
