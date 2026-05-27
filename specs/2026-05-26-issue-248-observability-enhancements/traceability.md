# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-008 | n/a | `observability_faro_endpoint()` helper | `scripts/lib/infra/observability.sh` | `test_contract.py` — `observability_faro_endpoint` in shell lib | README § Faro endpoint | `observability_runtime.env` faro_endpoint key |
| FR-002 | SDD-C-008 | n/a | `FARO_ENDPOINT` export in `observability_init_env` | `scripts/lib/infra/observability.sh` | `test_contract.py` — FARO_ENDPOINT in contract outputs | README § Consumer Usage | runtime state key |
| FR-003 | SDD-C-007, SDD-C-014 | n/a | Faro receiver + `${env:FARO_CORS_ALLOWED_ORIGINS}` + `extraEnvs` default `*`, local lane | `infra/local/helm/observability/otel-collector.values.yaml` | `test_contract.py` — port 12347, env substitution, extraEnv in local values | README § Faro Receiver | collector pod port 12347 |
| FR-004 | SDD-C-007, SDD-C-013 | n/a | Faro receiver + `${env:FARO_CORS_ALLOWED_ORIGINS}` + `extraEnvs` default `*`, STACKIT lane | `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` | `test_contract.py` — port 12347, env substitution in STACKIT values | README § STACKIT lane | ArgoCD Application |
| FR-005 | SDD-C-007, SDD-C-013 | n/a | Faro receiver + CORS env injection in ArgoCD inline values (dev/stage/prod) | `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` | `test_contract.py` — port 12347, FARO_CORS_ALLOWED_ORIGINS extraEnv in dev/stage/prod manifests | README § STACKIT lane | ArgoCD Application |
| FR-006 | SDD-C-005, SDD-C-015 | n/a | Contract outputs.produced + optional_env | `blueprint/modules/observability/module.contract.yaml` | `test_contract.py` — FARO_ENDPOINT in contract | README § Contract Summary | module.contract.yaml |
| FR-007 | SDD-C-012 | n/a | `faro_endpoint` state key write | `scripts/bin/infra/observability_apply.sh` | `test_contract.py` — faro_endpoint in mock state | README § Runtime State File | `artifacts/infra/observability_runtime.env` |
| FR-008 | SDD-C-012 | n/a | Faro smoke validation | `scripts/bin/infra/observability_smoke.sh` | `test_contract.py` — smoke validates faro_endpoint | README § Smoke Check | smoke exit code |
| FR-009 | SDD-C-009, SDD-C-010 | n/a | `memory_limiter` processor — both lanes | `otel-collector.values.yaml` ×2 + ArgoCD inline ×3 | `test_contract.py` — memory_limiter in local and STACKIT values | README § OTEL pipeline | collector memory metrics |
| FR-010 | SDD-C-009, SDD-C-010 | n/a | `filter/drop-healthcheck-spans` — both lanes | `otel-collector.values.yaml` ×2 + ArgoCD inline ×3 | `test_contract.py` — filter in local and STACKIT values | README § OTEL pipeline | reduced trace volume |
| FR-011 | SDD-C-010 | n/a | `spanmetrics` connector local lane | `infra/local/helm/observability/otel-collector.values.yaml` | `test_contract.py` — spanmetrics in local values | README § Local lane | RED metrics in debug output |
| FR-012 | SDD-C-011 | n/a | Seed dashboard JSON | `infra/observability/dashboards/golden-signals.json` | `test_contract.py` — seed dashboard file exists | README § Dashboard provisioning | Grafana UI dashboards |
| FR-013 | SDD-C-007 | n/a | Dashboard apply script | `scripts/bin/infra/observability_dashboards_apply.sh` | `test_contract.py` — dashboard apply script exists | README § Dashboard provisioning | ConfigMap in cluster |
| FR-014 | SDD-C-007 | n/a | Dashboard destroy script | `scripts/bin/infra/observability_dashboards_destroy.sh` | `test_contract.py` (implied by make target test) | README § Dashboard provisioning | ConfigMap removed |
| FR-015 | SDD-C-015 | n/a | Make targets declared + PHONY | `blueprint.generated.mk.tmpl` + `make/blueprint.generated.mk` | `test_contract.py` — dashboards-apply in Makefile template | README § Make targets | `make infra-observability-dashboards-apply` |
| FR-016 | SDD-C-011 | n/a | Bootstrap template mirror for dashboards | `scripts/templates/blueprint/bootstrap/infra/observability/dashboards/` | `quality-validate-bootstrap-template-drift` | README § Dashboard provisioning | consumer-seeded repos |
| FR-017 | SDD-C-005 | n/a | OBSERVABILITY_DASHBOARDS_NAME in contract | `blueprint/modules/observability/module.contract.yaml` | `test_contract.py` — OBSERVABILITY_DASHBOARDS_NAME in contract | README § Dashboard provisioning | env var |
| FR-018 | SDD-C-008 | n/a | 27 new test assertions (83 total; 21 from original slices + 6 for CORS env injection) | `tests/infra/modules/observability/test_contract.py` | pytest 83 passed, 0 failures | — | — |
| FR-019 | SDD-C-011 | n/a | README documentation update | `docs/platform/modules/observability/README.md` | `make quality-docs-lint` | README | — |
| NFR-SEC-001 | SDD-C-009 | n/a | Faro CORS via OTC `${env:FARO_CORS_ALLOWED_ORIGINS}` (pod env var, not file provider); `extraEnvs` default `*`; consumer override via ArgoCD `extraEnvs` | OTEL values config (×2) + ArgoCD inline (×3) | `test_contract.py` — env substitution in local/STACKIT values; FARO_CORS_ALLOWED_ORIGINS extraEnv in dev/stage/prod | README § Security + § Faro Receiver | no backend credential exposure; origin restriction is consumer opt-in |
| NFR-OPS-001 | SDD-C-010 | n/a | `memory_limiter` ordering (before batch) | OTEL values config | `test_contract.py` — memory_limiter before batch | README § OTEL pipeline | OOM protection |
| NFR-OPS-002 | SDD-C-010 | n/a | ConfigMap label `grafana_dashboard: "1"` | `observability_dashboards_apply.sh` | `test_contract.py` (script content check) | README § Dashboard provisioning | Grafana auto-discovery |
| NFR-OPS-003 | SDD-C-010 | n/a | Declarative `--dry-run | apply` idempotency | `observability_dashboards_apply.sh` | `test_contract.py` (script content check) | README § Dashboard provisioning | idempotent re-runs |
| NFR-A11Y-001 | n/a | n/a | N/A — no UI or frontend changes in this work item | n/a | n/a | n/a | n/a |
| AC-001 | FR-001 | n/a | `observability_faro_endpoint()` returns correct URL | `scripts/lib/infra/observability.sh` | `test_contract.py` — faro_endpoint function | README § Faro endpoint | — |
| AC-002 | FR-006 | n/a | `FARO_ENDPOINT` in contract outputs | `blueprint/modules/observability/module.contract.yaml` | `test_contract.py` — FARO_ENDPOINT in contract | README § Contract Summary | — |
| AC-003 | FR-003 | n/a | Port 12347 in local values faro entry | `infra/local/helm/observability/otel-collector.values.yaml` | `test_contract.py` | README § Local lane | collector pod port |
| AC-004 | FR-004 | n/a | Port 12347 in STACKIT values faro entry | `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` | `test_contract.py` | README § STACKIT lane | collector pod port |
| AC-005 | FR-003, FR-004, FR-005 | n/a | `faro` receiver in traces/logs pipelines all manifests | five config sources | `test_contract.py` | README § Faro endpoint | — |
| AC-006 | FR-009, NFR-OPS-001 | n/a | `memory_limiter` before `batch` all configs | five config sources | `test_contract.py` | README § OTEL pipeline | OOM protection |
| AC-007 | FR-010 | n/a | `filter/drop-healthcheck-spans` traces pipeline all configs | five config sources | `test_contract.py` | README § OTEL pipeline | reduced trace volume |
| AC-008 | FR-011 | n/a | `spanmetrics` in local values traces+metrics pipelines | `infra/local/helm/observability/otel-collector.values.yaml` | `test_contract.py` | README § Local lane | RED metrics |
| AC-009 | FR-012 | n/a | `golden-signals.json` exists and is valid JSON | `infra/observability/dashboards/golden-signals.json` | `test_contract.py` | README § Dashboard provisioning | Grafana UI |
| AC-010 | FR-013, NFR-OPS-002 | n/a | `dashboards-apply` creates labeled ConfigMap | `observability_dashboards_apply.sh` | manual test / `test_contract.py` script check | README § Dashboard provisioning | ConfigMap in cluster |
| AC-011 | FR-014 | n/a | `dashboards-destroy` removes ConfigMap | `observability_dashboards_destroy.sh` | manual test | README § Dashboard provisioning | ConfigMap removed |
| AC-012 | FR-018 | n/a | pytest passes ≥12 new assertions | `tests/infra/modules/observability/test_contract.py` | `pytest tests/infra/modules/observability/` | — | — |
| AC-013 | SDD-C-008 | n/a | `make quality-hooks-fast` passes no regressions | all changed files | pre-commit + quality gates | — | CI green |
