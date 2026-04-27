# PR Context

## Summary
- Work item: 2026-04-26-issue-206-contract-consumer-owned-workloads
- Objective: Remove hardcoded blueprint-seed workload manifest names from `required_files` and `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`; add them to `source_only_paths`. Consumers who rename their workload manifests will no longer need to re-patch `blueprint/contract.yaml` after every blueprint upgrade.
- Scope boundaries: `blueprint/contract.yaml` (and its bootstrap template mirror), six new/updated tests, auto-generated `contract_metadata.generated.md`, ADR, and full SDD artifact set.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001 ✓ AC-002 ✓ AC-003 ✓ AC-004 ✓ AC-005 ✓ (all verified by automated tests)
- Contract surfaces changed: `blueprint/contract.yaml` — two list modifications (remove 4 seed paths from `required_files` + `required_paths_when_enabled`; add them to `source_only_paths`)

## Key Reviewer Files
- Primary files to review first:
  - `blueprint/contract.yaml` — lines ~536–539 (source_only additions); lines ~1014–1015 (required_paths_when_enabled trimmed to 2 entries)
  - `tests/blueprint/test_upgrade_consumer.py` — classes `SeedManifestContractContentTests`, `SeedManifestUpgradePlannerTests`, `SeedManifestInitSeedingTests`
  - `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/spec.md` — full requirements and option decision
  - `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md` — status: approved
- Supporting files:
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — bootstrap template mirror (same 3 changes)
  - `docs/reference/generated/contract_metadata.generated.md` — auto-regenerated after contract.yaml edit
  - `tests/blueprint/test_upgrade_fixture_matrix.py` — `APP_RUNTIME_REQUIRED_FILES` updated (seed paths removed; now source-only/skip)
  - `tests/blueprint/contract_refactor_governance_structure_cases.py` — `source_only_paths` expected set updated
  - `tests/blueprint/test_optional_runtime_contract_validation.py` — two pre-existing test bugs fixed (wrong section substitution + wrong error message string)

## Validation Evidence
- Required commands executed: 8 commands — all PASS (details below)
  - `make quality-hooks-fast` — PASS (129 infra-contract-test-fast tests)
  - `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-206-contract-consumer-owned-workloads` — PASS
  - `make quality-hardening-review` — PASS
  - `make test-unit-all` — PASS
  - `python3 -m pytest tests/blueprint/ -q` — PASS (551 tests, 29 subtests, 0 failures)
  - `make docs-build` — PASS
  - `make docs-smoke` — PASS
  - `make quality-docs-check-changed` — PASS
- Result summary: All quality gates green; 551 blueprint tests pass; docs build and smoke pass

## Risk and Rollback
- Main risks: seed file auto-recovery loss; content drift (both accepted tradeoffs — see details below)
  - Consumers who relied on upgrade to re-create the 4 seed files (e.g. after accidental deletion) lose that auto-recovery. Mitigation: `make blueprint-init-repo` still seeds them; manual re-creation is straightforward.
  - Blueprint content improvements to the 4 seed files (health probes, resource limits, etc.) will not propagate automatically to consumers after this ships. This is the accepted tradeoff (see spec.md Informative Notes). Follow-up 3 in traceability.md tracks the `OPERATION_ADVISORY` mechanism needed for long-term advisory.
- Rollback strategy: Revert the three list modifications in `blueprint/contract.yaml` (and its bootstrap template mirror). No database or data migration. Consumer repos that have already upgraded will have the updated contract; they can re-add the 4 paths to `required_files` and `required_paths_when_enabled` manually if needed (one-time action per consumer).

## Deferred Proposals
- Follow-up 1: Option B — `consumer_workload_manifest_paths` schema field for explicit preflight validation of consumer-named manifests. Parked — subsumed by existing `consumer app descriptor (apps.yaml, consumer_seeded)` entry in `AGENTS.backlog.md` (trigger: on-scope: blueprint), which is the broader realisation of Option B. Prerequisites (#206 + #207) now both shipped; consumer app descriptor entry updated accordingly.
- Follow-up 2: Verify init seeding not broken when removing paths from `required_paths_when_enabled`. Resolved — addressed by IMPL T-106 (`test_seed_manifest_templates_exist_in_infra_bootstrap`); no open action.
- Follow-up 3: Source-only seed change advisory (`OPERATION_ADVISORY`) — parked in `AGENTS.backlog.md` as `proposal(issue-206): source-only seed change advisory`. Trigger updated at PR #211 close: `after:` trigger (now satisfied) removed; `on-scope: blueprint` retained as ongoing trigger. No open action until blueprint maintainers next improve seed workload content.
