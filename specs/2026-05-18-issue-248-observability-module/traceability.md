# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | n/a | foundation TF push URL outputs | `infra/cloud/stackit/terraform/foundation/outputs.tf`; bootstrap template copy | `test_contract.py` — foundation outputs.tf content check | ADR-issue-248-observability-module.md | `make infra-validate` |
| FR-002 | SDD-C-005 | n/a | `observability_metrics/logs/traces_push_url()` helpers | `scripts/lib/infra/observability.sh` | `test_contract.py` — function definition checks | `docs/platform/modules/observability/README.md` | `observability_runtime.env` keys |
| FR-003 | SDD-C-009 | n/a | `observability_api_key()` | `scripts/lib/infra/observability.sh` | `test_contract.py` — empty on local lane | README | state file (key present, value empty on local) |
| FR-004 | SDD-C-009 | n/a | `observability_reconcile/delete_runtime_secret()` | `scripts/lib/infra/observability.sh` | `test_contract.py` — function definition check | README — K8s Secret lifecycle | `blueprint-observability-auth` Secret existence |
| FR-005 | SDD-C-005, SDD-C-012 | n/a | `observability_apply.sh` foundation_contract case + state keys | `scripts/bin/infra/observability_apply.sh` | `test_contract.py` — script content checks | README | `artifacts/infra/observability_runtime.env` |
| FR-006 | SDD-C-009 | n/a | `observability_destroy.sh` Secret cleanup | `scripts/bin/infra/observability_destroy.sh` | `test_contract.py` — destroy script content check | README | `blueprint-observability-auth` Secret absent after destroy |
| FR-007 | SDD-C-007, SDD-C-013 | n/a | STACKIT otel-collector Helm values | `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` | `test_contract.py` — YAML content checks: exporters present, `extraVolumes`/`extraVolumeMounts` present, `/etc/otel/secrets` mount path, `${file:/etc/otel/secrets/` file provider references, `extraEnvFrom` absent, spanmetrics connector | README | ArgoCD sync status |
| FR-008 | SDD-C-007 | n/a | ArgoCD Application manifests | `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` | `test_contract.py` — `kind: Application` present | architecture.md | ArgoCD Application resource |
| FR-009 | SDD-C-010, SDD-C-012 | n/a | `observability_smoke.sh` STACKIT checks | `scripts/bin/infra/observability_smoke.sh` | `test_contract.py` — smoke script content check | README | `artifacts/infra/observability_smoke.env` status=passed |
| FR-010 | SDD-C-005 | n/a | module contract YAML additions | `blueprint/modules/observability/module.contract.yaml` | `test_contract.py` — contract YAML outputs list | README | `make infra-validate` |
| FR-011 | SDD-C-008 | n/a | test pyramid registration | `scripts/lib/quality/test_pyramid_contract.json` | pre-commit pyramid gate | n/a | `make quality-hooks-fast` |
| FR-012 | SDD-C-008 | n/a | `test_contract.py` ≥ 15 assertions | `tests/infra/modules/observability/test_contract.py` | pytest output ≥ 15 passed | n/a | `make test-unit-all` |
| FR-013 | SDD-C-011 | n/a | module README | `docs/platform/modules/observability/README.md` | `make docs-build && make docs-smoke` | README itself | `make docs-smoke` |
| NFR-SEC-001 | SDD-C-009 | n/a | `blueprint-observability-auth` Secret; empty `api_key` | `observability.sh`; `observability_apply.sh` | `test_contract.py` — password not in state file; api_key empty on local | README — security section | K8s Secret absent from state file |
| NFR-OBS-001 | SDD-C-010 | n/a | OTEL endpoint same DNS on both lanes | `observability.sh` `observability_init_env()`; both apply branches | `test_contract.py` — otel_endpoint format check | README — OTEL contract | `observability_runtime.env` otel_endpoint value |
| NFR-REL-001 | SDD-C-007 | n/a | ArgoCD selfHeal | `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` | `test_contract.py` — selfHeal: true in YAML | architecture.md | ArgoCD Application health |
| NFR-OPS-001 | SDD-C-010 | n/a | state file non-sensitive push URLs | `scripts/bin/infra/observability_apply.sh` | `test_contract.py` — state key names | README | `observability_runtime.env` |
| NFR-A11Y-001 | n/a | n/a | N/A — no UI or frontend changes | n/a | T-A01 marked N/A in tasks.md | n/a | n/a |
| AC-001 | SDD-C-012 | n/a | state file structure | `observability_apply.sh` | `test_contract.py` | README | `observability_runtime.env` |
| AC-002 | SDD-C-012 | n/a | otel_endpoint value | `observability.sh` | `test_contract.py` | README | `observability_runtime.env` |
| AC-003 | SDD-C-012 | n/a | smoke pass | `observability_smoke.sh` | smoke exit 0 | README | `observability_smoke.env` status=passed |
| AC-004 | SDD-C-009 | n/a | Secret lifecycle | `observability.sh` | `test_contract.py` | README | `blueprint-observability-auth` K8s Secret |
| AC-005 | SDD-C-007 | n/a | ArgoCD Application present | ArgoCD manifests | `test_contract.py` | architecture.md | manifest file content |
| AC-006 | SDD-C-007 | n/a | otel-collector exporters | `otel-collector.values.yaml` | `test_contract.py` | README | values file content |
| AC-007 | SDD-C-008 | n/a | test count ≥ 15 | `test_contract.py` | pytest output | n/a | `make test-unit-all` |
| AC-008 | SDD-C-009 | n/a | Secret removed on destroy | `observability_destroy.sh` | `test_contract.py` | README | K8s Secret absent |
| AC-009 | SDD-C-009 | n/a | api_key empty on local | `observability.sh` | `test_contract.py` | n/a | `observability_runtime.env` |
| AC-010 | SDD-C-005 | n/a | contract validation | module.contract.yaml | `make infra-validate` | n/a | `make infra-validate` |
| AC-011 | SDD-C-011 | n/a | README completeness | README | `make docs-build` | README itself | `make docs-smoke` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001 through FR-013, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-011

## Validation Summary
- Required bundles executed: `make test-unit-all`, `make infra-validate`, `make quality-hooks-run`, `make docs-build && make docs-smoke`, `make quality-hardening-review`, `make quality-spec-pr-ready`, `make blueprint-template-smoke`
- Result summary: All gates green. 1061 unit tests pass (43 new observability assertions including spanmetrics connector). `make infra-validate` exit 0. `make docs-build && make docs-smoke` exit 0. `make quality-hardening-review` exit 0. `make quality-spec-pr-ready` exit 0. `make blueprint-template-smoke` exit 0 (pre-existing `declare -A` failure fixed in PR #311). `make quality-hooks-run` passes all checks; `blueprint-template-smoke` failure pre-existing on main — fixed separately.
- Documentation validation:
  - `make docs-build` — exit 0 (2026-05-20)
  - `make docs-smoke` — exit 0 (2026-05-20)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Q-1 (TF attribute names): resolved 2026-05-19 — `metrics_push_url`, `logs_push_url`, `otlp_grpc_traces_url` confirmed in provider v0.88.0. Recorded in ADR and PR #308 comment.
