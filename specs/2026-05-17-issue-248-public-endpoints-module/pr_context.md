# PR Context

## Summary
- Work item: issue-248 — public-endpoints module HTTPS listener, cert-manager Issuer/Certificate, TLS policy, NetworkPolicy, AppProject whitelist
- Objective: Extend the public-endpoints optional module with HTTPS/TLS capability via cert-manager, enforce TLS 1.2+, add HSTS, network isolation, and profile-aware ACME server selection
- Scope boundaries: scripts/lib/infra/public_endpoints.sh, apply/destroy/smoke scripts, gateway template, appproject-edge overlays + bootstrap templates, module.contract.yaml, README

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-002, NFR-SEC-004, NFR-SEC-006, NFR-SEC-007, NFR-SEC-008, NFR-OBS-001, NFR-OBS-002, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020
- Contract surfaces changed: module.contract.yaml (4 new optional env vars), gateway template (HTTPS listener + TLS policy), appproject-edge.yaml for all 4 envs + bootstrap templates

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/public_endpoints.sh` — new rendering functions for Issuer, Certificate, TLS policy, NetworkPolicy manifests
  - `scripts/templates/infra/bootstrap/infra/gateway/public-endpoints.yaml.tmpl` — HTTPS listener + ClientTrafficPolicy
  - `scripts/bin/infra/public_endpoints_apply.sh` — new manifests applied, state file extended, KMS warning
  - `scripts/bin/infra/public_endpoints_destroy.sh` — Certificate→Issuer→gateway deletion ordering
- High-risk files:
  - `infra/gitops/argocd/overlays/*/appproject-edge.yaml` — adds cert-manager resource types to namespace whitelist
  - `scripts/bin/infra/public_endpoints_smoke.sh` — new HTTPS listener and Issuer/Certificate manifest validations

## Validation Evidence
- Required commands executed: `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/public-endpoints/test_contract.py -v`, `make test-unit-all`
- Result summary: 36/36 module contract tests pass; 1061 unit tests pass (no regressions)
- Artifact references: tests/infra/modules/public-endpoints/test_contract.py — 36 assertions covering AC-001 through AC-020

## Risk and Rollback
- Main risks: cert-manager featureGates flag requires cert-manager ≥v1.11 with ExperimentalGatewayAPISupport; KMS-less stackit-stage/prod environments will have unencrypted TLS secrets (warned at apply time); HSTS pinning on prod after first browser visit is irreversible for 1 year
- Rollback strategy: disable module (PUBLIC_ENDPOINTS_ENABLED=false) and run infra-public-endpoints-destroy; cert-manager featureGate can be reverted by removing the featureGates line from cert-manager.values.yaml and redeploying cert-manager

## Deferred Proposals
- None
