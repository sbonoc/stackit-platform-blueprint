# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-009 | | Local Helm values template — `allowInsecureImages` key | `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml` | AC-001 (static YAML; `make infra-validate`) | `docs/platform/modules/opensearch/README.md` §prerequisites | `helm install` pre-install hook passes |
| FR-002 | SDD-C-005, SDD-C-007 | | Local Helm values template — `sysctlImage.enabled` key | `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml` | AC-002 (static YAML; `make infra-validate`) | `docs/platform/modules/opensearch/README.md` §prerequisites | OpenSearch pods reach Running without init-container pull |
| FR-003 | SDD-C-005 | | Seed values file mirrors template | `infra/local/helm/opensearch/values.yaml` | `test_opensearch_seed_values_allow_insecure_images`, `test_opensearch_seed_values_sysctl_image_disabled` | — | `helm upgrade --install` uses seed file at apply time |
| FR-004 | SDD-C-005 | | Artifact rendered file mirrors template | `artifacts/infra/rendered/opensearch.values.yaml` | Manual YAML parity check | — | Rendered artifact used in CI dry-run validation |
| FR-005 | SDD-C-008, SDD-C-024 | | Test assertions for both new keys | `tests/infra/modules/opensearch/test_opensearch_module.py` — `OpenSearchLocalHelmChartTests` | `test_opensearch_seed_values_allow_insecure_images`, `test_opensearch_seed_values_sysctl_image_disabled` | — | `uv run python3 -m pytest tests/infra/modules/opensearch/ -v` |
| NFR-SEC-001 | SDD-C-009, SDD-C-013 | | `allowInsecureImages` scoped to local-lane only | `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`, `infra/local/helm/opensearch/values.yaml`, `artifacts/infra/rendered/opensearch.values.yaml` | No equivalent key in STACKIT Terraform module | ADR §Security | STACKIT lane apply is unaffected |
| NFR-OBS-001 | SDD-C-010 | | N/A | N/A | N/A | N/A | N/A |
| NFR-REL-001 | SDD-C-007 | | Backward-compatible additive change | All three YAML files — keys appended; no existing keys removed | Existing tests remain green | — | `helm upgrade` picks up new keys on re-apply |
| NFR-OPS-001 | SDD-C-010 | | N/A — no runbook changes required | N/A | N/A | N/A | N/A |
| NFR-A11Y-001 | — | N/A | N/A — infrastructure-only, no UI | N/A | N/A | N/A | N/A |
| AC-001 | SDD-C-012 | | `allowInsecureImages: true` in template | `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml` | `make infra-validate` + manual YAML inspection | — | CI infra-validate pass |
| AC-002 | SDD-C-012 | | `sysctlImage.enabled: false` in template | `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml` | `make infra-validate` + manual YAML inspection | — | CI infra-validate pass |
| AC-003 | SDD-C-012 | | Both keys in seed values | `infra/local/helm/opensearch/values.yaml` | `test_opensearch_seed_values_allow_insecure_images`, `test_opensearch_seed_values_sysctl_image_disabled` | — | pytest green |
| AC-004 | SDD-C-012 | | Both keys in artifact rendered file | `artifacts/infra/rendered/opensearch.values.yaml` | Manual YAML inspection | — | CI artifact parity |
| AC-005 | SDD-C-008, SDD-C-024 | | `test_opensearch_seed_values_allow_insecure_images` green | `tests/infra/modules/opensearch/test_opensearch_module.py` | `uv run python3 -m pytest tests/infra/modules/opensearch/ -v` | — | CI test run |
| AC-006 | SDD-C-008, SDD-C-024 | | `test_opensearch_seed_values_sysctl_image_disabled` green | `tests/infra/modules/opensearch/test_opensearch_module.py` | `uv run python3 -m pytest tests/infra/modules/opensearch/ -v` | — | CI test run |
| AC-007 | SDD-C-001, SDD-C-002 | | `make quality-hooks-fast` passes | All changed paths | `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` output | — | CI quality gate pass |
| AC-008 | SDD-C-011 | | `make infra-validate` passes | All changed paths | `make infra-validate` output | — | CI infra-validate pass |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008

## Validation Summary
- Required bundles executed: pending — to be filled at Verify phase.
- Result summary: pending.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Long-term — evaluate chart version upgrade to restore a working `sysctlImage` init container tag; deferred proposal in ADR.
