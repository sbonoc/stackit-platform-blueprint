# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: cert-manager featureGates line was absent from both `infra/local/helm/core/cert-manager.values.yaml` and the corresponding bootstrap template — added `ExperimentalGatewayAPISupport=true` to enable Gateway API HTTP01 challenge support (AC-005, FR-005)

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: new log_metric calls added for `public_endpoints_issuer_manifest_render_total`, `public_endpoints_certificate_manifest_render_total`, `public_endpoints_tls_policy_manifest_render_total`, `public_endpoints_network_policy_manifest_render_total`; KMS warning emitted via `log_warn` when stackit-stage/prod runs without KMS module
- Operational diagnostics updates: runtime state file extended with `cluster_issuer_name`, `cluster_issuer_type`, `tls_secret_name` keys; smoke script validates Issuer/Certificate manifests exist on disk and `cluster_issuer_name` is non-empty in runtime state

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: new rendering functions follow single-responsibility pattern consistent with existing public_endpoints.sh structure; path helpers return reproducible artifact paths; no cross-concern coupling introduced
- Test-automation and pyramid checks: 36 static-analysis assertions in test_contract.py covering all 20 ACs; test file registered in test_pyramid_contract.json under unit scope; make test-unit-all passes with 1061 tests
- Documentation/diagram/CI/skill consistency checks: bootstrap template mirror updated in sync with overlays (appproject-edge.yaml templates match actuals); README updated and synced to bootstrap template via sync_module_contract_summaries.py; quality-bootstrap-template-drift-check passes

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI or frontend changes
- [x] SC 2.1.1 (Keyboard): N/A — no UI or frontend changes
- [x] SC 2.4.7 (Focus Visible): N/A — no UI or frontend changes
- [x] SC 1.4.1 (Use of Color): N/A — no UI or frontend changes
- [x] SC 3.3.1 (Error Identification): N/A — no UI or frontend changes
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI or frontend changes

## Proposals Only (Not Implemented)
- none
