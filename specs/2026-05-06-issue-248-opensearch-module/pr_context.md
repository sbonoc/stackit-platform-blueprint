# PR Context

## Summary
- Work item: Issue #248 — OpenSearch module dual-lane implementation (local Helm + STACKIT Terraform)
- Objective: Implement first-class OpenSearch support so `infra-opensearch-apply` provisions a real service on both local (Bitnami Helm on Docker Desktop) and STACKIT (Terraform managed instance) lanes, writing an identical 8-key runtime state file.
- Scope boundaries: `scripts/lib/infra/opensearch.sh`, `scripts/bin/infra/opensearch_apply.sh`, `scripts/lib/infra/module_execution.sh`, `scripts/lib/infra/versions.sh`, `infra/cloud/stackit/terraform/modules/opensearch/`, `infra/local/helm/opensearch/`, `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/`, `scripts/bin/infra/bootstrap.sh`, `docs/platform/modules/opensearch/README.md`, `tests/infra/modules/opensearch/`.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-OBS-001, NFR-SEC-001, NFR-SEC-002, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010
- Contract surfaces changed: `opensearch_runtime.env` state schema (8 keys); local lane route changed from `noop` to `fallback_runtime/helm`.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/opensearch.sh` — local lane getters, seed_env_defaults, render_values_file
  - `scripts/bin/infra/opensearch_apply.sh` — helm) case added
  - `scripts/lib/infra/module_execution.sh` — opensearch local route: noop → helm
  - `infra/cloud/stackit/terraform/modules/opensearch/main.tf` — lifecycle create_before_destroy
  - `tests/infra/modules/opensearch/test_opensearch_module.py` — 17 assertions
  - `tests/infra/modules/opensearch/test_contract.py` — 8-key contract fixture
- High-risk files:
  - `scripts/lib/infra/versions.sh` — new pins; incorrect tag would fail local apply
  - `scripts/bin/infra/bootstrap.sh` — opensearch include_helm_values flag changed to true

## Validation Evidence
- Required commands executed: `pytest tests/infra/modules/opensearch/` (23 passed), `pytest tests/infra/test_tooling_contracts.py::...test_optional_module_execution_resolves_local_helm_mode_for_opensearch` (1 passed), `make quality-docs-check-changed` (passed), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (all green after fixes), `make infra-validate` (passed)
- Result summary: All 23 unit tests green; tooling contracts test updated and green; docs sync complete; test pyramid ratio 95% unit (>60% threshold).
- Artifact references:
  - `artifacts/infra/opensearch_runtime.env` — written by local apply
  - `artifacts/infra/rendered/opensearch.values.yaml` — rendered Helm values

## Risk and Rollback
- Main risks: (1) Bitnami `bitnamilegacy/opensearch` tag `2.17.1-debian-12-r0` needs confirmation at first live apply; (2) `stackit_opensearch_credential` admin-level assumption — stop condition applies if non-admin.
- Rollback strategy: local — `helm uninstall blueprint-opensearch -n search`; STACKIT — `OPENSEARCH_ENABLED=false make infra-opensearch-destroy`; code — revert `module_execution.sh` opensearch cases from `helm` to `noop` and revert `opensearch_apply.sh` helm) case.

## Deferred Proposals
- Proposal 1 (dhe-marketplace consumer adoption): Rejected at PR closure — consumer-repo work; belongs in dhe-marketplace's own backlog, not blueprint.
- Proposal 2 (Bitnami image tag verification): Resolved pre-PR — `bitnamilegacy/opensearch:2.17.1-debian-12-r0` confirmed present on Docker Hub (2026-05-06). No issue filed.
- Proposal 3 (Q-1 Option B cross-cutting naming change): Rejected at PR closure — speculative; Q-1 resolved to Option A with no active driver to revisit.
