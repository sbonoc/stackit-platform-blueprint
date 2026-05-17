# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | N/A | D-1 HTTPS listener | `gateway/public-endpoints.yaml.tmpl` | `test_ac001_*` | README Stack Execution Model | smoke: HTTPS listener check |
| FR-002 | SDD-C-005 | N/A | D-2 Namespace Issuer | `public_endpoints.sh`, `public_endpoints_apply.sh` | `test_ac002_*` | README TLS section | smoke: Issuer manifest on disk |
| FR-003 | SDD-C-005 | N/A | D-2 Certificate | `public_endpoints.sh`, `public_endpoints_apply.sh` | `test_ac003_*` | README TLS section | smoke: Certificate manifest on disk |
| FR-004 | SDD-C-005 | N/A | D-3 external-dns annotation | `gateway/public-endpoints.yaml.tmpl` | `test_ac004_*` | README external-dns section | smoke: annotation check |
| FR-005 | SDD-C-002 | N/A | D-4 cert-manager featureGate | `cert-manager.values.yaml` + template mirror | `test_ac005_*` | ADR D-4 | core runtime bootstrap picks up featureGate |
| FR-006 | SDD-C-006 | N/A | contract API surface | `module.contract.yaml` | `test_ac016_*` | README Optional Inputs | init_repo_env.py defaults |
| FR-007 | SDD-C-007 | N/A | ArgoCD policy | `appproject-edge.yaml` (4 envs) | `test_ac010_*` | ADR D-5 | smoke: AppProject validation |
| FR-008 | SDD-C-012 | N/A | test contract | `test_contract.py` | AC-011, AC-012 | test_pyramid_contract.json | CI quality gate |
| NFR-SEC-001 | SDD-C-009 | N/A | ACME secret isolation | `public_endpoints_apply.sh` (no email in state) | structural: no email in state keys | README security note | runtime state review |
| NFR-OBS-001 | SDD-C-010 | N/A | smoke validation | `public_endpoints_smoke.sh` | `test_ac006_*`, `test_ac007_*`, `test_ac008_*` | README smoke section | smoke exit code |
| NFR-REL-001 | SDD-C-011 | N/A | destroy ordering | `public_endpoints_destroy.sh` | structural: delete cert before gateway | README destroy warning | destroy state file |
| NFR-OPS-001 | SDD-C-010 | N/A | runtime state keys | `public_endpoints_apply.sh` | `test_ac009_*` | README runtime state | `artifacts/infra/public_endpoints_runtime.env` |
| NFR-A11Y-001 | SDD-C-019 | N/A | N/A — no UI | N/A | N/A | spec.md NFR-A11Y-001 | N/A |
| AC-001 | SDD-C-005 | N/A | D-1 HTTPS listener | `gateway/public-endpoints.yaml.tmpl` | `test_ac001_*` | README Stack Execution Model | smoke: HTTPS listener check |
| AC-002 | SDD-C-005 | N/A | D-2 Namespace Issuer | `public_endpoints.sh` | `test_ac002_*` | README TLS section | smoke: Issuer manifest on disk |
| AC-003 | SDD-C-005 | N/A | D-2 Certificate | `public_endpoints.sh` | `test_ac003_*` | README TLS section | smoke: Certificate manifest on disk |
| AC-004 | SDD-C-005 | N/A | D-3 external-dns annotation | `gateway/public-endpoints.yaml.tmpl` | `test_ac004_*` | README external-dns section | smoke: annotation check |
| AC-005 | SDD-C-002 | N/A | D-4 cert-manager featureGate | `cert-manager.values.yaml` + template mirror | `test_ac005_*` | ADR D-4 | core runtime bootstrap featureGate |
| AC-006 | SDD-C-010 | N/A | D-1 smoke HTTPS check | `public_endpoints_smoke.sh` | `test_ac006_*` | README smoke section | smoke exit code |
| AC-007 | SDD-C-010 | N/A | D-3 smoke annotation check | `public_endpoints_smoke.sh` | `test_ac007_*` | README smoke section | smoke exit code |
| AC-008 | SDD-C-010 | N/A | D-2 smoke manifest check | `public_endpoints_smoke.sh` | `test_ac008_*` | README smoke section | smoke exit code |
| AC-009 | SDD-C-010 | N/A | D-2 runtime state keys | `public_endpoints_apply.sh` | `test_ac009_*` | README runtime state | `artifacts/infra/public_endpoints_runtime.env` |
| AC-010 | SDD-C-007 | N/A | D-5 AppProject whitelist | `appproject-edge.yaml` (4 envs) | `test_ac010_*` | ADR D-5 | smoke: AppProject validation |
| AC-011 | SDD-C-012 | N/A | FR-008 test registration | `test_pyramid_contract.json` | AC-011 self | — | CI quality gate |
| AC-012 | SDD-C-012 | N/A | FR-008 assertion count | `test_contract.py` | AC-012 self | — | CI quality gate |
| NFR-SEC-002 | SDD-C-009 | N/A | TLS min version | `gateway/public-endpoints.yaml.tmpl` | `test_ac013_*` | README security note | gateway listener options |
| NFR-SEC-003 | SDD-C-009 | N/A | TLS Secret RBAC doc | module README | structural: README section | README Secret access constraint | operator checklist |
| NFR-SEC-004 | SDD-C-009 | N/A | profile-aware ACME server | `public_endpoints.sh` `public_endpoints_init_env` | `test_ac014_*` | README TLS section | staging vs prod env var default |
| NFR-SEC-005 | SDD-C-009 | N/A | HTTP plain-text trade-off doc | module README | structural: README section | README security constraint | operator checklist |
| NFR-OBS-002 | SDD-C-010, SDD-C-011 | N/A | Certificate renewBefore | `public_endpoints.sh` Certificate renderer | `test_ac015_*` | README TLS section | rendered cert manifest |
| AC-013 | SDD-C-009 | N/A | TLS min version in gateway listener | `gateway/public-endpoints.yaml.tmpl` | `test_ac013_*` | README security note | gateway listener options |
| AC-014 | SDD-C-009 | N/A | profile-aware ACME server default | `public_endpoints.sh` | `test_ac014_*` | README TLS section | staging vs prod env var default |
| AC-015 | SDD-C-011 | N/A | Certificate renewBefore field | `public_endpoints.sh` Certificate renderer | `test_ac015_*` | README TLS section | rendered cert manifest |
| AC-016 | SDD-C-006 | N/A | FR-006 module.contract.yaml env vars | `module.contract.yaml` | `test_ac016_*` | README Optional Inputs | init_repo_env.py defaults |
| NFR-SEC-006 | SDD-C-009 | N/A | HSTS response header on HTTPS listener | gateway policy manifest + `public_endpoints_apply.sh` | `test_ac017_*` | README security section | gateway policy manifest on disk |
| NFR-SEC-007 | SDD-C-009 | N/A | NetworkPolicy for network namespace | `public_endpoints.sh` + `public_endpoints_apply.sh` | `test_ac018_*` | README network isolation section | NetworkPolicy manifests on disk |
| NFR-SEC-008 | SDD-C-009 | N/A | KMS module dependency for stackit-prod | `public_endpoints_apply.sh` (warning) + README | `test_ac019_*` | README KMS dependency section | apply log warning |
| AC-017 | SDD-C-009 | N/A | HSTS policy manifest | gateway policy manifest | `test_ac017_*` | README security section | gateway policy manifest on disk |
| AC-018 | SDD-C-009 | N/A | NetworkPolicy default-deny + allow 80/443 | NetworkPolicy manifests | `test_ac018_*` | README network isolation section | NetworkPolicy manifests on disk |
| AC-019 | SDD-C-009 | N/A | KMS warning on stackit-prod without KMS | `public_endpoints_apply.sh` | `test_ac019_*` | README KMS dependency section | apply log warning |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-012.

## Validation Summary
- Required bundles executed: pending implementation
- Result summary: pending implementation
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Wildcard cert via DNS01 ACME — parked, on-scope: infra; surfaces when STACKIT cert-manager DNS01 webhook becomes available.
- cert expiry monitoring — parked, on-scope: observability; surfaces when observability module is in scope.
