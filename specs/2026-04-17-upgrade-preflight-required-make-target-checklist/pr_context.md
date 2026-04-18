# PR Context

## Summary
- Work item: `specs/2026-04-17-upgrade-preflight-required-make-target-checklist`
- Objective: detect missing contract-required consumer-owned Make targets during upgrade preflight with deterministic remediation guidance.
- Scope boundaries: upgrade planner diagnostics, unit regressions, and consumer upgrade docs sync.

## Requirement Coverage
- Requirements (FR/NFR): `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria (AC): `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`
- Contract surfaces changed:
  - `required_manual_actions[*].dependency_of`
  - `required_manual_actions[*].reason`
  - consumer upgrade docs around `upgrade_preflight.json` interpretation

## Key Reviewer Files
- `scripts/lib/blueprint/upgrade_consumer.py`
- `tests/blueprint/test_upgrade_consumer.py`
- `docs/platform/consumer/quickstart.md`
- `docs/platform/consumer/troubleshooting.md`
- `scripts/templates/blueprint/bootstrap/docs/platform/consumer/quickstart.md`
- `scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md`
- `specs/2026-04-17-upgrade-preflight-required-make-target-checklist/spec.md`
- `specs/2026-04-17-upgrade-preflight-required-make-target-checklist/traceability.md`

## Validation Evidence
- `python3 -m unittest tests.blueprint.test_upgrade_consumer` (22 tests passed)
- `python3 -m unittest tests.blueprint.test_upgrade_preflight` (4 tests passed)
- `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check` (pass)
- `python3 scripts/lib/docs/sync_platform_seed_docs.py --check` (pass)
- `make quality-hooks-fast` (pass; includes `infra-validate` and `infra-contract-test-fast`)
- `make quality-hardening-review` (pass)

## Risk and Rollback
- Main risks:
  - legacy consumer repos may now see larger manual-action lists when many required targets are missing.
- Rollback strategy:
  - revert planner/test/docs changes and rerun `python3 -m unittest tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_preflight && make quality-hooks-fast`.

## Deferred Proposals
- Add optional boilerplate/skeleton target snippets to required manual actions once schema extension is explicitly approved.
