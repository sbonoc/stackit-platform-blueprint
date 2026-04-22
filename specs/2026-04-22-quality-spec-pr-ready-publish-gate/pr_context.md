# PR Context

## Summary
- Work item: 2026-04-22-quality-spec-pr-ready-publish-gate
- Objective: add a `quality-spec-pr-ready` make target (script `scripts/bin/quality/check_spec_pr_ready.py`) that detects unfilled scaffold placeholders in the four SDD publish-gate files (plan.md, tasks.md, hardening_review.md, pr_context.md) and wire it into `hooks_fast.sh` with a branch-pattern guard.
- Scope boundaries: `scripts/bin/quality/check_spec_pr_ready.py` (new), `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (quality-spec-pr-ready target added), `make/blueprint.generated.mk` (regenerated), `scripts/bin/quality/hooks_fast.sh` (conditional invocation), `tests/blueprint/test_spec_pr_ready.py` (new), ADR.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: `quality-spec-pr-ready` make target added to both the blueprint makefile template and its rendered output; `hooks_fast.sh` gains a branch-pattern conditional invocation.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_spec_pr_ready.py` — all check functions and main entry point (AC-001 through AC-004)
  - `scripts/bin/quality/hooks_fast.sh` — branch-pattern guard wiring (AC-006)
  - `tests/blueprint/test_spec_pr_ready.py` — 39 tests covering positive-path and all negative-path variants (AC-007)
- High-risk files:
  - `scripts/bin/quality/hooks_fast.sh` — adds a conditional block; existing gate flow unchanged when not on an SDD branch

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-docs-sync-all`, `make infra-contract-test-fast`
- Result summary: all gates green; 39 new tests in `test_spec_pr_ready.py` pass; `quality-spec-pr-ready` runs on this SDD branch via `hooks_fast.sh` and exits 0
- Artifact references: `specs/2026-04-22-quality-spec-pr-ready-publish-gate/traceability.md`, `hardening_review.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: the static label allowlist (`_SCAFFOLD_TASK_SUBJECTS`, `_PLAN_INLINE_FIELDS`, etc.) must be updated when `.spec-kit/templates/blueprint/` scaffold templates change; see hardening review proposal 1.
- Rollback strategy: remove the `quality-spec-pr-ready` target from both makefile files and the `hooks_fast.sh` conditional block; rerun `make blueprint-render-makefile`; the script file can be left in place as it is not invoked except via the make target.

## Deferred Proposals
- Proposal 1 (not implemented): spec template drift test asserting `check_spec_pr_ready.py` constants match `.spec-kit/templates/blueprint/` labels — deferred; requires parsing template markdown or a separate allowlist contract.
- Proposal 2 (not implemented): extend `check_spec_pr_ready.py` to validate `architecture.md` and `context_pack.md` — deferred; already covered by `check_sdd_assets.py`.
