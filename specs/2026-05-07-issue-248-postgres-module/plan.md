# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: implement all missing pieces additively; no new abstractions beyond the three Secret lifecycle functions already established by opensearch/object-storage.
- Anti-abstraction gate: reuse existing framework functions (`apply_optional_module_secret_from_literals`, `delete_optional_module_secret`, `render_optional_module_values_file`); no new wrappers.
- Integration-first testing gate: write all tests RED in Slice 1, then implement GREEN in Slices 2–4.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic.
- Finding-to-test translation gate: not applicable — no reproducible pre-PR smoke failures identified; existing scripts are structurally sound.

## Delivery Slices

### Slice 1: Tests RED
Write all test files with assertions that will fail against the current scaffold. Run to confirm RED state before implementing.
- `tests/infra/modules/postgres/test_postgres_module.py` — unit assertions for Terraform module structure, Helm values contract, version pins, apply/destroy/smoke script invariants, lib function presence.
- `tests/infra/modules/postgres/test_contract.py` — contract fixture assertions for runtime state keys.
- `tests/infra/test_tooling_contracts.py` — add two tests: `test_optional_module_execution_resolves_local_fallback_modes_for_postgres` and `test_optional_module_execution_resolves_stackit_provider_backed_postgres_modes`.
- `scripts/lib/quality/test_pyramid_contract.json` — register both new test files under `unit` scope.

### Slice 2: Execution Class Fix + Secret-Backed Credentials
- `scripts/lib/infra/module_execution.sh` — change local lane class from `provider_backed` to `fallback_runtime` for `postgres:plan|apply` and `postgres:destroy`.
- `scripts/lib/infra/postgres.sh` — add `postgres_credential_secret_name()`, `postgres_reconcile_runtime_secret()`, `postgres_delete_runtime_secret()`; update `postgres_render_values_file()` to remove plaintext credential bindings and add `POSTGRES_CREDENTIAL_SECRET_NAME`.
- `infra/local/helm/postgres/values.yaml` — replace `auth.username`/`auth.password` with `auth.existingSecret: blueprint-postgres-auth`.
- `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml` — same change (use `{{POSTGRES_CREDENTIAL_SECRET_NAME}}`).
- `scripts/bin/infra/postgres_apply.sh` — call `postgres_reconcile_runtime_secret` before `run_helm_upgrade_install` in `helm)` case.
- `scripts/bin/infra/postgres_destroy.sh` — call `postgres_delete_runtime_secret` after `run_helm_uninstall` in `helm)` case; add `--ignore-not-found`.
- `scripts/bin/infra/bootstrap.sh` — replace plaintext credential bindings with `POSTGRES_CREDENTIAL_SECRET_NAME` in `postgres)` case.

### Slice 3: STACKIT Terraform Module
- `infra/cloud/stackit/terraform/modules/postgres/main.tf` — implement with `stackit_postgresflex_instance`, `stackit_postgresflex_user`, `stackit_postgresflex_database`; ACL validation mirroring foundation (`forbid_default_open_world`); `depends_on` between user and database.
- `infra/cloud/stackit/terraform/modules/postgres/variables.tf` — all contract inputs: `stackit_project_id`, `stackit_region`, `postgres_instance_name`, `postgres_db_name`, `postgres_username`, `postgres_user_roles`, `postgres_version`, `postgres_replicas`, `postgres_acl`, `postgres_flavor_cpu`, `postgres_flavor_ram`, `postgres_storage_class`, `postgres_storage_size_gb`, `postgres_backup_schedule`.
- `infra/cloud/stackit/terraform/modules/postgres/outputs.tf` — all contract outputs: `postgres_instance_id`, `postgres_host`, `postgres_port`, `postgres_username`, `postgres_password`, `postgres_database`.
- `infra/cloud/stackit/terraform/modules/postgres/versions.tf` — `stackitcloud/stackit` provider version pin matching foundation.

### Slice 4: Smoke Hardening + Docs
- `scripts/bin/infra/postgres_smoke.sh` — add `host`, `port`, `database` non-empty validation checks (in addition to existing DSN format check).
- `docs/platform/modules/postgres/README.md` — complete: Standalone STACKIT Terraform Module section, Credentials section, Smoke Checks section, Destroy section, Local Lane vs STACKIT Lane differences, Env-Var Reference.
- `python3 scripts/lib/docs/sync_platform_seed_docs.py` (or equivalent) — sync seed docs if needed.

## Change Strategy
- Migration/rollout sequence: Slice 1 (tests RED) → Slice 2 (exec class + secrets GREEN) → Slice 3 (Terraform module GREEN) → Slice 4 (smoke + docs GREEN)
- Backward compatibility policy: no breaking changes to env var names, make targets, or state file keys; `auth.existingSecret` change requires Secret to exist before pod start — ordering guaranteed by reconcile-before-upgrade.
- Rollback plan: revert the PR; K8s Secret `blueprint-postgres-auth` can be deleted manually via `kubectl delete secret -n data blueprint-postgres-auth` if needed.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/infra/modules/postgres/ -v` — ≥ 20 assertions covering Terraform module structure, Helm values contract, script invariants, lib functions.
- Contract checks: `pytest tests/infra/modules/postgres/test_contract.py -v` — runtime state key contract.
- Integration checks: `pytest tests/infra/test_tooling_contracts.py -k postgres` — execution class routing.
- E2E checks: N/A — infra-only module; no HTTP endpoint.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact — infra-only work item; no app code changes.
- Notes: existing make targets (`infra-postgres-{plan,apply,smoke,destroy}`) are unchanged; no new make targets added.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/postgres/README.md` — complete all stubs (Credentials, Smoke Checks, Destroy, Env-Var Reference, Local Lane vs STACKIT Lane Differences).
- Consumer docs updates: none.
- Mermaid diagrams updated: architecture.md already contains the flowchart diagram.
- Docs validation commands:
  - `make quality-docs-check-changed`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route changes.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no changes; existing `start_script_metric_trap` in all four bin scripts retained.
- Alerts/ownership: no new alerts; `blueprint-postgres-auth` Secret lifetime tied to `postgres_destroy.sh` cleanup.
- Runbook updates: `docs/platform/modules/postgres/README.md` Destroy section.

## Risks and Mitigations
- Risk 1: `auth.existingSecret` pod start order → mitigation: `postgres_reconcile_runtime_secret` called before `run_helm_upgrade_install` in `postgres_apply.sh`.
- Risk 2: `stackit_postgresflex_database.owner` user must exist first → mitigation: `depends_on = [stackit_postgresflex_user.postgres]` in Terraform module.
