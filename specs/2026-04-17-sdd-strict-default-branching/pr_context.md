# PR Context

## Summary
- Work item: `specs/2026-04-17-sdd-strict-default-branching`
- Objective: enforce strict-default SDD behavior and dedicated-branch creation for new SDD work items.
- Scope boundaries: governance/contract, scaffold behavior, quality checks, template/doc synchronization, and branch behavior tests.

## Requirement Coverage
- Requirement IDs covered: `FR-001`, `FR-002`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria covered: `AC-001`, `AC-002`
- Contract surfaces changed:
  - `blueprint/contract.yaml` (`spec.spec_driven_development_contract.branch_contract`)
  - `.spec-kit/control-catalog.yaml` (`SDD-C-020`, `SDD-C-021`)
  - `make/blueprint.generated.mk` (`spec-scaffold` branch controls)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/blueprint/spec_scaffold.py`
  - `scripts/bin/quality/check_sdd_assets.py`
  - `blueprint/contract.yaml`
  - `.spec-kit/control-catalog.yaml`
- High-risk files:
  - `make/blueprint.generated.mk`
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`
  - `scripts/templates/consumer/init/.spec-kit/control-catalog.yaml.tmpl`
  - `scripts/templates/consumer/init/AGENTS.md.tmpl`

## Validation Evidence
- Required commands executed:
  - `make quality-sdd-check-all`
  - `make infra-validate`
  - `make quality-hooks-run`
  - `./.venv/bin/python -m pytest -q tests/blueprint/test_spec_scaffold.py tests/infra/test_sdd_asset_checker.py`
- Result summary: all commands passed on branch `codex/sdd-default-enforcement-and-branching` before opening draft PR #139.
- Artifact references:
  - `specs/2026-04-17-sdd-strict-default-branching/traceability.md`
  - `specs/2026-04-17-sdd-strict-default-branching/evidence_manifest.json`
  - `specs/2026-04-17-sdd-strict-default-branching/hardening_review.md`

## Risk and Rollback
- Main risks:
  - stricter defaults increase workflow friction for users who intentionally stay on current branch.
  - branch-contract drift can reappear if contract/template/checker updates diverge in future changes.
- Rollback strategy:
  - revert commit `df7595c` (or revert PR #139) to restore previous scaffold and validation behavior.

## Deferred Proposals
- Proposal 1 (not implemented): add an explicit retrospective-work-item mode in the checker for completed work where `SPEC_READY` remains false pending formal sign-offs.
- Proposal 2 (not implemented): add checker regression tests for `SPEC_READY=true` paths with unresolved-token field-label exclusions.
