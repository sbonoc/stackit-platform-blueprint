# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Bitnami chart 1.6.x breaking changes (issues #281 / #282) — `global.security.allowInsecureImages: true` and `sysctlImage.enabled: false` were absent from the local Helm values seed file and consumer template, causing pod startup failures on fresh bootstrap. Both keys are now set in `infra/local/helm/opensearch/values.yaml` and `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none — no observability instrumentation paths modified
- Operational diagnostics updates: none — Helm values changes are transparent to the existing smoke target (`make infra-opensearch-smoke`); smoke assertions unchanged and still sufficient to detect startup failures

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: no design changes; two static YAML keys added to values files; no new abstractions introduced
- Test-automation and pyramid checks: two new test methods added to `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py`, following the established `test_opensearch_seed_values_*` naming pattern; red-before-green slice discipline followed; test count 39 → 41 (red) → 47/47 (green) including contract tests
- Documentation/diagram/CI/skill consistency checks: both README files updated with Bitnami chart 1.6.x compatibility subsection; ADR filed at `docs/blueprint/architecture/decisions/ADR-issue-281-282-opensearch-bitnami-chart-fixes.md`; CI/CD pipelines unaffected (infra-only YAML change)

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI components (infrastructure-only work item; NFR-A11Y-001)
- [x] SC 2.1.1 (Keyboard): N/A — no UI components
- [x] SC 2.4.7 (Focus Visible): N/A — no UI components
- [x] SC 1.4.1 (Use of Color): N/A — no UI components
- [x] SC 3.3.1 (Error Identification): N/A — no UI components
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components; `artifacts/a11y/axe-report.json` not applicable

## Proposals Only (Not Implemented)
- Proposal 1 (not implemented): Long-term Bitnami chart 2.x upgrade — chart series 2.x targets OpenSearch 3.x and is incompatible with the 2.17/2.19 image line used by the blueprint; migration requires validating OpenSearch 3.x compatibility with STACKIT managed service plans and consumer applications — deferred as a separate work item
