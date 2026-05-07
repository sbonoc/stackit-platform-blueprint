# PR Context

## Summary
- Work item: 2026-05-07-issue-248-postgres-module
- Objective: Elevate the postgres module from partial scaffold to production-grade optional module: correct execution class (`fallback_runtime` on local lane), Secret-backed credentials (no plaintext in rendered Helm values), working STACKIT Terraform standalone module (`stackit_postgresflex_*` resources), and complete module documentation with verified test coverage.
- Scope boundaries: `scripts/lib/infra/postgres.sh`, `scripts/lib/infra/module_execution.sh`, `scripts/bin/infra/postgres_{apply,destroy,smoke}.sh`, `scripts/bin/infra/bootstrap.sh`, `infra/local/helm/postgres/values.yaml`, `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml`, `infra/cloud/stackit/terraform/modules/postgres/`, `docs/platform/modules/postgres/README.md`, `tests/infra/modules/postgres/`. No make target changes; no API contract changes; no consumer onboarding changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-014
- Contract surfaces changed: `OPTIONAL_MODULE_EXECUTION_CLASS` changes from `provider_backed` to `fallback_runtime` for local lane. Runtime state file keys renamed: `database` → `db_name`, `username` → `user` (consumers reading raw `artifacts/infra/postgres_runtime.env` must update key references; ESO consumers unaffected).

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/postgres.sh` — three new secret lifecycle functions; `postgres_render_values_file` no longer passes plaintext credentials
  - `scripts/lib/infra/module_execution.sh` — local lane class fix (`provider_backed` → `fallback_runtime`)
  - `infra/local/helm/postgres/values.yaml` — `auth.existingSecret` replaces `auth.username`/`auth.password`
  - `infra/cloud/stackit/terraform/modules/postgres/main.tf` — full postgresflex resource implementation
- High-risk files: `scripts/bin/infra/postgres_apply.sh` (state key rename `database`→`db_name`, `username`→`user` + reconcile ordering), `scripts/bin/infra/postgres_destroy.sh` (new postgres.sh source + secret delete after helm uninstall)

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/infra/modules/postgres/ -v` (19/19 PASSED), `python3 -m pytest tests/infra/test_tooling_contracts.py -k postgres` (4/4 PASSED), `python3 -m pytest tests/infra/test_tooling_contracts.py` (104/104 PASSED), `make quality-docs-check-changed` (PASS), `make infra-validate` (PASS), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (all checks PASSED)
- Result summary: 21 new tests added, all green. No regressions across 104 tooling contract tests. Pyramid ratios within thresholds.
- Artifact references: `specs/2026-05-07-issue-248-postgres-module/traceability.md`

## Risk and Rollback
- Main risks: (1) `auth.existingSecret` requires K8s Secret before pod start — guaranteed by `postgres_reconcile_runtime_secret` running before helm upgrade; (2) state key rename (`database`→`db_name`, `username`→`user`) breaks direct raw-state-file readers — migration path documented in spec.md § Contract Changes and ADR D-4; ESO consumers unaffected.
- Rollback strategy: Revert the PR branch. If the Secret was already created by a previous apply, delete it manually: `kubectl delete secret -n data blueprint-postgres-auth`. No persistent data is affected.

## Deferred Proposals
- none
