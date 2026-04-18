# PR Context

## Summary
- Work item: `specs/2026-04-18-docs-ownership-boundary-generated-consumer`
- Objective: enforce one-way generated-consumer ownership for `docs/platform/**` and remove template duplication drift while preserving template-source strict sync.
- Scope boundaries:
  - repo-mode-aware platform docs sync/check + orphan cleanup
  - repo-mode-aware runtime identity and module summary sync/check behavior
  - shared docs repo-mode helper extraction across sync scripts
  - regression tests + SDD/ADR/governance updates

## Requirement Coverage
- Requirements (FR/NFR): `FR-001`, `FR-002`, `FR-003`, `FR-004`, `NFR-OBS-001`, `NFR-OPS-001`, `NFR-REL-001`, `NFR-SEC-001`
- Acceptance criteria (AC): `AC-001`, `AC-002`, `AC-003`, `AC-004`
- Traceability IDs present: `AC-001`, `AC-002`, `AC-003`, `AC-004`, `FR-001`, `FR-002`, `FR-003`, `FR-004`, `NFR-OBS-001`, `NFR-OPS-001`, `NFR-REL-001`, `NFR-SEC-001`

## Key Reviewer Files
- `scripts/lib/docs/sync_platform_seed_docs.py`
- `scripts/lib/docs/sync_runtime_identity_contract_summary.py`
- `scripts/lib/docs/sync_module_contract_summaries.py`
- `scripts/lib/docs/repo_mode.py`
- `tests/blueprint/test_quality_contracts.py`
- `docs/blueprint/architecture/decisions/ADR-20260418-generated-consumer-platform-docs-ownership-boundary.md`
- `AGENTS.backlog.md`
- `AGENTS.decisions.md`

## Validation Evidence
- `python3 -m unittest tests.blueprint.test_quality_contracts tests.docs.test_orchestrate_sync`
- `python3 scripts/lib/docs/sync_platform_seed_docs.py --check`
- `python3 scripts/lib/docs/sync_runtime_identity_contract_summary.py --check`
- `python3 scripts/lib/docs/sync_module_contract_summaries.py --check`
- `make docs-build`
- `make docs-smoke`
- `make infra-validate`
- `make quality-hooks-fast`
- `make quality-hooks-run`
- `make quality-sdd-check-all`
- `make quality-hardening-review`

## Risk and Rollback
- Risk notes:
  - generated-consumer cleanup accidentally removes blueprint seed files.
  - hidden template-coupled paths remain and reintroduce drift failures.
- Mitigations:
  - cleanup targets only paths outside contract-declared `required_seed_files`.
  - summary sync scripts now load `repo_mode` and skip template coupling in generated-consumer mode; tests cover this behavior.
- Rollback notes:
  - revert docs sync script changes + test updates + governance/SDD artifacts in this work item.
  - rerun `make infra-validate` and `make quality-hooks-run`.

## Deferred Proposals
- add a dedicated upgrade/validate artifact section that records template-orphan cleanup actions performed by bootstrap.
