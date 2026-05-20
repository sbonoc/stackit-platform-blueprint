# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | n/a | `WORKFLOWS_ENABLED` feature toggle; profile guard in `workflows_init_env()` | `scripts/lib/infra/workflows.sh`; all `stackit_workflows_*.sh` scripts | `test_contract.py` — `log_fatal` guard present in `workflows.sh` | `docs/platform/modules/workflows/README.md` | `WORKFLOWS_ENABLED=false` → make targets exit 0 |
| FR-002 | SDD-C-005 | n/a | `workflows_init_env()` env var validation + `.git` URL constraint | `scripts/lib/infra/workflows.sh` | `test_contract.py` — `test_workflows_init_env_function_defined`, `test_workflows_init_env_rejects_non_git_dags_url` (asserts `.git$` pattern and `must end with .git` message present in `workflows.sh`) | README | `make infra-stackit-workflows-plan` fails fast on missing env |
| FR-003 | SDD-C-005, SDD-C-012 | n/a | `workflows_payload_json()` JSON construction | `scripts/lib/infra/workflows.sh` | `test_contract.py` — `displayName`, `version`, `dagsRepository`, `identityProvider`, `observabilityId` present in function body | README | API `POST /instances` payload fields |
| FR-004 | SDD-C-005, SDD-C-012 | n/a | `stackit_workflows_plan.sh` plan state file | `scripts/bin/infra/stackit_workflows_plan.sh` | `test_contract.py` — `provision_driver=api_contract`, `provision_path`, `payload_file`, `display_name` keys in plan state | README | `artifacts/infra/workflows_plan.env` |
| FR-005 | SDD-C-005, SDD-C-012 | n/a | `stackit_workflows_apply.sh` apply + HTTP 409 idempotency | `scripts/bin/infra/stackit_workflows_apply.sh` | `test_contract.py` — `instance_id`, `instance_fqdn`, `web_url`, `health_status` keys in instance state | README | `artifacts/infra/workflows_instance.env` |
| FR-006 | SDD-C-009 | n/a | `stackit_workflows_keycloak_reconcile.sh` OIDC client upsert + roles | `scripts/bin/infra/stackit_workflows_keycloak_reconcile.sh` | `test_contract.py` — `realm`, `client_id`, `redirect_uris` keys in reconcile state | README — Keycloak OIDC contract | `artifacts/infra/workflows_keycloak_reconcile.env` |
| FR-007 | SDD-C-005, SDD-C-012 | n/a | `stackit_workflows_dag_deploy.sh` PATCH dags-repository | `scripts/bin/infra/stackit_workflows_dag_deploy.sh` | `test_contract.py` — `status=synced`, `dags_repo_url` keys in dag deploy state | README | `artifacts/infra/workflows_dag_deploy.env` |
| FR-008 | SDD-C-010 | n/a | `stackit_workflows_reconcile.sh` cardinality guard + keycloak converge | `scripts/bin/infra/stackit_workflows_reconcile.sh` | `test_contract.py` — `test_render_makefile_registers_workflows_apply_target` confirms module Makefile integration; reconcile script existence verified by implementation path | README | `make infra-stackit-workflows-reconcile` exit 0 |
| FR-009 | SDD-C-005 | n/a | `stackit_workflows_destroy.sh` DELETE + state file cleanup | `scripts/bin/infra/stackit_workflows_destroy.sh` | `test_contract.py` — no destroy state mock (destroy script writes `api_mode`, `api_http_status`, `instance_id`, `timestamp_utc`; no `status=destroyed`); security coverage via `SecurityContractTests` (token/secret absent) | README | destroy script exists at implementation path; state files removed after run |
| FR-010 | SDD-C-010 | n/a | `stackit_workflows_dag_parse_smoke.sh` DAG location guard | `scripts/bin/infra/stackit_workflows_dag_parse_smoke.sh` | `test_contract.py` — `apps/` guard present in parse smoke script | README | `artifacts/infra/workflows_dag_parse_smoke.env` |
| FR-011 | SDD-C-010 | n/a | `stackit_workflows_smoke.sh` health + live API check | `scripts/bin/infra/stackit_workflows_smoke.sh` | `test_contract.py` — `test_smoke_state_has_status_passed` (mock state contains `status=passed`); `SmokeStateContractTests` covers FR-011 contract | README | `artifacts/infra/workflows_smoke.env` status=passed |
| FR-012 | SDD-C-008 | n/a | test pyramid registration | `scripts/lib/quality/test_pyramid_contract.json` | pre-commit pyramid gate | n/a | `make quality-hooks-fast` |
| FR-013 | SDD-C-008 | n/a | `test_contract.py` ≥ 15 assertions | `tests/infra/modules/workflows/test_contract.py` | pytest output ≥ 15 passed | n/a | `make test-unit-all` |
| FR-014 | SDD-C-011 | n/a | module README | `docs/platform/modules/workflows/README.md` | `make docs-build && make docs-smoke` — exit 0 | README itself | `make docs-smoke` — exit 0 |
| NFR-SEC-001 | SDD-C-009 | n/a | `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` and `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` absent from all state files | `stackit_workflows_apply.sh`; `stackit_workflows_dag_deploy.sh` | `test_contract.py` — `test_dags_repo_token_absent_from_all_state_files`, `test_oidc_client_secret_absent_from_all_state_files` (mock state), `test_apply_script_does_not_persist_dags_repo_token_to_state`, `test_apply_script_does_not_persist_oidc_client_secret_to_state`, `test_dag_deploy_does_not_persist_dags_repo_token_as_state_key` (script-reading) | README — security note | state files contain no token/secret keys |
| NFR-OPS-001 | SDD-C-014 | n/a | STACKIT-only; `log_fatal` on non-STACKIT profile | `scripts/lib/infra/workflows.sh` `workflows_init_env()` | `test_contract.py` — `log_fatal` guard in `workflows.sh` | README — SDD-C-014 exception note | all make targets fail fast on local profile |
| NFR-A11Y-001 | n/a | n/a | N/A — no UI or frontend changes | n/a | n/a — no UI or frontend changes | n/a | n/a |
| AC-001 | SDD-C-012 | n/a | plan state file structure | `stackit_workflows_plan.sh` | `test_contract.py` | README | `artifacts/infra/workflows_plan.env` |
| AC-002 | SDD-C-012 | n/a | instance state key structure | `stackit_workflows_apply.sh` | `test_contract.py` | README | `artifacts/infra/workflows_instance.env` |
| AC-003 | SDD-C-009 | n/a | token absent from state files | all `stackit_workflows_*.sh` | `test_contract.py` | README | state file inspection |
| AC-004 | SDD-C-010 | n/a | smoke exit 0 | `stackit_workflows_smoke.sh` | smoke exit 0 | README | `artifacts/infra/workflows_smoke.env` status=passed |
| AC-005 | SDD-C-005 | n/a | destroy state + file cleanup | `stackit_workflows_destroy.sh` | `test_contract.py` | README | `workflows_instance.env` absent |
| AC-006 | SDD-C-009 | n/a | Keycloak reconcile state keys | `stackit_workflows_keycloak_reconcile.sh` | `test_contract.py` | README | `artifacts/infra/workflows_keycloak_reconcile.env` |
| AC-007 | SDD-C-008 | n/a | test count ≥ 15 and pyramid registration | `test_contract.py`; `test_pyramid_contract.json` | pytest output | n/a | `make test-unit-all` |
| AC-008 | SDD-C-012 | n/a | `make infra-validate` exit 0 | `blueprint/modules/workflows/module.contract.yaml` | `make infra-validate` | n/a | `make infra-validate` |
| AC-009 | SDD-C-011 | n/a | README completeness | `docs/platform/modules/workflows/README.md` | `make docs-build` | README itself | `make docs-smoke` |
| AC-010 | SDD-C-013 | n/a | `workflows_default_display_name()` ≤ 16 chars `a-z0-9-` | `scripts/lib/infra/workflows.sh` | `test_contract.py` — display name length constraint | n/a | `stackit_workflows_plan.sh` output |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001 through FR-014, NFR-SEC-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-010

## Validation Summary
- Required bundles executed: `make test-unit-all`, `make infra-validate`, `make quality-hooks-run`, `make docs-build && make docs-smoke`, `make quality-hardening-review`, `make quality-spec-pr-ready`
- Result summary: all green — `make test-unit-all` 1061 passed (41 subtests); `make infra-validate` exit 0; `make quality-hooks-fast` all 11 checks passed; `make quality-hardening-review` exit 0; `make quality-spec-pr-ready` no violations; `make docs-build && make docs-smoke` exit 0; `make quality-hooks-run` all hooks green (pre-existing `blueprint-template-smoke` bash 3.2 failure excluded — confirmed pre-existing on base, unrelated to this work item)
- Documentation validation:
  - `make docs-build` — exit 0 (2026-05-20)
  - `make docs-smoke` — exit 0 (2026-05-20)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Q-1 (TF provider upgrade): deferred — STACKIT provider v0.88.0 → v0.96.0 upgrade is out of scope; workflows uses REST API, no functional impact. Separate work item to be filed.
