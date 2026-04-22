# PR Context

## Summary
- Work item: 2026-04-22-issue-131-blueprint-uplift-status
- Objective: Add `make blueprint-uplift-status` as a blueprint-native command for generated-consumer repos to detect which tracked upstream blueprint issues are now CLOSED and which local backlog lines still require convergence action.
- Scope boundaries: new `scripts/lib/blueprint/uplift_status.py`, new `scripts/bin/blueprint/uplift_status.sh`, make target in both makefile files, 32 unit tests, docs reference entry, ADR, SDD artifacts. No existing scripts, targets, or contracts are modified.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: `blueprint-uplift-status` make target added to `make/blueprint.generated.mk` and template; `BLUEPRINT_UPLIFT_REPO`, `BLUEPRINT_UPLIFT_BACKLOG_PATH`, `BLUEPRINT_UPLIFT_STATUS_PATH`, `BLUEPRINT_UPLIFT_STRICT` env vars added to shell wrapper.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/uplift_status.py` — backlog parsing, gh query, classification, artifact write, strict mode
  - `scripts/bin/blueprint/uplift_status.sh` — env var wiring, strict mode flag, metrics emission
- High-risk files:
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — new target propagated to all generated consumers on next upgrade

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/blueprint/test_uplift_status.py -v`, `make quality-hooks-fast`, `make infra-validate`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`, `SPEC_SLUG=2026-04-22-issue-131-blueprint-uplift-status make quality-spec-pr-ready`
- Result summary: 32/32 tests pass (5 additional tests from PR review fixes: aligned reachability, mismatched ID guard, bare-slash repo validation, checked_ids tracking, full-run aligned integration); all quality gates green
- Artifact references: `specs/2026-04-22-issue-131-blueprint-uplift-status/traceability.md`, `specs/2026-04-22-issue-131-blueprint-uplift-status/evidence_manifest.json`

## Risk and Rollback
- Main risks: `BLUEPRINT_UPLIFT_REPO` defaults to placeholder values in freshly initialized consumers — surfaces as `query_failures` in artifact; non-fatal without `--strict`.
- Rollback strategy: revert the commit; no persistent cluster or infra state is introduced.

## Deferred Proposals
- Proposal 1 (not implemented): optional integration of `blueprint-uplift-status` into `blueprint-upgrade-consumer-validate` behind a `BLUEPRINT_UPLIFT_STRICT` gate — deferred to a follow-up work item pending consumer buy-in on the strict threshold as a blocking gate.
