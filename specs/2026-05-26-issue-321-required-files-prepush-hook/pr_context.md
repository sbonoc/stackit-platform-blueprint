# PR Context

## Summary
- Work item: 2026-05-26-issue-321-required-files-prepush-hook
- Objective: Surface stale `blueprint/contract.yaml` `required_files` entries at pre-push so developers catch the gap locally rather than first in the `blueprint-quality` CI job.
- Scope boundaries: `validate_contract.py` (new `--required-files-only` flag), `blueprint.generated.mk.tmpl` + `make/blueprint.generated.mk` (new target + PHONY), `.pre-commit-config.yaml` (blueprint own + bootstrap template). No runtime logic, API surface, or existing check behaviour changed.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Contract surfaces changed: new `quality-validate-contract-required-files` make target added to generated Makefile; new always-run pre-push hook added to both `.pre-commit-config.yaml` files.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/blueprint/validate_contract.py` — `--required-files-only` flag and fast path (stat-only, no shellcheck or makefile rendering)
  - `.pre-commit-config.yaml` — new always-run pre-push hook before `quality-validate-branch`
  - `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — consumer bootstrap mirror of the same hook
- Supporting files:
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — new target definition + PHONY entry
  - `make/blueprint.generated.mk` — regenerated from template (same changes)

## Validation Evidence
- Required commands executed: make quality-validate-contract-required-files (passed); python3 validate_contract.py --required-files-only (passed); negative test with missing required file (exit 1 with clear error); make quality-hooks-fast (passed)
  - `python3 scripts/bin/blueprint/validate_contract.py --required-files-only` — exit 0 on clean tree
  - removing `.github/CODEOWNERS` temporarily → exit 1, `missing file: .github/CODEOWNERS`
  - `make quality-validate-contract-required-files` — exit 0
  - `make quality-hooks-fast` — all checks passed
- Result summary: new flag and hook behave correctly on both positive and negative paths.
- Artifact references: none

## Risk and Rollback
- Main risks: the always-run pre-push hook adds ~50ms to every push in consumer repos (stat-check on ~480 files); negligible. No existing hook behaviour is changed.
- Rollback strategy: revert the commit; the hook is additive only.

## Deferred Proposals
- Proposal 1 (not implemented): extend the hook to also check `required_paths` (directories) — lower urgency since directory removal is caught by kustomization checks; deferred to a follow-up.
