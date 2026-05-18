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
| NFR-REL-001 | SDD-C-011 | N/A | destroy ordering | `public_endpoints_destroy.sh` | `test_ac020_*` | README destroy warning | destroy state file |
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
| NFR-SEC-008 | SDD-C-009 | N/A | KMS module dependency for stackit-stage and stackit-prod | `public_endpoints_apply.sh` (warning) + README | `test_ac019_*` | README KMS dependency section | apply log warning |
| AC-017 | SDD-C-009 | N/A | HSTS policy manifest | gateway policy manifest | `test_ac017_*` | README security section | gateway policy manifest on disk |
| AC-018 | SDD-C-009 | N/A | NetworkPolicy default-deny + allow 80/443 | NetworkPolicy manifests | `test_ac018_*` | README network isolation section | NetworkPolicy manifests on disk |
| AC-019 | SDD-C-009 | N/A | KMS warning on stackit-stage or stackit-prod without KMS | `public_endpoints_apply.sh` | `test_ac019_*` | README KMS dependency section | apply log warning |
| AC-020 | SDD-C-011 | N/A | destroy ordering: Certificate → Issuer → gateway | `public_endpoints_destroy.sh` | `test_ac020_*` | README destroy warning | static analysis of destroy script |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001 through FR-008; NFR-SEC-001 through NFR-SEC-008; NFR-OBS-001, NFR-OBS-002; NFR-REL-001; NFR-OPS-001; NFR-A11Y-001; AC-001 through AC-020.

## Validation Summary
- Required bundles executed: `make quality-sdd-check` PASS, `make quality-sdd-check-all` PASS (2026-05-18)
- Result summary: SDD governance checks pass. Implementation is complete — all 36 tests pass, all 20 ACs verified green.
- Test evidence: `uv run python3 -m pytest tests/infra/modules/public-endpoints/test_contract.py -v` — 36 passed (2026-05-18)
- Documentation validation:
  - `make docs-build` — pass (docs content complete)
  - `make docs-smoke` — pass

## Traceability Gap Report (2026-05-18 — traceability-keeper run)

### Blocking Gaps

None. All 19 gaps recorded in the 2026-05-17 pre-implementation run are now resolved.

### Resolved Gaps (2026-05-17 → 2026-05-18)

| Gap ID | Requirement(s) | Resolution |
|---|---|---|
| GAP-001 | FR-008, AC-011, AC-012 | `tests/infra/modules/public-endpoints/test_contract.py` created with 36 assertions; all pass. |
| GAP-002 | FR-008, AC-011 | `test_contract.py` registered in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope. |
| GAP-003 | FR-005, AC-005 | `ExperimentalGatewayAPISupport` added to `infra/local/helm/core/cert-manager.values.yaml` and bootstrap template mirror. |
| GAP-004 | FR-001, AC-001 | Gateway template updated with HTTPS listener (port 443, `tls.mode: Terminate`, `certificateRefs`). |
| GAP-005 | FR-004, AC-004 | `external-dns.alpha.kubernetes.io/hostname` annotation added to gateway template. |
| GAP-006 | FR-002, AC-002 | `public_endpoints_render_issuer_manifest()` and helpers added to `public_endpoints.sh`. |
| GAP-007 | FR-003, AC-003, NFR-OBS-002, AC-015 | `public_endpoints_render_certificate_manifest()` with `renewBefore` field added to `public_endpoints.sh`. |
| GAP-008 | NFR-SEC-004, AC-014 | Profile-aware `PUBLIC_ENDPOINTS_ACME_SERVER` default added to `public_endpoints_init_env`. |
| GAP-009 | NFR-SEC-006, AC-017 | `public_endpoints_render_gateway_tls_policy_manifest()` with HSTS header added; applied in `public_endpoints_apply.sh`. |
| GAP-010 | NFR-SEC-007, AC-018 | `public_endpoints_render_network_policy_manifests()` added; NetworkPolicy manifests applied in `public_endpoints_apply.sh`. |
| GAP-011 | NFR-OPS-001, AC-009 | `write_state_file` in `public_endpoints_apply.sh` extended with `cluster_issuer_name`, `cluster_issuer_type`, `tls_secret_name`. |
| GAP-012 | NFR-SEC-008, AC-019 | KMS warning emitted in `public_endpoints_apply.sh` for `stackit-stage`/`stackit-prod` without KMS module. |
| GAP-013 | NFR-REL-001, AC-020 | `public_endpoints_destroy.sh` updated to delete Certificate → Issuer before gateway baseline removal. |
| GAP-014 | NFR-OBS-001, AC-006, AC-007, AC-008 | `public_endpoints_smoke.sh` updated to validate HTTPS listener, external-dns annotation, Issuer manifest, Certificate manifest. |
| GAP-015 | FR-007, AC-010 | All 4 `appproject-edge.yaml` overlays updated with `cert-manager.io/Issuer` and `cert-manager.io/Certificate` in `namespaceResourceWhitelist`. |
| GAP-016 | FR-006, AC-016 | `module.contract.yaml` declares all 4 new optional TLS env vars. |
| GAP-017 | NFR-SEC-002, AC-013 | Minimum TLS version (TLS 1.2, excluding 1.0/1.1) configured in gateway template HTTPS listener. |
| GAP-018 | NFR-SEC-003, NFR-SEC-005, NFR-REL-001, NFR-SEC-006, NFR-SEC-007, NFR-SEC-008, NFR-OBS-002 | README updated with all required TLS sections. |
| GAP-019 | evidence_manifest.json | `evidence_manifest.json` `files[]` populated with all 15 implementation artifact paths; `traceability_keeper_status` set to `clean`. |

### Orphan Tests
- None.

### Orphan Requirements
- NFR-A11Y-001 is correctly mapped as N/A in traceability table (no gap).

### Confirmed Clean (implementation complete)
- graph.json: all 20 AC nodes, 8 FR nodes, 13 NFR nodes, and all implementation/doc nodes are present with correct edges. Graph is internally consistent with spec.md.
- ADR `docs/blueprint/architecture/decisions/ADR-issue-248-public-endpoints-module.md` exists (file present).
- `make quality-sdd-check` and `make quality-sdd-check-all` pass (spec readiness gates, language policy, control catalog sync all green).
- 36/36 test assertions pass in `tests/infra/modules/public-endpoints/test_contract.py`.

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Wildcard cert via DNS01 ACME — parked, on-scope: infra; surfaces when STACKIT cert-manager DNS01 webhook becomes available.
- cert expiry monitoring — parked, on-scope: observability; surfaces when observability module is in scope.
