# PR Context

## Summary
- Work item: 2026-05-20-issue-248-workflows-module (issue #248 — 11th of 11 optional modules)
- Objective: Add STACKIT Workflows (managed Apache Airflow) module to the blueprint using the `api_contract` provision driver — no Terraform provider resource exists; all lifecycle operations use the REST API at `https://workflows.api.stackit.cloud/v1alpha`.
- Scope boundaries: STACKIT-lane only (SDD-C-014 exception documented); `test_pyramid_contract.json` registration; `test_contract.py` (39 assertions); full README for `docs/platform/modules/workflows/`.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, NFR-SEC-001, NFR-OPS-001, NFR-A11Y-001 (n/a — no UI changes)
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010
- Contract surfaces changed: `scripts/lib/quality/test_pyramid_contract.json` (new entry), `tests/infra/modules/workflows/test_contract.py` (new file), `docs/platform/modules/workflows/README.md` (stub replaced with full content)

## Key Reviewer Files
- Primary files to review first:
  - `tests/infra/modules/workflows/test_contract.py` — 39-assertion contract test covering all FRs and ACs
  - `scripts/lib/quality/test_pyramid_contract.json` — pyramid registration entry added before test file (pre-commit gate ordering)
  - `docs/platform/modules/workflows/README.md` — full module documentation replacing stub
- High-risk files:
  - `scripts/lib/quality/test_pyramid_contract.json` — pyramid registration ordering (must precede test file commit); verified by pre-commit hook

## Validation Evidence
- Required commands executed: `uv run python3 -m pytest tests/infra/modules/workflows/test_contract.py`, `make test-unit-all`, `make quality-hooks-fast`, `make infra-validate`, `make docs-build && make docs-smoke`, `make quality-hooks-run`, `make quality-hardening-review`
- Result summary: `test_contract.py` — 39 passed in 0.06s; `make test-unit-all` — 1061 passed, 41 subtests; `make infra-validate` — exit 0; `make docs-build && make docs-smoke` — exit 0; `make quality-hooks-run` — all hooks green; `make quality-hardening-review` — exit 0
- Artifact references: `specs/2026-05-20-issue-248-workflows-module/traceability.md`, `specs/2026-05-20-issue-248-workflows-module/hardening_review.md`

## Risk and Rollback
- Main risks: REST API instability — STACKIT Workflows REST API is v1alpha; endpoint or payload changes would require shell script updates. The module is guarded by `WORKFLOWS_ENABLED=false` default so any breakage is opt-in.
- Rollback strategy: Set `WORKFLOWS_ENABLED=false` in the consumer's `.env` and revert the three commits on this branch (pyramid entry, test file, README). No state files are written unless `make infra-stackit-workflows-apply` was run. If the instance was provisioned, run `make infra-stackit-workflows-destroy` before reverting.

## Deferred Proposals
- Local Airflow toggle (not implemented): Optional local lane using Docker Desktop Kubernetes, crossplane, and Helm to deploy an Apache Airflow chart with a git-sync sidecar for DAGs; controlled by a `WORKFLOWS_LOCAL_ENABLED` feature gate. Parked in `AGENTS.backlog.md` under `### on-scope: workflows`. Deferred to keep blast radius minimal and avoid unvalidated local toolchain assumptions.
