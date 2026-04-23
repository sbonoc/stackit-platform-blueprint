# PR Context

## Summary
- Work item: 2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard
- Objective: Fix `ensure_infra_template_file` and `ensure_infra_rendered_file` to skip recreation of paths declared as `consumer_seeded` in `blueprint/contract.yaml`, so consumers can delete blueprint placeholder manifests without bootstrap recreating them on every fresh checkout.
- Scope boundaries: two local functions in `scripts/bin/infra/bootstrap.sh`; one new structural test; SDD artifacts. No new make targets, no new env vars, no consumer-facing doc changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003
- Contract surfaces changed: `infra_consumer_seeded_skip_count` metric added to bootstrap stdout (additive, non-breaking).

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/infra/bootstrap.sh` — the two guard blocks added to `ensure_infra_template_file` and `ensure_infra_rendered_file`
- High-risk files:
  - none — the change is a pure additive guard; non-seeded and init_managed path behavior is unchanged.

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k infra_bootstrap -v`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`, `SPEC_SLUG=2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard make quality-spec-pr-ready`
- Result summary: 2/2 targeted tests pass; all quality gates green
- Artifact references: `specs/2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard/traceability.md`, `specs/2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard/evidence_manifest.json`

## Risk and Rollback
- Main risks: consumer miscategorizes an actually-managed path as `consumer_seeded`; mitigated by explicit declaration being intentional and the consumer owning the decision.
- Rollback strategy: revert the commit; no persistent cluster or infra state is introduced.

## Deferred Proposals
- Proposal 1 (not implemented): live integration test using a generated-consumer fixture — deferred; structural test is sufficient for the fixed shell function scope.
