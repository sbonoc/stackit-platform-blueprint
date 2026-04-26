# PR Context

## Summary
- Work item: 2026-04-26-issue-206-contract-consumer-owned-workloads
- Objective: Design the contract schema change that removes hardcoded blueprint-seed workload manifest names from `required_files` and `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`. This is a spec-only deliverable; implementation is deferred to the next work item.
- Scope boundaries: Specification artifacts only (`specs/2026-04-26-issue-206-contract-consumer-owned-workloads/`). No code changes in this PR.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005 (defined, not yet verified — pending implementation)
- Contract surfaces changed: none in this PR (implementation deferred)

## Key Reviewer Files
- Primary files to review first:
  - `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/spec.md` — full requirements and option decision
  - `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/plan.md` — delivery slices for the implementing engineer
  - `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/architecture.md` — problem statement, Mermaid diagram, design rationale
- High-risk files:
  - None in this PR (spec-only). The implementing PR will touch `blueprint/contract.yaml` — review carefully for `required_files` and `source_only_paths` list correctness.

## Validation Evidence
- Required commands executed: `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-206-contract-consumer-owned-workloads`, `make quality-hardening-review`, `make docs-build`, `make docs-smoke`
- Result summary: SDD check clean; hardening review clean; docs build and smoke pass
- Artifact references: `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/` (full SDD artifact set)

## Risk and Rollback
- Main risks: None in this PR (spec-only). Implementation risks documented in `plan.md` Risks and Mitigations section.
- Rollback strategy: Not applicable for a spec-only PR.

## Deferred Proposals
- none
