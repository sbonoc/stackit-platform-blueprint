# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `bootstrap_infra_static_templates()` in `scripts/bin/infra/bootstrap.sh` hardcoded four blueprint seed workload manifest names (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`). When a consumer renames their workloads, the function issued FATAL errors and created empty placeholder files. Fixed by replacing the four hardcoded calls with a `sed`-based `while` loop reading the template kustomization at `$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml` at runtime.
- Finding 2: `validate_app_runtime_conformance()` in `scripts/lib/blueprint/template_smoke_assertions.py` hardcoded the same four names. When a consumer's manifests differed, the smoke assertion checked for non-existent files (empty placeholders) and failed with "missing expected workload kinds Deployment/Service". Fixed by adding `_extract_kustomization_resources()` and deriving `app_manifest_paths` from the consumer repo's `infra/gitops/platform/base/apps/kustomization.yaml` at runtime.
- Finding 3: `test_pyramid_contract.json` was missing the new `tests/blueprint/test_template_smoke_assertions.py` entry — the test pyramid check would have flagged it as uncategorized. Added to `unit` scope.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: when the template kustomization is missing, `bootstrap.sh` now logs `FATAL: missing infra template kustomization: <path>` and halts (via `log_fatal`). When `kustomization.yaml` declares no resources and `APP_RUNTIME_GITOPS_ENABLED=true`, `validate_app_runtime_conformance()` raises `AssertionError: <scenario>: <kust_rel> declares no resources` — clearer than the previous silent empty-list path.
- Operational diagnostics updates: none — no new monitoring signals, dashboards, or runbook changes required.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: `_extract_kustomization_resources` is a pure function with no side effects; testable in isolation. Dependency direction preserved (template kustomization → bootstrap/smoke → no circular imports). No new abstraction layers introduced.
- Test-automation and pyramid checks: 8 new unit tests in `tests/blueprint/test_template_smoke_assertions.py` at the lowest valid layer (in-process, no subprocess or filesystem I/O beyond reading the blueprint repo's own template file). Regression guard in `test_quality_contracts.py` adds one test to the same unit class. Pre-existing pyramid ratios unchanged.
- Documentation/diagram/CI/skill consistency checks: no blueprint docs, consumer docs, or Mermaid diagrams require updates — this is internal tooling. No Make targets, CLI flags, or contract schema change. No skill runbook changes required.

## Proposals Only (Not Implemented)
- none
