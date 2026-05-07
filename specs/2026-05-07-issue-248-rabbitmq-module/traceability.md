# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | — | STACKIT Terraform module (instance + credential) | `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf`, `versions.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | `docs/platform/modules/rabbitmq/README.md` | — |
| FR-002 | SDD-C-005 | — | `module.contract.yaml` outputs.produced | `blueprint/modules/rabbitmq/module.contract.yaml` | `tests/infra/modules/rabbitmq/test_contract.py` | `docs/platform/modules/rabbitmq/README.md` | — |
| FR-003 | SDD-C-005 | — | `rabbitmq_vhost()` constant `/` | `scripts/lib/infra/rabbitmq.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | `docs/platform/modules/rabbitmq/README.md` | — |
| FR-004 | SDD-C-005 | — | `rabbitmq_management_url()` dual-lane | `scripts/lib/infra/rabbitmq.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | `docs/platform/modules/rabbitmq/README.md` | — |
| FR-005 | SDD-C-005, SDD-C-006 | — | State file write extended with vhost + management_url | `scripts/bin/infra/rabbitmq_apply.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | `artifacts/infra/rabbitmq_runtime.env` |
| FR-006 | SDD-C-005, SDD-C-006 | — | Smoke hardening | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| FR-007 | SDD-C-005 | — | Terraform variables.tf + outputs.tf | `infra/cloud/stackit/terraform/modules/rabbitmq/variables.tf`, `outputs.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| FR-008 | SDD-C-005 | — | Foundation outputs expose rabbitmq_management_url | `infra/cloud/stackit/terraform/foundation/outputs.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| NFR-SEC-001 | SDD-C-009 | — | No plaintext credentials in Helm values | `infra/local/helm/rabbitmq/values.yaml` (unchanged) | no automated test required — values.yaml unchanged, pre-existing `existingPasswordSecret` pattern already compliant | — | — |
| NFR-OBS-001 | SDD-C-010 | — | `start_script_metric_trap` in all four scripts | `scripts/bin/infra/rabbitmq_{plan,apply,smoke,destroy}.sh` | verified by grep | — | metric events |
| NFR-REL-001 | SDD-C-011 | — | `lifecycle { create_before_destroy = true }` | `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| NFR-OPS-001 | SDD-C-012 | — | State file has all 7 keys; smoke validates uri prefix, host, port, vhost, and management_url (5 checks) | `scripts/bin/infra/rabbitmq_apply.sh`, `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_contract.py`, `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | `artifacts/infra/rabbitmq_runtime.env` |
| NFR-A11Y-001 | — | — | N/A — infrastructure module | — | — | — | — |
| AC-001 | SDD-C-012 | — | Terraform resources declared | `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-002 | SDD-C-012 | — | variables.tf inputs | `infra/cloud/stackit/terraform/modules/rabbitmq/variables.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-003 | SDD-C-012 | — | outputs.tf keys | `infra/cloud/stackit/terraform/modules/rabbitmq/outputs.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-004 | SDD-C-012 | — | contract YAML outputs | `blueprint/modules/rabbitmq/module.contract.yaml` | `tests/infra/modules/rabbitmq/test_contract.py` | — | — |
| AC-005 | SDD-C-012 | — | rabbitmq_vhost() = "/" | `scripts/lib/infra/rabbitmq.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-006 | SDD-C-012 | — | rabbitmq_management_url() non-empty local | `scripts/lib/infra/rabbitmq.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-007 | SDD-C-012 | — | apply state file keys | `scripts/bin/infra/rabbitmq_apply.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-008 | SDD-C-012 | — | smoke pass with 7 keys | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-009 | SDD-C-012 | — | smoke fails bad URI | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-010 | SDD-C-012 | — | smoke fails empty host | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-011 | SDD-C-012 | — | smoke fails empty vhost | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-012 | SDD-C-012 | — | contract test 7 keys | `tests/infra/modules/rabbitmq/test_contract.py` | `tests/infra/modules/rabbitmq/test_contract.py` | — | — |
| AC-013 | SDD-C-012 | — | foundation outputs rabbitmq_management_url | `infra/cloud/stackit/terraform/foundation/outputs.tf` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |
| AC-014 | SDD-C-012 | — | Smoke fails when management_url empty | `scripts/bin/infra/rabbitmq_smoke.sh` | `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014

## Validation Summary
- Required bundles executed: `python3 -m pytest tests/infra/modules/rabbitmq/ -v` (22/22 PASSED), `make quality-docs-check-changed` (PASS), `make infra-validate` (PASS), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (all checks PASSED)
- Result summary: 22 tests across `test_rabbitmq_module.py` and `test_contract.py`; all 14 ACs covered. Pyramid ratios within thresholds.
- Documentation validation:
  - `make docs-build` — N/A (no MkDocs generation target; README synced via `sync_platform_seed_docs.py`)
  - `make docs-smoke` — N/A (no browser-facing surface)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Vhost customisation (non-default vhost per consumer) — deferred to separate work item.
- Follow-up 2: HA replica configuration (`stackit_rabbitmq_instance.replicas > 1`) — deferred to separate work item.
