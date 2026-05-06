# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 |  | Terraform module bounded context | `infra/cloud/stackit/terraform/modules/opensearch/main.tf`, `variables.tf`, `outputs.tf` | `test_terraform_module_has_opensearch_resources` | `docs/platform/modules/opensearch/README.md` §STACKIT lane | `infra-opensearch-apply` state file |
| FR-002 | SDD-C-005, SDD-C-013 |  | Local helm chart provisioning context | `infra/local/helm/opensearch/values.yaml` | `test_opensearch_local_helm_values_file_exists_and_parses` | `docs/platform/modules/opensearch/README.md` §Local lane | `helm status blueprint-opensearch` |
| FR-003 | SDD-C-005, SDD-C-006 |  | module_execution.sh routing | `scripts/lib/infra/module_execution.sh` opensearch cases | `test_opensearch_local_profile_routes_to_helm_driver` | Architecture.md §Bounded Contexts | `opensearch_runtime.env` `provision_driver=helm` |
| FR-004 | SDD-C-005, SDD-C-006 |  | opensearch.sh lib local lane | `scripts/lib/infra/opensearch.sh` local functions | `test_opensearch_local_host_returns_service_hostname`, port, scheme | `docs/platform/modules/opensearch/README.md` §env-var reference | `opensearch_runtime.env` |
| FR-005 | SDD-C-011 |  | Version pins | `scripts/lib/infra/versions.sh` | `test_opensearch_version_pins_declared` | `docs/platform/modules/opensearch/README.md` §prerequisites | `make infra-audit-version` |
| FR-006 | SDD-C-005 |  | opensearch_init_env defaults | `scripts/lib/infra/opensearch.sh` `opensearch_init_env()` | `test_opensearch_init_env_sets_helm_defaults` | — | `opensearch_runtime.env` |
| FR-007 | SDD-C-005 |  | render_values_file helper | `scripts/lib/infra/opensearch.sh` `opensearch_render_values_file()` | `test_opensearch_render_values_file` | — | `artifacts/infra/opensearch_values_rendered.yaml` |
| FR-008 | SDD-C-012 |  | Contract test | `tests/infra/modules/opensearch/test_contract.py` | `test_opensearch_runtime_state_has_all_contract_outputs` | `tests/infra/modules/opensearch/` | — |
| FR-009 | SDD-C-014 |  | Module README | `docs/platform/modules/opensearch/README.md` | `make quality-docs-check-changed` | `docs/platform/modules/opensearch/README.md` | — |
| FR-010 | SDD-C-005, SDD-C-012 |  | Smoke script | `scripts/bin/infra/opensearch_smoke.sh` | `test_opensearch_smoke_passes_with_valid_uri`, `test_opensearch_smoke_fails_when_uri_empty` | `docs/platform/modules/opensearch/README.md` §smoke | `infra-opensearch-smoke` exit code |
| NFR-OBS-001 | SDD-C-010 |  | Metric emission | `scripts/bin/infra/opensearch_apply.sh` `start_script_metric_trap` | Review: metric trap present and not removed | — | `infra_opensearch_apply` metric at exit |
| NFR-SEC-001 | SDD-C-009 |  | Password masking | `scripts/lib/infra/opensearch.sh`, `scripts/bin/infra/opensearch_apply.sh` | Review: password not in log lines | `docs/platform/modules/opensearch/README.md` §security | `opensearch_runtime.env` password field |
| NFR-SEC-002 | SDD-C-009 |  | Admin credential level | `infra/cloud/stackit/terraform/modules/opensearch/main.tf` `stackit_opensearch_credential` | Q-2 resolution confirmation | `docs/platform/modules/opensearch/README.md` §credentials | STACKIT provider docs reference |
| NFR-REL-001 | SDD-C-007, SDD-C-016 |  | lifecycle create_before_destroy | `infra/cloud/stackit/terraform/modules/opensearch/main.tf` | Terraform plan output showing lifecycle policy | `docs/platform/modules/opensearch/README.md` §version migration | `terraform plan` diff on version bump |
| NFR-OPS-001 | SDD-C-010, SDD-C-014 |  | State file schema | `scripts/bin/infra/opensearch_apply.sh` `write_state_file` | `test_opensearch_runtime_state_has_all_contract_outputs` | `docs/platform/modules/opensearch/README.md` §state | `artifacts/infra/opensearch_runtime.env` |
| AC-001 | SDD-C-005, SDD-C-012 |  | Local apply end-to-end | `opensearch_apply.sh` → `helm` driver → state file | `test_contract.py` | README §local lane | `opensearch_runtime.env` |
| AC-002 | SDD-C-005, SDD-C-012 |  | STACKIT apply end-to-end | `opensearch_apply.sh` → `foundation_contract` driver → state file | Maintainer-run apply evidence | README §STACKIT lane | `opensearch_runtime.env` |
| AC-003 | SDD-C-012 |  | Local smoke validation | `opensearch_smoke.sh` | `test_opensearch_smoke_passes_with_valid_uri` | README §smoke | smoke exit code |
| AC-004 | SDD-C-012 |  | STACKIT smoke validation | `opensearch_smoke.sh` | Maintainer-run smoke evidence | README §smoke | smoke exit code |
| AC-005 | SDD-C-007 |  | Local destroy cleanup | `opensearch_destroy.sh` → helm uninstall | Manual verify: no K8s resources remain | README §destroy | destroy state file |
| AC-006 | SDD-C-007 |  | STACKIT destroy cleanup | `opensearch_destroy.sh` → foundation reconcile | Maintainer-run destroy evidence | README §destroy | destroy state file |
| AC-007 | SDD-C-005 |  | Terraform module resources | `infra/cloud/stackit/terraform/modules/opensearch/main.tf` | `test_terraform_module_has_opensearch_resources` | `infra/cloud/stackit/terraform/modules/opensearch/` README | terraform validate |
| AC-008 | SDD-C-012 |  | Contract test passes | `tests/infra/modules/opensearch/test_contract.py` | `pytest tests/infra/modules/opensearch/` | — | CI test run |
| AC-009 | SDD-C-001, SDD-C-002 |  | Quality gates pass | All changed paths | `make quality-hooks-fast` green | — | CI pass |
| AC-010 | SDD-C-011 |  | Version pins | `scripts/lib/infra/versions.sh` | `test_opensearch_version_pins_declared` | README §prerequisites | `make infra-audit-version` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-OBS-001, NFR-SEC-001, NFR-SEC-002, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010

## Validation Summary
- Required bundles executed: pending (pre-implementation)
- Result summary: pending
- Documentation validation:
  - `make quality-docs-check-changed`
  - `make quality-docs-check-module-contract-summaries-sync`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consumer-side PR in dhe-marketplace to adopt `infra-opensearch-local-apply` and refactor `apps-openmetadata-local-apply` away from bundled OpenSearch — separate work item, after blueprint PR merge.
- Follow-up 2: If Q-1 resolves to Option B (dual-lane naming), a cross-cutting blueprint change is needed to apply dual-lane axis to all modules consistently — separate work item.
