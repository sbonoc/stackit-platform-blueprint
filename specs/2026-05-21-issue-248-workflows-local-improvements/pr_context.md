# PR Context

## Summary
- Work item: 2026-05-21-issue-248-workflows-local-improvements
- Objective: Automate port-forward in the local-workflows smoke script and add DAG development setup guidance (Python 3.12 venv + repository structure convention).
- Scope boundaries: Two additive changes: (1) `local_workflows_smoke.sh` now manages its own port-forward lifecycle via `port_forward.sh`; (2) README gains "DAG Development Setup" section + `infra-local-workflows-dags-venv` make target.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-A11Y-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002, NFR-OPS-003
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010
- Contract surfaces changed: `blueprint/modules/local-workflows/module.contract.yaml` — added `dags-venv` make target key

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/infra/local_workflows_smoke.sh` — port-forward lifecycle integration
  - `scripts/bin/infra/local_workflows_dags_venv.sh` — new script, WORKFLOWS_LOCAL_ENABLED guard
  - `scripts/bin/blueprint/render_makefile.sh` — new phony + target block + optional_target_count for local-workflows
- High-risk files:
  - `scripts/bin/infra/local_workflows_smoke.sh` — stop_port_forward placement on each exit path must be verified

## Validation Evidence
- Required commands executed: `make quality-hardening-review` (pass), `make quality-hooks-fast` (pass after publish artifact fill), skip path verified for both scripts with WORKFLOWS_LOCAL_ENABLED=false
- Result summary: All automated gates pass. AC-002 and AC-008 (WORKFLOWS_LOCAL_ENABLED=false skip paths) verified locally. AC-001, AC-003, AC-004 require a running local-workflows stack and are documented as requiring manual verification.
- Artifact references: `hardening_review.md`, `traceability.md`

## Risk and Rollback
- Main risks: If Python 3.12 is not yet installed via uv on a developer machine, `make infra-local-workflows-dags-venv` will fail with a uv error; README documents `uv python install 3.12` as the prerequisite.
- Rollback strategy: Revert `local_workflows_smoke.sh` (remove three port-forward calls + source line); delete `local_workflows_dags_venv.sh`; revert `render_makefile.sh` local-workflows case and optional_target_count; revert README and bootstrap template; revert module.contract.yaml dags-venv key.

## Deferred Proposals
- none
