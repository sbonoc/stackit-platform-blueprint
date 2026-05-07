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
- Required commands executed: `pytest tests/infra/modules/opensearch/` (45 passed), `pytest tests/infra/test_tooling_contracts.py::...test_optional_module_execution_resolves_local_helm_mode_for_opensearch` (1 passed), `helm template` against chart 1.6.3 verified actual Service shape and minimal 2-pod topology, `make quality-docs-check-changed` (passed), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (all green after fixes), `make infra-validate` (passed)
- Result summary: All 45 unit tests green (up from 23 after deep review fixes); tooling contracts test updated and green; docs sync complete; chart pin corrected from non-existent 2.28.3 to verified 1.6.3; image pin corrected from 2.17.1 to chart-compatible 2.19.1-debian-12-r4.
- Artifact references:
  - `artifacts/infra/opensearch_runtime.env` — written by local apply
  - `artifacts/infra/rendered/opensearch.values.yaml` — rendered Helm values

## Risk and Rollback
- Main risks: (1) `stackit_opensearch_credential` admin-level assumption — stop condition applies if non-admin; (2) Bitnami chart 1.6.3 templates assume OpenSearch 2.x — bumping image tag past 2.x without first bumping to chart 2.x will fail at runtime.
- Rollback strategy: local — `OPENSEARCH_ENABLED=true make infra-opensearch-destroy` (runs `helm uninstall blueprint-opensearch -n search` with `--ignore-not-found`, then deletes K8s Secret); STACKIT — `OPENSEARCH_ENABLED=true make infra-opensearch-destroy` (foundation reconcile destroys the managed instance); code — revert `module_execution.sh` opensearch cases from `helm` to `noop` and revert `opensearch_apply.sh` helm) case.

## Deferred Proposals
- Proposal 1 (dhe-marketplace consumer adoption): Rejected at PR closure — consumer-repo work; belongs in dhe-marketplace's own backlog, not blueprint.
- Proposal 2 (Bitnami image tag verification): Resolved pre-PR — `bitnamilegacy/opensearch:2.17.1-debian-12-r0` confirmed present on Docker Hub (2026-05-06). No issue filed.
- Proposal 3 (Q-1 Option B cross-cutting naming change): Rejected at PR closure — speculative; Q-1 resolved to Option A with no active driver to revisit.
