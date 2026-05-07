# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Existing `test_optional_module_execution_resolves_local_provider_noop_mode_for_opensearch` in `test_tooling_contracts.py` tested for stale `noop` driver — updated to assert `fallback_runtime/helm` routing consistent with Slice 5 implementation.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `opensearch_apply.sh` already emits `infra_opensearch_apply` metric via `start_script_metric_trap` (NFR-OBS-001 — no change required). `opensearch_smoke.sh` already emits `infra_opensearch_smoke` metric. `optional_module_values_render_total` metric emitted by `render_optional_module_values_file` on each render.
- Operational diagnostics updates: Runtime state file written to `artifacts/infra/opensearch_runtime.env` on every apply with `provision_driver`, `provision_path`, and all 8 contract outputs logged.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: All new functions follow single-responsibility pattern established by `rabbitmq.sh` reference. No new abstractions introduced beyond what the 8-output contract requires. `opensearch.sh` mirrors `rabbitmq.sh` structure.
- Test-automation and pyramid checks: 23 new unit tests across `test_opensearch_module.py` and `test_contract.py`; both files classified as `unit` in `test_pyramid_contract.json`. Integration test `test_opensearch_module_flow` updated to assert local HTTP lane values. Test pyramid ratio maintained (unit >60%).
- Documentation/diagram/CI/skill consistency checks: `docs/platform/modules/opensearch/README.md` updated with dual-lane usage, env-var reference, smoke, credentials, security, and state sections. Template synced via `sync_platform_seed_docs.py`.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- N/A SC 4.1.2 (Name, Role, Value): infrastructure-only work item; no UI components (NFR-A11Y-001)
- N/A SC 2.1.1 (Keyboard): infrastructure-only work item; no UI components
- N/A SC 2.4.7 (Focus Visible): infrastructure-only work item; no UI components
- N/A SC 1.4.1 (Use of Color): infrastructure-only work item; no UI components
- N/A SC 3.3.1 (Error Identification): infrastructure-only work item; no UI components
- N/A axe-core WCAG 2.1 AA scan evidence: infrastructure-only; no UI surfaces (declared NFR-A11Y-001, T-A01)

## Pre-PR Verifications
- Bitnami chart `bitnami/opensearch` original pin `2.28.3` was non-existent in the public Helm repo (verified via `helm search repo bitnami/opensearch -l`); revised pin to `1.6.3` (Bitnami chart 1.x line, OpenSearch app version `2.19.1`) — matches the STACKIT 2.x family. Chart 2.x targets OpenSearch 3.x and was rejected as incompatible with the 2.17 image line.
- Bitnami image revised pin `bitnamilegacy/opensearch:2.19.1-debian-12-r4` confirmed present on Docker Hub (Docker Hub API, 2026-05-06).
- Local helm topology revised from chart defaults (8 pods, ~7 GB RAM) to minimal 2-pod (master + coordinating) with `master.masterOnly: false` so master serves data role; total memory budget ≤1.5 GB. Verified via `helm template`.
- `dashboards.enabled: false` set explicitly on local lane (chart default is also false but made explicit for clarity); `OPENSEARCH_DASHBOARD_URL` is intentionally empty for local profile.
- `OPENSEARCH_USERNAME` is locked to `admin` for local lane: chart hardcodes `OPENSEARCH_USERNAME=admin` env var in the StatefulSet, so any operator override creates a duplicate env entry with undefined precedence. State file always reports `username=admin` for local.
- Local password reconciled via Kubernetes Secret `blueprint-opensearch-auth` (key `opensearch-password`, consumed via `security.existingSecret`) instead of being embedded in `values.yaml`; matches the rabbitmq pattern.

## Proposals Only (Not Implemented)
- Proposal 1 (dhe-marketplace consumer adoption): Rejected at PR closure — consumer-repo work; belongs in dhe-marketplace's own backlog, not blueprint.
- Proposal 2 (Q-1 Option B cross-cutting naming change): Rejected at PR closure — speculative; Q-1 resolved to Option A with no active driver to revisit.
