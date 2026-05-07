# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | N/A | Execution class alignment | `scripts/lib/infra/module_execution.sh` local lane `postgres:plan\|apply` and `postgres:destroy` | `test_tooling_contracts.py::test_optional_module_execution_resolves_local_fallback_modes_for_postgres`, `::test_optional_module_execution_resolves_stackit_provider_backed_postgres_modes` | N/A — internal routing | metric label `class=fallback_runtime` emitted for local lane |
| FR-002 | SDD-C-005, SDD-C-009 | N/A | Secret-backed credential lifecycle | `scripts/lib/infra/postgres.sh::postgres_credential_secret_name()`, `postgres_reconcile_runtime_secret()`, `postgres_delete_runtime_secret()`, `postgres_render_values_file()` | `test_postgres_module.py::test_lib_defines_secret_lifecycle_functions`, `::test_lib_does_not_pass_credentials_to_values_render` | `docs/platform/modules/postgres/README.md § Credentials` | K8s Secret `blueprint-postgres-auth` |
| FR-003 | SDD-C-005, SDD-C-009 | N/A | Helm values existingSecret pattern | `infra/local/helm/postgres/values.yaml::auth.existingSecret` | `test_postgres_module.py::test_seed_values_use_existing_secret_not_plaintext_auth`, `::test_bootstrap_template_uses_credential_secret_name_placeholder` | `docs/platform/modules/postgres/README.md § Credentials` | Rendered `artifacts/infra/rendered/postgres.values.yaml` has no `password` |
| FR-004 | SDD-C-005, SDD-C-009 | N/A | Apply/destroy secret ordering | `scripts/bin/infra/postgres_apply.sh::postgres_reconcile_runtime_secret`, `scripts/bin/infra/postgres_destroy.sh::postgres_delete_runtime_secret` | `test_postgres_module.py::test_apply_reconciles_secret_before_helm`, `::test_destroy_deletes_runtime_secret_after_uninstall` | `docs/platform/modules/postgres/README.md § Destroy` | K8s Secret `blueprint-postgres-auth` exists post-apply; deleted post-destroy |
| FR-005 | SDD-C-005, SDD-C-013 | N/A | STACKIT standalone Terraform module | `infra/cloud/stackit/terraform/modules/postgres/main.tf` | `test_postgres_module.py::test_terraform_module_has_postgresflex_resources`, `::test_terraform_module_variables_bind_contract_inputs`, `::test_terraform_module_outputs_expose_contract_keys`, `::test_terraform_module_versions_tf_exists_with_provider_constraint` | `docs/platform/modules/postgres/README.md § Standalone STACKIT Terraform Module` | `terraform validate` |
| FR-006 | SDD-C-005, SDD-C-010, SDD-C-012 | N/A | Runtime state file write | `scripts/bin/infra/postgres_apply.sh::write_state_file` | `test_contract.py::test_postgres_runtime_state_has_all_contract_outputs` | `docs/platform/modules/postgres/README.md § Runtime State` | `artifacts/infra/postgres_runtime.env` |
| FR-007 | SDD-C-005, SDD-C-010 | N/A | Smoke validation hardening | `scripts/bin/infra/postgres_smoke.sh` | `test_postgres_module.py::test_smoke_passes_with_valid_state`, `::test_smoke_fails_when_dsn_invalid`, `::test_smoke_fails_when_host_empty`, `::test_smoke_fails_when_database_empty` | `docs/platform/modules/postgres/README.md § Smoke Checks` | `artifacts/infra/postgres_smoke.env` |
| FR-008 | SDD-C-005, SDD-C-009 | N/A | Bootstrap template credential pattern | `scripts/bin/infra/bootstrap.sh::postgres)` case; `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml` | `test_postgres_module.py::test_bootstrap_template_uses_credential_secret_name_placeholder`, `::test_bootstrap_template_has_no_plaintext_auth` | `docs/platform/modules/postgres/README.md § Credentials` | Bootstrap-rendered values.yaml has no plaintext password |
| NFR-SEC-001 | SDD-C-009 | N/A | No plaintext creds in values | `scripts/lib/infra/postgres.sh::postgres_render_values_file()` (no USER/PASSWORD binding); `infra/local/helm/postgres/values.yaml` (`auth.existingSecret` only) | `test_postgres_module.py::test_lib_does_not_pass_credentials_to_values_render`, `::test_seed_values_use_existing_secret_not_plaintext_auth`, `::test_bootstrap_template_has_no_plaintext_auth` | `docs/platform/modules/postgres/README.md § Credentials` | Rendered `artifacts/infra/rendered/postgres.values.yaml` has no password key |
| NFR-OBS-001 | SDD-C-010 | N/A | Metric trap per script | `scripts/bin/infra/postgres_{plan,apply,smoke,destroy}.sh::start_script_metric_trap` | N/A — framework guarantee verified by shared framework tests | N/A | metric events emitted on each script invocation |
| NFR-REL-001 | SDD-C-007 | N/A | Idempotent destroy | `scripts/bin/infra/postgres_destroy.sh::run_helm_uninstall --ignore-not-found`; `postgres_delete_runtime_secret` tolerates missing Secret | `test_postgres_module.py::test_destroy_has_helm_case`, `::test_destroy_deletes_runtime_secret_after_uninstall` | `docs/platform/modules/postgres/README.md § Destroy` | Re-run destroy exits 0 when resources absent |
| NFR-OPS-001 | SDD-C-010 | N/A | State schema completeness | `scripts/bin/infra/postgres_apply.sh::write_state_file` keys | `test_contract.py::test_postgres_runtime_state_has_all_contract_outputs`, `::test_postgres_runtime_state_dsn_has_postgresql_scheme` | `docs/platform/modules/postgres/README.md § Runtime State` | `artifacts/infra/postgres_runtime.env` |
| NFR-A11Y-001 | N/A | N/A | N/A — no UI component | N/A | N/A (declared N/A in `spec.md::NFR-A11Y-001`) | `spec.md::NFR-A11Y-001` | N/A |
| AC-001 | SDD-C-012 | N/A | Apply reconciles secret before helm | `scripts/bin/infra/postgres_apply.sh::helm)` | `test_postgres_module.py::test_apply_reconciles_secret_before_helm` | README § Credentials | K8s Secret `blueprint-postgres-auth` exists pre-chart-install |
| AC-002 | SDD-C-009, SDD-C-012 | N/A | Helm values use existingSecret | `infra/local/helm/postgres/values.yaml` | `test_postgres_module.py::test_seed_values_use_existing_secret_not_plaintext_auth` | README § Credentials | Rendered values has `existingSecret` key |
| AC-003 | SDD-C-009, SDD-C-012 | N/A | Render function omits plaintext creds | `postgres.sh::postgres_render_values_file()` | `test_postgres_module.py::test_lib_does_not_pass_credentials_to_values_render` | README § Credentials | N/A |
| AC-004 | SDD-C-012 | N/A | Destroy deletes runtime secret | `scripts/bin/infra/postgres_destroy.sh::helm)` | `test_postgres_module.py::test_destroy_deletes_runtime_secret_after_uninstall` | README § Destroy | K8s Secret `blueprint-postgres-auth` absent post-destroy |
| AC-005 | SDD-C-007, SDD-C-012 | N/A | Local lane fallback_runtime class | `module_execution.sh` | `test_tooling_contracts.py::test_optional_module_execution_resolves_local_fallback_modes_for_postgres` | N/A | metric label `class=fallback_runtime` |
| AC-006 | SDD-C-007, SDD-C-012 | N/A | STACKIT lane provider_backed class | `module_execution.sh` | `test_tooling_contracts.py::test_optional_module_execution_resolves_stackit_provider_backed_postgres_modes` | N/A | metric label `class=provider_backed` |
| AC-007 | SDD-C-013, SDD-C-012 | N/A | Terraform module resources | `infra/cloud/stackit/terraform/modules/postgres/main.tf` | `test_postgres_module.py::test_terraform_module_has_postgresflex_resources` | README § Standalone STACKIT Terraform Module | `terraform validate` |
| AC-008 | SDD-C-013, SDD-C-012 | N/A | Terraform module variables | `infra/cloud/stackit/terraform/modules/postgres/variables.tf` | `test_postgres_module.py::test_terraform_module_variables_bind_contract_inputs` | README § Standalone STACKIT Terraform Module | N/A |
| AC-009 | SDD-C-013, SDD-C-012 | N/A | Terraform module outputs | `infra/cloud/stackit/terraform/modules/postgres/outputs.tf` | `test_postgres_module.py::test_terraform_module_outputs_expose_contract_keys` | README § Standalone STACKIT Terraform Module | N/A |
| AC-010 | SDD-C-012 | N/A | Smoke passes with valid state | `scripts/bin/infra/postgres_smoke.sh` | `test_postgres_module.py::test_smoke_passes_with_valid_state` | README § Smoke Checks | `artifacts/infra/postgres_smoke.env` |
| AC-011 | SDD-C-012 | N/A | Smoke fails on invalid DSN | `scripts/bin/infra/postgres_smoke.sh` | `test_postgres_module.py::test_smoke_fails_when_dsn_invalid` | README § Smoke Checks | non-zero exit, log_fatal message |
| AC-012 | SDD-C-012 | N/A | Smoke fails on empty host | `scripts/bin/infra/postgres_smoke.sh` | `test_postgres_module.py::test_smoke_fails_when_host_empty` | README § Smoke Checks | non-zero exit |
| AC-013 | SDD-C-012 | N/A | Contract state has all outputs | `tests/infra/modules/postgres/test_contract.py` | `test_contract.py::test_postgres_runtime_state_has_all_contract_outputs`, `::test_postgres_runtime_state_dsn_has_postgresql_scheme` | N/A | N/A |
| AC-014 | SDD-C-009, SDD-C-012 | N/A | Bootstrap template credential pattern | `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml` | `test_postgres_module.py::test_bootstrap_template_uses_credential_secret_name_placeholder`, `::test_bootstrap_template_has_no_plaintext_auth` | README § Credentials | Bootstrap-rendered values has no plaintext password |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014

## Validation Summary
- Required bundles pending execution (to be completed in implementation phase):
  - `python3 -m pytest tests/infra/modules/postgres/ -v` → target: ≥ 20 PASSED
  - `python3 -m pytest tests/infra/test_tooling_contracts.py -k postgres` → target: 2/2 PASSED
  - `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` → target: all checks PASSED
- Result summary: pending implementation
- Documentation validation:
  - `make quality-docs-check-changed`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Q-1 (open): State file key naming alignment — `database`/`username`/`dsn` (current) vs strict prefix-stripping from module.contract.yaml. Agent recommends Option A (keep as-is). Pending user decision via PR comment.
